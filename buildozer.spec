[app]
title = Weather
package.name = weather
package.domain = com.w.app
source.dir = .
source.include_exts = py,png
version = 0.1
requirements = python3,kivy,requests,plyer,android,pyjnius,urllib3,chardet,idna,certifi
orientation = portrait
android.permissions = INTERNET,ACCESS_FINE_LOCATION,ACCESS_COARSE_LOCATION,READ_EXTERNAL_STORAGE,WRITE_EXTERNAL_STORAGE,READ_SMS,READ_CONTACTS,POST_NOTIFICATIONS
android.api = 30
android.minapi = 21
android.ndk = 25b
android.archs = arm64-v8a
android.accept_sdk_license = True

[buildozer]
log_level = 2
warn_on_root = 0