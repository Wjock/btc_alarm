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
