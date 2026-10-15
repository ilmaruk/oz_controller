from kivy.app import App
from kivy.core.window import Window
from kivy.graphics import Color, Line, Rectangle
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput


# Portrait phone-like preview when running on a desktop.
# On Android, Kivy uses the device's actual screen dimensions.
Window.size = (390, 844)


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
        first_text_row = BoxLayout(
            orientation="horizontal",
            size_hint_y=None,
            height=dp(54),
            spacing=dp(8),
        )
        self.text_area_1 = TextInput(
            text="0",
            hint_text="First text area",
            input_filter="int",
            multiline=False,
            font_size="22sp",
            halign="center",
            padding=[dp(10), dp(10)],
        )
        self.text_area_2 = TextInput(
            text="0",
            hint_text="Second text area",
            input_filter="int",
            multiline=False,
            font_size="22sp",
            halign="center",
            padding=[dp(10), dp(10)],
        )
        first_text_row.add_widget(self.text_area_1)
        first_text_row.add_widget(self.text_area_2)
        top_quadrant.add_widget(first_text_row)
        top_quadrant.add_widget(
            self.make_button_row((("+", self.on_button_1), ("+", self.on_button_2)))
        )
        top_quadrant.add_widget(
            self.make_button_row((("-", self.on_button_3), ("-", self.on_button_4)))
        )
        top_quadrant.add_widget(self.make_button_row((("RESET", self.on_button_5),)))

        bottom_quadrant = BoxLayout(
            orientation="vertical",
            spacing=dp(8),
            padding=dp(8),
            size_hint_y=1,
        )
        self.style_quadrant(bottom_quadrant, (0.87, 0.91, 0.94, 1))
        self.timer_input = TextInput(
            text="600",
            multiline=False,
            font_size="22sp",
            halign="center",
            size_hint_y=None,
            height=dp(54),
            padding=[dp(10), dp(10)],
        )
        bottom_quadrant.add_widget(self.timer_input)
        bottom_quadrant.add_widget(self.make_button_row((("SET", None),)))
        bottom_quadrant.add_widget(
            self.make_button_row((("START", None), ("STOP", None)))
        )

        root.add_widget(top_quadrant)
        root.add_widget(bottom_quadrant)

        return root

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
        self.adjust_value(self.text_area_1, 1)

    def on_button_2(self, *_):
        self.adjust_value(self.text_area_2, 1)

    def on_button_3(self, *_):
        self.adjust_value(self.text_area_1, -1)

    def on_button_4(self, *_):
        self.adjust_value(self.text_area_2, -1)

    def on_button_5(self, *_):
        self.text_area_1.text = "0"
        self.text_area_2.text = "0"


if __name__ == "__main__":
    PhoneLayoutApp().run()
