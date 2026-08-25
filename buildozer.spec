[app]
title = BTC Alarm
package.name = btcalarm
package.domain = org.btcalarm
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,mp3
version = 0.1
requirements = python3,kivy,requests,urllib3,chardet,idna,certifi

orientation = portrait
fullscreen = 0

# Registra o serviço que roda no escuro
services = Monitoramento:service.py:foreground

#android.permissions = INTERNET, WAKE_LOCK, FOREGROUND_SERVICE, REQUEST_IGNORE_BATTERY_OPTIMIZATIONS, DISABLE_KEYGUARD, USE_FULL_SCREEN_INTENT, ACCESS_WIFI_STATE, CHANGE_WIFI_MULTICAST_STATE

android.permissions = INTERNET, WAKE_LOCK, FOREGROUND_SERVICE, REQUEST_IGNORE_BATTERY_OPTIMIZATIONS, DISABLE_KEYGUARD, USE_FULL_SCREEN_INTENT, ACCESS_WIFI_STATE, CHANGE_WIFI_MULTICAST_STATE, SYSTEM_ALERT_WINDOW, POST_NOTIFICATIONS

android.api = 33
android.minapi = 21
android.archs = arm64-v8a

[buildozer]
log_level = 2
warn_on_root = 1
