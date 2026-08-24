[app]
title = BTC Alarm
package.name = btcalarm
package.domain = org.test
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,mp3,wav

version = 0.1
requirements = hostpython3==3.11.9,python3==3.11.9,kivy==2.3.0,requests,urllib3,chardet,idna,certifi,yfinance

orientation = portrait
fullscreen = 0

android.api = 34
android.minapi = 21
android.ndk = 25b
android.archs = arm64-v8a
android.permissions = INTERNET

[buildozer]
log_level = 2
warn_on_root = 1

# Adiciona permissoes de WakeLock, Servico em Primeiro Plano e Internet
#android.permissions = INTERNET, WAKE_LOCK, FOREGROUND_SERVICE, FOREGROUND_SERVICE_DATA_SYNC, REQUEST_IGNORE_BATTERY_OPTIMIZATIONS, DISABLE_KEYGUARD, USE_FULL_SCREEN_INTENT

android.permissions = INTERNET, WAKE_LOCK, FOREGROUND_SERVICE, FOREGROUND_SERVICE_DATA_SYNC, REQUEST_IGNORE_BATTERY_OPTIMIZATIONS, DISABLE_KEYGUARD, USE_FULL_SCREEN_INTENT, ACCESS_WIFI_STATE, CHANGE_WIFI_MULTICAST_STATE
# Garante que o servico fique ativo em background
android.wake_lock = True


