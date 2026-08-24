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
        self.preco_atual_global = 0.0
        self.alarme_tocando = False
        self.android_player = None

        if platform == 'android':
            from jnius import autoclass
            PythonActivity = autoclass('org.kivy.android.PythonActivity')
            activity = PythonActivity.mActivity
            self.caminho_config = os.path.join(activity.getFilesDir().getAbsolutePath(), "app", "alarm_config.json")
        else:
            self.caminho_config = "alarm_config.json"

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
        Clock.schedule_interval(self.disparar_busca_segundo_plano, 4)
        return layout

    def _update_rect(self, instance, value):
        self.rect.pos = instance.pos
        self.rect.size = instance.size

    def gerenciar_servico_android(self, iniciar=True):
        if platform == 'android':
            try:
                from jnius import autoclass
                PythonActivity = autoclass('org.kivy.android.PythonActivity')
                activity = PythonActivity.mActivity
                
                # Tenta inicializar a classe do serviço
                service = autoclass('org.test.btcalarm.ServiceMonitoramento')
                if iniciar:
                    service.start(activity, '')
                else:
                    service.stop(activity)
            except Exception as e:
                print(f"Aviso ao gerenciar servico: {e}")

    def salvar_configuracao(self, ativo):
        dados = {
            "preco_alvo": self.preco_alvo,
            "modo": self.modo_alarme,
            "ativo": ativo,
            "disparado": False
        }
        try:
            os.makedirs(os.path.dirname(self.caminho_config), exist_ok=True)
            with open(self.caminho_config, "w") as f:
                json.dump(dados, f)
        except Exception:
            pass

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

            # Diagnosticando no Logcat
            print(f"[BTC_DEBUG] Modo: {self.modo_alarme} | Atual: {atual} | Alvo: {alvo} | Disparar: {disparar}")

            if disparar:
                print("[BTC_DEBUG] >>> ENTROU NA ROTINA DISPARAR ALARME! <<<")
                self.disparar_alarme()

    def disparar_alarme(self):
        self.alarme_tocando = True
        # Confirmação visual imediata na tela
        self.txt_status.text = f"🚨 ALVO ATINGIDO: U$ {self.preco_atual_global:,.2f}! 🚨"
        self.txt_status.color = get_color_from_hex('#FF3333')
        self.btn_acao.text = "PARAR SIRENE"
        self.btn_acao.background_color = get_color_from_hex('#D32F2F')
        
        self.acender_e_desbloquear_tela()
        self.tocar_sirene()
        
    def tocar_sirene_local(self):
        nome_arquivo = "sirene.mp3"
        caminho_abs = os.path.abspath(nome_arquivo)

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
                print(f"Erro audio local: {e}")

    def parar_sirene_local(self):
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
        if not self.alarme_ativo:
            if self.input_alvo.text and self.preco_atual_global > 0:
                try:
                    limpo = self.input_alvo.text.replace(",", ".")
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

                    self.salvar_configuracao(ativo=True)
                    self.gerenciar_servico_android(iniciar=True)
                except ValueError:
                    pass
        else:
            self.parar_sirene_local()
            self.alarme_ativo = False
            self.alarme_tocando = False
            self.preco_alvo = None
            self.modo_alarme = None
            self.input_alvo.text = ""
            self.txt_status.text = "Nenhum alarme programado"
            self.txt_status.color = get_color_from_hex('#808080')
            self.btn_acao.text = "Ativar Alarme"
            self.btn_acao.background_color = get_color_from_hex('#00A843')

            self.salvar_configuracao(ativo=False)
            self.gerenciar_servico_android(iniciar=False)

if __name__ == '__main__':
    BtcAlarmApp().run()