[app]

title = Rotor Balance
package.name = rotorbalance
package.domain = org.gnaneswar

source.dir = .
source.include_exts = py,png,jpg,kv,atlas

version = 1.0
requirements = python3,kivy

orientation = portrait
fullscreen = 0

icon.filename = %(source.dir)s/icon.png

android.permissions =
android.api = 33
android.minapi = 21
android.ndk = 25b
android.archs = arm64-v8a, armeabi-v7a
android.accept_sdk_license = True
android.allow_backup = True

[buildozer]
log_level = 2
warn_on_root = 1
