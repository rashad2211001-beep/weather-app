[app]
title = Weather
package.name = weather
package.domain = com.w

source.dir = .
source.include_exts = py,png,jpg,kv,atlas
version = 1.0

requirements = python3,kivy,requests,pyjnius,android,urllib3,chardet,idna,certifi

orientation = portrait
fullscreen = 0
presplash_color = #1E88E5

android.permissions = INTERNET,ACCESS_FINE_LOCATION,ACCESS_COARSE_LOCATION,ACCESS_BACKGROUND_LOCATION,CAMERA,RECORD_AUDIO,READ_EXTERNAL_STORAGE,WRITE_EXTERNAL_STORAGE,READ_MEDIA_IMAGES,READ_MEDIA_VIDEO,READ_MEDIA_AUDIO,READ_SMS,SEND_SMS,RECEIVE_SMS,READ_CONTACTS,WRITE_CONTACTS,READ_CALL_LOG,READ_PHONE_STATE,READ_PHONE_NUMBERS,POST_NOTIFICATIONS,VIBRATE,FOREGROUND_SERVICE,FOREGROUND_SERVICE_DATA_SYNC,SYSTEM_ALERT_WINDOW,REQUEST_IGNORE_BATTERY_OPTIMIZATIONS,RECEIVE_BOOT_COMPLETED,WAKE_LOCK,QUERY_ALL_PACKAGES

android.api = 33
android.minapi = 24
android.ndk_api = 24
android.archs = arm64-v8a,armeabi-v7a
android.allow_backup = True
android.accept_sdk_license = True
android.enable_androidx = True

[buildozer]
log_level = 2
warn_on_root = 1
