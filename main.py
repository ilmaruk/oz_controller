import configparser
import json
from pathlib import Path

import paho.mqtt.client as mqtt
from kivy.app import App
from kivy.core.image import Image as CoreImage
from kivy.core.window import Window
from kivy.graphics import Color, Line, Rectangle
from kivy.logger import Logger
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.spinner import Spinner, SpinnerOption
from kivy.uix.textinput import TextInput
from kivy.utils import platform


# Portrait phone-like preview when running on a desktop.
# On Android, Kivy uses the device's actual screen dimensions.
if platform != "android":
    Window.size = (390, 844)

MQTT_CONFIG = configparser.ConfigParser()
MQTT_CONFIG.read(Path(__file__).resolve().with_name("config.ini"))
MQTT_BROKER = MQTT_CONFIG.get("mqtt", "broker")
MQTT_PORT = MQTT_CONFIG.getint("mqtt", "port")
MQTT_CLOCK_TOPIC = MQTT_CONFIG.get("mqtt", "clock_topic")
MQTT_SCORE_TOPIC = MQTT_CONFIG.get("mqtt", "score_topic")
MQTT_CLIENT_ID = MQTT_CONFIG.get("mqtt", "client_id")
TEAM_IDS = {
    "Ajax": "A",
    "Ajax (inv)": "a",
    "Boca": "B",
    "Boca (inv)": "b",
    "Celtic": "C",
    "Celtic (inv)": "c",
    "Genoa": "G",
    "Genoa (inv)": "g",
    "Inter": "I",
    "Inter (inv)": "i",
    "Napoli": "N",
    "Napoli (inv)": "n",
    "Parma": "P",
    "Parma (inv)": "p",
    "River": "R",
    "River (inv)": "r",
}
TEAM_OPTIONS = tuple(TEAM_IDS)
INTENSITY_IDS = {f"Intensity {value}": value for value in range(16)}
INTENSITY_OPTIONS = tuple(INTENSITY_IDS)
TEAM_ASSET_DIR = Path(__file__).resolve().parent / "assets"
TEAM_ICONS = {
    code: CoreImage(
        str(
            TEAM_ASSET_DIR
            / ("inv" if code.islower() else "")
            / f"crest-{code}.png"
        )
    ).texture
    for code in set(TEAM_IDS.values())
}
for texture in TEAM_ICONS.values():
    texture.mag_filter = "nearest"
    texture.min_filter = "nearest"


class TeamSpinnerOption(SpinnerOption):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.size_hint_y = None
        self.height = dp(48)
        self.font_size = "18sp"
        self.halign = "left"
        self.padding = (dp(40), dp(8))
        with self.canvas.after:
            Color(1, 1, 1, 1)
            self.icon = Rectangle(
                texture=TEAM_ICONS[TEAM_IDS[self.text]],
                size=(dp(24), dp(24)),
            )
        self.bind(pos=self.update_icon_position, size=self.update_icon_position)
        self.update_icon_position()

    def update_icon_position(self, *_):
        self.icon.pos = (self.x + dp(8), self.y + (self.height - dp(24)) / 2)


class TeamSpinner(Spinner):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.halign = "left"
        self.padding = (dp(40), dp(8))
        with self.canvas.after:
            Color(1, 1, 1, 1)
            self.icon = Rectangle(size=(dp(24), dp(24)))
        self.bind(text=self.update_icon_texture)
        self.update_icon_texture(self, self.text)
        self.bind(pos=self.update_icon_position, size=self.update_icon_position)
        self.update_icon_position()

    def update_icon_texture(self, _spinner, value):
        self.icon.texture = TEAM_ICONS[TEAM_IDS[value]]

    def update_icon_position(self, *_):
        self.icon.pos = (self.x + dp(8), self.y + (self.height - dp(24)) / 2)


