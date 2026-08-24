import os
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
        self.alarme_tocando = False
        self.preco_atual_global = 0.0
        
        self.android_player = None
        self.pc_sirene = None
        self.wake_lock = None

        layout = BoxLayout(
            orientation='vertical',
            padding=[30, 40, 30, 20],
            spacing=15
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
            height=70,
            font_size='20sp',
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
        Clock.schedule_interval(self.disparar_busca_segundo_plano, 4)
        return layout

    def _update_rect(self, instance, value):
        self.rect.pos = instance.pos
        self.rect.size = instance.size

    def adquirir_wakelock(self):
        if platform == 'android' and self.wake_lock is None:
            try:
                from jnius import autoclass
                PythonActivity = autoclass('org.kivy.android.PythonActivity')
                Context = autoclass('android.content.Context')
                PowerManager = autoclass('android.os.PowerManager')

                activity = PythonActivity.mActivity
                power_manager = activity.getSystemService(Context.POWER_SERVICE)
                
                self.wake_lock = power_manager.newWakeLock(1, "BtcAlarm::WakeLockTag")
                self.wake_lock.acquire()
            except Exception as e:
                print(f"Erro ao adquirir WakeLock: {e}")

    def soltar_wakelock(self):
        if platform == 'android' and self.wake_lock is not None:
            try:
                if self.wake_lock.isHeld():
                    self.wake_lock.release()
                self.wake_lock = None
            except Exception as e:
                print(f"Erro ao soltar WakeLock: {e}")

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
                print(f"Erro ao forçar acendimento da tela: {e}")

    def disparar_busca_segundo_plano(self, dt=None):
        threading.Thread(target=self.buscar_preco_btc, daemon=True).start()

    def buscar_preco_btc(self):
        try:
            import yfinance as yf
            ticker = yf.Ticker("BTC-USD")
            preco = float(ticker.fast_info['last_price'])
            self.atualizar_tela_segura(preco)
        except Exception:
            try:
                import requests
                res = requests.get("https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT", timeout=4).json()
                preco = float(res["price"])
                self.atualizar_tela_segura(preco)
            except Exception:
                self.notificar_erro_tela()

    @mainthread
    def atualizar_tela_segura(self, preco_obtido):
        self.preco_atual_global = preco_obtido
        self.txt_preco.text = f"U$ {self.preco_atual_global:,.2f}"

        if self.preco_alvo is not None and not self.alarme_tocando:
            disparar = False
            if self.modo_alarme == "ACIMA" and self.preco_atual_global >= self.preco_alvo:
                disparar = True
            elif self.modo_alarme == "ABAIXO" and self.preco_atual_global <= self.preco_alvo:
                disparar = True

            if disparar:
                self.alarme_tocando = True
                self.txt_status.text = f"🚨 ALVO ATINGIDO: U$ {self.preco_atual_global:,.2f}! 🚨"
                self.txt_status.color = get_color_from_hex('#FF3333')
                
                self.tocar_sirene()
                
                self.btn_acao.text = "PARAR SIRENE"
                self.btn_acao.background_color = get_color_from_hex('#D32F2F')

    @mainthread
    def notificar_erro_tela(self):
        if self.preco_atual_global > 0:
            self.txt_preco.text = f"U$ {self.preco_atual_global:,.2f} (Sinc...)"
        else:
            self.txt_preco.text = "Conectando..."

    def tocar_sirene(self):
        nome_arquivo = "sirene.mp3"
        caminho_abs = os.path.abspath(nome_arquivo)

        self.acender_e_desbloquear_tela()

        if platform == 'android':
            try:
                from jnius import autoclass
                MediaPlayer = autoclass('android.media.MediaPlayer')
                AudioManager = autoclass('android.media.AudioManager')
                
                if self.android_player is not None:
                    self.android_player.release()

                self.android_player = MediaPlayer()
                self.android_player.setDataSource(caminho_abs)
                self.android_player.setAudioStreamType(AudioManager.STREAM_ALARM)
                self.android_player.setLooping(True)
                self.android_player.prepare()
                self.android_player.start()
            except Exception as e:
                self.txt_status.text = f"Erro Audio Android: {str(e)}"
        else:
            try:
                from kivy.core.audio import SoundLoader
                if not self.pc_sirene:
                    self.pc_sirene = SoundLoader.load(caminho_abs)
                if self.pc_sirene:
                    self.pc_sirene.loop = True
                    self.pc_sirene.play()
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
        else:
            if self.pc_sirene:
                self.pc_sirene.stop()

    def alternar_alarme(self, instance):
        if not self.alarme_tocando:
            if self.input_alvo.text and self.preco_atual_global > 0:
                try:
                    limpo = self.input_alvo.text.replace(",", ".")
                    self.preco_alvo = float(limpo)
                    self.alarme_tocando = False
                    
                    if self.preco_alvo > self.preco_atual_global:
                        self.modo_alarme = "ACIMA"
                        texto_direcao = "se SUBIR para"
                    else:
                        self.modo_alarme = "ABAIXO"
                        texto_direcao = "se CAIR para"
                        
                    self.txt_status.text = f"Alerta ativo {texto_direcao}: U$ {self.preco_alvo:,.2f}"
                    self.txt_status.color = get_color_from_hex('#FFB300')
                    
                    self.adquirir_wakelock()
                except ValueError:
                    pass
        else:
            self.parar_sirene()
            self.soltar_wakelock()
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
        self.soltar_wakelock()

if __name__ == '__main__':
    BtcAlarmApp().run()