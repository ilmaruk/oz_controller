[app]

title = OZ Controller App
package.name = oz_controller
package.domain = net.ilmaruk
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,ini,ttf
source.exclude_dirs = venv, .github, .vscode, .git
version = 0.1
requirements = python3,kivy,paho-mqtt
orientation = sensor
fullscreen = 1
android.presplash_color = #00C000
android.permissions = INTERNET, WAKE_LOCK
android.accept_sdk_license = True
android.wakelock = True
android.archs = arm64-v8a
android.allow_backup = True

p4a.branch = master
# remove the pinned develop commit unless you know it is compatible
# p4a.commit = d2ee8c54d9d42375a95f18159e950a119671cf63

[buildozer]
log_level = 2
warn_on_root = 1