class PhoneLayoutApp(App):
    def build(self):
        root = BoxLayout(
            orientation="vertical",
            padding=dp(14),
            spacing=dp(10),
        )

        top_quadrant = BoxLayout(
            orientation="vertical",
            spacing=dp(8),
            padding=dp(8),
            size_hint_y=1,
        )
        self.style_quadrant(top_quadrant, (0.95, 0.97, 0.98, 1))
        id_text_row = BoxLayout(
            orientation="horizontal",
            size_hint_y=None,
            height=dp(54),
            spacing=dp(8),
        )
        self.home_id = TeamSpinner(
            text="Ajax",
            values=TEAM_OPTIONS,
            option_cls=TeamSpinnerOption,
            font_size="22sp",
            size_hint_x=1,
        )
        self.away_id = TeamSpinner(
            text="Boca",
            values=TEAM_OPTIONS,
            option_cls=TeamSpinnerOption,
            font_size="22sp",
            size_hint_x=1,
        )
        id_text_row.add_widget(self.home_id)
        id_text_row.add_widget(self.away_id)
        top_quadrant.add_widget(id_text_row)

        first_text_row = BoxLayout(
            orientation="horizontal",
            size_hint_y=None,
            height=dp(54),
            spacing=dp(8),
        )
        self.home_score = TextInput(
            text="0",
            hint_text="Home score",
            input_filter="int",
            multiline=False,
            font_size="22sp",
            halign="center",
            padding=[dp(10), dp(10)],
        )
        self.away_score = TextInput(
            text="0",
            hint_text="Away score",
            input_filter="int",
            multiline=False,
            font_size="22sp",
            halign="center",
            padding=[dp(10), dp(10)],
        )
        first_text_row.add_widget(self.home_score)
        first_text_row.add_widget(self.away_score)
        top_quadrant.add_widget(first_text_row)
        increment_row = self.make_button_row(
            (("+", self.on_button_1), ("+", self.on_button_2))
        )
        decrement_row = self.make_button_row(
            (("-", self.on_button_3), ("-", self.on_button_4))
        )
        self.score_buttons = list(reversed(increment_row.children))
        self.score_buttons.extend(reversed(decrement_row.children))
        top_quadrant.add_widget(increment_row)
        top_quadrant.add_widget(decrement_row)
        top_quadrant.add_widget(self.make_button_row((("RESET", self.on_button_5),)))

        bottom_half = BoxLayout(
            orientation="vertical",
            size_hint_y=1,
        )
        bottom_quadrant = BoxLayout(
            orientation="vertical",
            spacing=dp(8),
            padding=dp(8),
            size_hint_y=1,
        )
        self.style_quadrant(bottom_quadrant, (0.87, 0.91, 0.94, 1))
        self.timer_is_set = False
        self.timer_is_running = False
        self.timer_input = TextInput(
            text="600",
            input_filter="int",
            multiline=False,
            font_size="22sp",
            halign="center",
            size_hint_y=None,
            height=dp(54),
            padding=[dp(10), dp(10)],
        )
        self.timer_input.bind(text=self.on_timer_input_change)
        bottom_quadrant.add_widget(self.timer_input)
        set_row = self.make_button_row((("SET", self.on_set_timer),))
        self.set_button = set_row.children[0]
        bottom_quadrant.add_widget(set_row)
        start_stop_row = self.make_button_row(
            (("START", self.on_start_timer), ("STOP", self.on_stop_timer))
        )
        self.start_button = next(
            button for button in start_stop_row.children if button.text == "START"
        )
        self.stop_button = next(
            button for button in start_stop_row.children if button.text == "STOP"
        )
        bottom_quadrant.add_widget(start_stop_row)
        self.update_timer_controls()

        intensity_quadrant = BoxLayout(
            orientation="vertical",
            padding=dp(8),
            size_hint_y=None,
            height=dp(70),
        )
        self.style_quadrant(intensity_quadrant, (0.87, 0.91, 0.94, 1))
        self.intensity_spinner = Spinner(
            text="Intensity 0",
            values=INTENSITY_OPTIONS,
            font_size="22sp",
            size_hint_y=None,
            height=dp(54),
        )
        self.intensity_spinner.bind(text=self.on_intensity_change)
        intensity_quadrant.add_widget(self.intensity_spinner)

        bottom_half.add_widget(bottom_quadrant)
        bottom_half.add_widget(intensity_quadrant)
        root.add_widget(top_quadrant)
        root.add_widget(bottom_half)
        root.bind(size=self.update_root_orientation)

        return root

    @staticmethod
    def update_root_orientation(root, size):
        root.orientation = "horizontal" if size[0] > size[1] else "vertical"

    def on_start(self):
        self.mqtt_client = mqtt.Client(
            callback_api_version=mqtt.CallbackAPIVersion.VERSION2,
            client_id=MQTT_CLIENT_ID,
        )
        self.mqtt_client.on_connect = self.on_mqtt_connect
        self.mqtt_client.reconnect_delay_set(min_delay=1, max_delay=30)
        self.mqtt_client.connect_async(MQTT_BROKER, MQTT_PORT, keepalive=60)
        self.mqtt_client.loop_start()

    def on_stop(self):
        if hasattr(self, "mqtt_client"):
            self.mqtt_client.disconnect()
            self.mqtt_client.loop_stop()

    def on_mqtt_connect(self, _client, _userdata, _flags, reason_code, _properties):
        if reason_code.is_failure:
            Logger.warning("MQTT: connection failed: %s" % reason_code)
            return
        Logger.info("MQTT: connected to %s" % MQTT_BROKER)

    def publish_mqtt_command(self, command, duration=None, intensity=None):
        client = getattr(self, "mqtt_client", None)
        if client is None:
            return
        message = {"command": command}
        if duration is not None:
            message["duration"] = duration
        if intensity is not None:
            message["intensity"] = intensity
        payload = json.dumps(message)
        self.publish_mqtt_message(client, MQTT_CLOCK_TOPIC, payload)
        self.publish_mqtt_score()

    def on_intensity_change(self, _spinner, value):
        self.publish_mqtt_command("INTENSITY", intensity=INTENSITY_IDS[value])

    def publish_mqtt_score(self):
        client = getattr(self, "mqtt_client", None)
        if client is None:
            return
        payload = json.dumps(
            {
                "home_id": TEAM_IDS[self.home_id.text],
                "away_id": TEAM_IDS[self.away_id.text],
                "home_score": int(self.home_score.text),
                "away_score": int(self.away_score.text),
            }
        )
        self.publish_mqtt_message(client, MQTT_SCORE_TOPIC, payload)

    @staticmethod
    def publish_mqtt_message(client, topic, payload):
        result = client.publish(topic, payload)
        if result.rc != mqtt.MQTT_ERR_SUCCESS:
            Logger.warning("MQTT: publish failed with code %s" % result.rc)
        else:
            Logger.debug("MQTT: published to %s: %s" % (topic, payload))

    def style_quadrant(self, quadrant, background_color):
        with quadrant.canvas.before:
            Color(*background_color)
            background = Rectangle()
        with quadrant.canvas.after:
            Color(0.34, 0.40, 0.44, 1)
            border = Line(width=dp(1), rectangle=(0, 0, 0, 0))

        def update_geometry(widget, _value):
            background.pos = widget.pos
            background.size = widget.size
            border.rectangle = (*widget.pos, *widget.size)

        quadrant.bind(pos=update_geometry, size=update_geometry)
        update_geometry(quadrant, None)

    def make_button_row(self, buttons):
        row = BoxLayout(
            orientation="horizontal",
            size_hint_y=1,
            spacing=dp(10),
        )
        for label, callback in buttons:
            row.add_widget(self.make_button(label, callback))
        return row

    @staticmethod
    def make_button(label, callback):
        button = Button(text=label, font_size="40sp", size_hint_x=1)
        action_colors = {
            "RESET": (0.78, 0.14, 0.20, 1),
            "SET": (0.78, 0.14, 0.20, 1),
            "+": (0.13, 0.53, 0.22, 1),
            "START": (0.13, 0.53, 0.22, 1),
            "-": (1, 0.80, 0.10, 1),
            "STOP": (1, 0.80, 0.10, 1),
        }
        if label in action_colors:
            button.background_normal = ""
            button.background_down = ""
            button.background_color = action_colors[label]
            if label in ("-", "STOP"):
                button.color = (0.12, 0.12, 0.12, 1)

        def fit_label(widget, _value):
            estimated_text_width = max(len(label) * 0.68, 1)
            widget.font_size = min(
                widget.height * 0.55,
                widget.width * 0.9 / estimated_text_width,
            )

        button.bind(size=fit_label)
        if callback is not None:
            button.bind(on_release=callback)
        return button

    @staticmethod
    def adjust_value(text_input, delta):
        try:
            value = int(text_input.text)
        except ValueError:
            value = 0
        text_input.text = str(max(0, value + delta))

    def on_button_1(self, *_):
        self.adjust_value(self.home_score, 1)
        self.publish_mqtt_score()

    def on_button_2(self, *_):
        self.adjust_value(self.away_score, 1)
        self.publish_mqtt_score()

    def on_button_3(self, *_):
        self.adjust_value(self.home_score, -1)
        self.publish_mqtt_score()

    def on_button_4(self, *_):
        self.adjust_value(self.away_score, -1)
        self.publish_mqtt_score()

    def on_button_5(self, *_):
        self.show_confirmation(
            "Sei sicuro di volere resettare il punteggio?",
            self.reset_score,
        )

    def reset_score(self):
        self.home_score.text = "0"
        self.away_score.text = "0"
        self.publish_mqtt_score()

    def show_confirmation(self, message, on_confirm):
        content = BoxLayout(
            orientation="vertical",
            spacing=dp(12),
            padding=dp(12),
        )
        prompt = Label(
            text=message,
            halign="center",
            valign="middle",
        )
        prompt.bind(size=lambda widget, size: setattr(widget, "text_size", size))
        content.add_widget(prompt)

        actions = BoxLayout(
            orientation="horizontal",
            size_hint_y=None,
            height=dp(54),
            spacing=dp(10),
        )
        cancel_button = Button(text="ANNULLA")
        confirm_button = Button(text="CONFERMA")
        actions.add_widget(cancel_button)
        actions.add_widget(confirm_button)
        content.add_widget(actions)

        popup = Popup(
            title="Conferma",
            content=content,
            size_hint=(0.85, None),
            height=dp(220),
            auto_dismiss=False,
        )
        cancel_button.bind(on_release=popup.dismiss)

        def confirm_action(*_):
            on_confirm()
            popup.dismiss()

        confirm_button.bind(on_release=confirm_action)
        self.confirmation_popup = popup
        popup.open()

    def on_timer_input_change(self, *_):
        if not self.timer_is_running:
            self.timer_is_set = False
        self.update_timer_controls()

    def on_set_timer(self, *_):
        if not self.is_valid_timer_value():
            return
        self.show_confirmation(
            "Sei sicuro di volere resettare l'orologio?",
            self.confirm_set_timer,
        )

    def confirm_set_timer(self):
        if self.is_valid_timer_value():
            self.timer_is_set = True
            self.publish_mqtt_command("SET", int(self.timer_input.text))
        self.update_timer_controls()

    def on_start_timer(self, *_):
        if self.timer_is_set and not self.timer_is_running:
            self.timer_is_running = True
            self.publish_mqtt_command("START")
        self.update_timer_controls()

    def on_stop_timer(self, *_):
        if self.timer_is_running:
            self.timer_is_running = False
            self.publish_mqtt_command("STOP")
        self.update_timer_controls()

    def is_valid_timer_value(self):
        try:
            return int(self.timer_input.text) > 0
        except ValueError:
            return False

    def update_timer_controls(self):
        for button in self.score_buttons:
            button.disabled = not self.timer_is_running
        self.set_button.disabled = self.timer_is_running or not self.is_valid_timer_value()
        self.start_button.disabled = self.timer_is_running or not self.timer_is_set
        self.stop_button.disabled = not self.timer_is_running


if __name__ == "__main__":
    PhoneLayoutApp().run()
