import os
import time
import json
from jnius import autoclass

# Classes Nativas do Android
PythonService = autoclass('org.kivy.android.PythonService')
service = PythonService.mService

Context = autoclass('android.content.Context')
PowerManager = autoclass('android.os.PowerManager')
WifiManager = autoclass('android.net.wifi.WifiManager')
MediaPlayer = autoclass('android.media.MediaPlayer')
AudioManager = autoclass('android.media.AudioManager')
WindowManager = autoclass('android.view.WindowManager$LayoutParams')
NotificationBuilder = autoclass('android.app.Notification$Builder')
NotificationManager = autoclass('android.app.NotificationManager')
NotificationChannel = autoclass('android.app.NotificationChannel')

# 1. Adquire Trava de CPU e Wi-Fi
power_manager = service.getSystemService(Context.POWER_SERVICE)
wake_lock = power_manager.newWakeLock(1, "BtcAlarm::ServiceWakeLock")
wake_lock.acquire()

wifi_service = service.getSystemService(Context.WIFI_SERVICE)
wifi_lock = wifi_service.createWifiLock(3, "BtcAlarm::ServiceWifiLock")
wifi_lock.acquire()

# 2. Configura Notificação Fixa na Barra (Exigência de Foreground Service no Android)
CHANNEL_ID = "btc_alarm_channel"
notification_manager = service.getSystemService(Context.NOTIFICATION_SERVICE)

if hasattr(NotificationChannel, 'class'):
    channel = NotificationChannel(CHANNEL_ID, "BTC Alarm Monitor", NotificationManager.IMPORTANCE_LOW)
    notification_manager.createNotificationChannel(channel)

def criar_notificacao(texto):
    if hasattr(NotificationBuilder, 'class'):
        builder = NotificationBuilder(service, CHANNEL_ID)
    else:
        builder = NotificationBuilder(service)
    
    builder.setContentTitle("BTC Alarm Ativo")
    builder.setContentText(texto)
    builder.setSmallIcon(service.getApplicationInfo().icon)
    return builder.build()

# Inicia o serviço exibindo a notificação de monitoramento
service.startForeground(1001, criar_notificacao("Iniciando monitoramento..."))

android_player = None

def acender_e_desbloquear_tela():
    """Força o acendimento da tela e ignora o bloqueio quando o alvo for atingido"""
    try:
        PythonActivity = autoclass('org.kivy.android.PythonActivity')
        activity = PythonActivity.mActivity
        flags = (
            WindowManager.FLAG_SHOW_WHEN_LOCKED |
            WindowManager.FLAG_TURN_SCREEN_ON |
            WindowManager.FLAG_DISMISS_KEYGUARD |
            WindowManager.FLAG_KEEP_SCREEN_ON
        )
        def apply_flags():
            activity.getWindow().addFlags(flags)

        from android.runnable import run_on_ui_thread
        run_on_ui_thread(apply_flags)()
    except Exception as e:
        print(f"Erro ao acender tela pelo servico: {e}")

def tocar_sirene():
    global android_player
    acender_e_desbloquear_tela()
    try:
        caminho_abs = os.path.abspath("sirene.mp3")
        if android_player is not None:
            android_player.release()

        android_player = MediaPlayer()
        android_player.setDataSource(caminho_abs)
        android_player.setAudioStreamType(AudioManager.STREAM_ALARM)
        android_player.setLooping(True)
        android_player.prepare()
        android_player.start()
    except Exception as e:
        print(f"Erro ao tocar sirene no servico: {e}")

def buscar_preco():
    try:
        import yfinance as yf
        ticker = yf.Ticker("BTC-USD")
        return float(ticker.fast_info['last_price'])
    except Exception:
        try:
            import requests
            res = requests.get("https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT", timeout=4).json()
            return float(res["price"])
        except Exception:
            return None

# 3. Loop Principal do Serviço (Roda a cada 5 segundos no escuro)
caminho_config = os.path.join(service.getFilesDir().getAbsolutePath(), "app", "alarm_config.json")

alarme_disparado = False

while True:
    try:
        if os.path.exists(caminho_config):
            with open(caminho_config, "r") as f:
                config = json.load(f)
            
            preco_alvo = config.get("preco_alvo")
            modo = config.get("modo")
            ativo = config.get("ativo", False)

            if ativo and preco_alvo is not None and not alarme_disparado:
                preco_atual = buscar_preco()
                
                if preco_atual is not None:
                    # Atualiza texto da notificação na barra
                    notif = criar_notificacao(f"BTC: U$ {preco_atual:,.2f} | Alvo: U$ {preco_alvo:,.2f}")
                    notification_manager.notify(1001, notif)

                    disparar = False
                    if modo == "ACIMA" and preco_atual >= preco_alvo:
                        disparar = True
                    elif modo == "ABAIXO" and preco_atual <= preco_alvo:
                        disparar = True

                    if disparar:
                        alarme_disparado = True
                        tocar_sirene()
                        
                        # Notificação de emergência ao disparar
                        notif_alerta = criar_notificacao(f"🚨 ALVO ATINGIDO: U$ {preco_atual:,.2f}! 🚨")
                        notification_manager.notify(1001, notif_alerta)

            elif not ativo:
                alarme_disparado = False
                if android_player is not None and android_player.isPlaying():
                    android_player.stop()
                    android_player.release()
                    android_player = None

    except Exception as e:
        print(f"Erro no loop do servico: {e}")

    time.sleep(5)  # Intervalo exato de 5 segundos