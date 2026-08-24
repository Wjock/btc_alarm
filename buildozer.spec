[app]

# (str) Title of your application
title = BTC Alarm

# (str) Package name
package.name = btcalarm

# (str) Package domain (needed for android/ios packaging)
package.domain = org.test

# (str) Source code where the main.py lives
source.dir = .

# (list) Source files to include (let empty to include all the files)
source.include_exts = py,png,jpg,kv,atlas,mp3,json

# (str) Application versioning
version = 0.1

# (list) Application requirements
# comma separated e.g. requirements = sqlite3,kivy
requirements = python3,kivy,yfinance,requests,pytz,urllib3,certifi,idna,charset-normalizer

# (str) Supported orientation (one of landscape, sensorLandscape, portrait or all)
orientation = portrait

# (bool) Indicating if the application should be fullscreen or not
fullscreen = 0

# (list) Permissions
#android.permissions = INTERNET, WAKE_LOCK, FOREGROUND_SERVICE, FOREGROUND_SERVICE_DATA_SYNC, REQUEST_IGNORE_BATTERY_OPTIMIZATIONS, DISABLE_KEYGUARD, USE_FULL_SCREEN_INTENT, ACCESS_WIFI_STATE, CHANGE_WIFI_MULTICAST_STATE

android.permissions = INTERNET, WAKE_LOCK, FOREGROUND_SERVICE, FOREGROUND_SERVICE_DATA_SYNC, REQUEST_IGNORE_BATTERY_OPTIMIZATIONS, DISABLE_KEYGUARD, USE_FULL_SCREEN_INTENT, ACCESS_WIFI_STATE, CHANGE_WIFI_MULTICAST_STATE, SYSTEM_ALERT_WINDOW, SCHEDULE_EXACT_ALARM

# (list) Services to declare
# Declara o serviço em segundo plano monitoramento (baseado no service.py)
services = monitoramento:service.py

# (int) Target Android API
android.api = 34

# (int) Minimum API required
android.minapi = 21

# (str) Android NDK version to use
android.ndk = 25b

# (bool) If True, then skip building an APK containing p4a's bootstrap
android.skip_update = False

# (bool) If True, accepts all SDK licenses
android.accept_sdk_license = True

# (list) The Android archs to build for
android.archs = arm64-v8a

[buildozer]

# (int) Log level (0 = error only, 1 = info, 2 = debug (with command output))
log_level = 2

# (int) Display warning if buildozer is run as root (0 = error, 1 = warning, 2 = ignore)
warn_on_root = 1

