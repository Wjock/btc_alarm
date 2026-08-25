
import os
import json
import threading
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.widget import Widget
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.graphics import Color, Rectangle
from kivy.clock import Clock, mainthread
from kivy.utils import get_color_from_hex
from kivy.utils import platform

class BtcAlarmApp(App):
    def build(self):
        self.title = "BTC Alarm"
        self.preco_alvo = None
        self.modo_alarme = None
        self.alarme_ativo = False
        self.alarme_tocando = False
        self.preco_atual_global = 0.0
        
        self.android_player = None

        layout = BoxLayout(
            orientation='vertical',
            padding=[30, 100, 30, 20],
            spacing=30
        )
        
        with layout.canvas.before:
            Color(*get_color_from_hex('#12121A'))
            self.rect = Rectangle(size=layout.size, pos=layout.pos)
            layout.bind(size=self._update_rect, pos=self._update_rect)

        self.txt_titulo = Label(
            text="Cotação Atual do Bitcoin (USD)", 
            font_size='15sp', 
            size_hint=(1, None),
            height=30,
            color=get_color_from_hex('#B0B0C0')
        )
        
        self.txt_preco = Label(
            text="Buscando Mercado...", 
            font_size='28sp', 
            bold=True, 
            size_hint=(1, None),
            height=45,
            color=get_color_from_hex('#00E676')
        )
        
        self.input_alvo = TextInput(
            hint_text="Definir Valor Alvo (U$)", 
            multiline=False, 
            input_filter='float',
            input_type='number',
            size_hint=(0.9, None),
            pos_hint={'center_x': 0.5},
            height=90,
            font_size='22sp',
            halign='center',
            background_color=get_color_from_hex('#2A2A38'),
            foreground_color=get_color_from_hex('#FFFFFF'),
            hint_text_color=get_color_from_hex('#808090'),
            cursor_color=get_color_from_hex('#00E676')
        )
        
        self.btn_acao = Button(
            text="Ativar Alarme", 
            background_normal='',
            background_color=get_color_from_hex('#00A843'), 
            size_hint=(0.8, None),
            pos_hint={'center_x': 0.5},
            height=60, 
            bold=True,
            font_size='18sp'
        )
        self.btn_acao.bind(on_press=self.alternar_alarme)

        self.txt_status = Label(
            text="Nenhum alarme programado", 
            font_size='14sp', 
            size_hint=(1, None),
            height=35,
            color=get_color_from_hex('#808080')
        )

        layout.add_widget(self.txt_titulo)
        layout.add_widget(self.txt_preco)
        layout.add_widget(self.input_alvo)
        layout.add_widget(self.btn_acao)
        layout.add_widget(self.txt_status)
        layout.add_widget(Widget())

        self.disparar_busca_segundo_plano()
        Clock.schedule_interval(self.disparar_busca_segundo_plano, 5)
        return layout

    def on_pause(self):
        return True

    def on_resume(self):
        pass

    def _update_rect(self, instance, value):
        self.rect.pos = instance.pos
        self.rect.size = instance.size

    def agendar_proximo_alarme_cascata(self, segundos=5):
        """Usa o AlarmManager nativo para furar a suspensão do Galaxy A31"""
        if platform == 'android':
            try:
                from jnius import autoclass
                PythonActivity = autoclass('org.kivy.android.PythonActivity')
                Context = autoclass('android.content.Context')
                Intent = autoclass('android.content.Intent')
                PendingIntent = autoclass('android.app.PendingIntent')
                System = autoclass('java.lang.System')

                activity = PythonActivity.mActivity
                alarm_manager = activity.getSystemService(Context.ALARM_SERVICE)

                intent = Intent(activity, PythonActivity.class)
                intent.setFlags(Intent.FLAG_ACTIVITY_NEW_TASK | Intent.FLAG_ACTIVITY_SINGLE_TOP)
                
                # FLAG_UPDATE_CURRENT (134217728) ou FLAG_IMMUTABLE (67108864)
                flags = 134217728 | 67108864
                pending_intent = PendingIntent.getActivity(activity, 0, intent, flags)

                tempo_disparo = System.currentTimeMillis() + (segundos * 1000)

                # RTC_WAKEUP = 0 -> Acorda a CPU no tempo exato
                alarm_manager.setExactAndAllowWhileIdle(0, tempo_disparo, pending_intent)
            except Exception as e:
                print(f"Erro ao agendar AlarmManager: {e}")

    def acender_e_desbloquear_tela(self):
        if platform == 'android':
            try:
                from jnius import autoclass
                PythonActivity = autoclass('org.kivy.android.PythonActivity')
                WindowManager = autoclass('android.view.WindowManager$LayoutParams')
                
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
                print(f"Erro ao acender tela: {e}")

    def disparar_busca_segundo_plano(self, dt=None):
        threading.Thread(target=self.buscar_preco_btc, daemon=True).start()

    def buscar_preco_btc(self):
        try:
            import requests
            res = requests.get("https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT", timeout=4).json()
            preco = float(res["price"])
            self.atualizar_tela_segura(preco)
        except Exception:
            try:
                import yfinance as yf
                ticker = yf.Ticker("BTC-USD")
                preco = float(ticker.fast_info['last_price'])
                self.atualizar_tela_segura(preco)
            except Exception:
                pass

    @mainthread
    def atualizar_tela_segura(self, preco_obtido):
        self.preco_atual_global = float(preco_obtido)
        self.txt_preco.text = f"U$ {self.preco_atual_global:,.2f}"

        if self.alarme_ativo and self.preco_alvo is not None and not self.alarme_tocando:
            alvo = float(self.preco_alvo)
            atual = float(self.preco_atual_global)
            
            disparar = False
            if self.modo_alarme == "ACIMA" and atual >= alvo:
                disparar = True
            elif self.modo_alarme == "ABAIXO" and atual <= alvo:
                disparar = True

            if disparar:
                self.disparar_alarme()
            else:
                # Reagenda o próximo pulso exato no sistema
                self.agendar_proximo_alarme_cascata(segundos=5)

    def disparar_alarme(self):
        self.alarme_tocando = True
        self.txt_status.text = f"🚨 ALVO ATINGIDO: U$ {self.preco_atual_global:,.2f}! 🚨"
        self.txt_status.color = get_color_from_hex('#FF3333')
        self.btn_acao.text = "PARAR SIRENE"
        self.btn_acao.background_color = get_color_from_hex('#D32F2F')
        
        self.acender_e_desbloquear_tela()
        self.tocar_sirene()

    def obter_caminho_sirene(self):
        if platform == 'android':
            try:
                from jnius import autoclass
                PythonActivity = autoclass('org.kivy.android.PythonActivity')
                activity = PythonActivity.mActivity
                caminho_app = os.path.join(activity.getFilesDir().getAbsolutePath(), "app", "sirene.mp3")
                if os.path.exists(caminho_app):
                    return caminho_app
            except Exception:
                pass
        return os.path.abspath("sirene.mp3")

    def tocar_sirene(self):
        caminho_abs = self.obter_caminho_sirene()

        if platform == 'android':
            try:
                from jnius import autoclass
                MediaPlayer = autoclass('android.media.MediaPlayer')
                AudioManager = autoclass('android.media.AudioManager')
                
                if self.android_player is not None:
                    try:
                        self.android_player.release()
                    except Exception:
                        pass

                self.android_player = MediaPlayer()
                self.android_player.setDataSource(caminho_abs)
                self.android_player.setAudioStreamType(AudioManager.STREAM_ALARM)
                self.android_player.setLooping(True)
                self.android_player.prepare()
                self.android_player.start()
            except Exception as e:
                print(f"Erro ao tocar sirene: {e}")
                self.txt_status.text = f"🚨 ALVO ATINGIDO! (Erro audio: {e})"
        else:
            try:
                from kivy.core.audio import SoundLoader
                sound = SoundLoader.load(caminho_abs)
                if sound:
                    sound.loop = True
                    sound.play()
            except Exception:
                pass

    def parar_sirene(self):
        if platform == 'android':
            if self.android_player is not None:
                try:
                    if self.android_player.isPlaying():
                        self.android_player.stop()
                    self.android_player.release()
                    self.android_player = None
                except Exception:
                    pass

    def alternar_alarme(self, instance):
        if not self.alarme_ativo and not self.alarme_tocando:
            if self.input_alvo.text and self.preco_atual_global > 0:
                try:
                    limpo = self.input_alvo.text.replace(",", ".").strip()
                    self.preco_alvo = float(limpo)
                    self.alarme_ativo = True
                    self.alarme_tocando = False
                    
                    if self.preco_alvo > self.preco_atual_global:
                        self.modo_alarme = "ACIMA"
                        texto_direcao = "se SUBIR para"
                    else:
                        self.modo_alarme = "ABAIXO"
                        texto_direcao = "se CAIR para"
                        
                    self.txt_status.text = f"Alerta ativo {texto_direcao}: U$ {self.preco_alvo:,.2f}"
                    self.txt_status.color = get_color_from_hex('#FFB300')
                    
                    self.btn_acao.text = "Desativar Alarme"
                    self.btn_acao.background_color = get_color_from_hex('#C62828')

                    # Agenda o primeiro pulso exato no AlarmManager
                    self.agendar_proximo_alarme_cascata(segundos=5)
                except ValueError:
                    pass
        else:
            self.parar_sirene()
            self.alarme_ativo = False
            self.alarme_tocando = False
            self.preco_alvo = None
            self.modo_alarme = None
            self.input_alvo.text = ""
            self.txt_status.text = "Nenhum alarme programado"
            self.txt_status.color = get_color_from_hex('#808080')
            self.btn_acao.text = "Ativar Alarme"
            self.btn_acao.background_color = get_color_from_hex('#00A843')

    def on_stop(self):
        self.parar_sirene()

if __name__ == '__main__':
    BtcAlarmApp().run()