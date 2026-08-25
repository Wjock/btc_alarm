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

        self.disparar_busca_ui()
        Clock.schedule_interval(self.disparar_busca_ui, 3)
        return layout

    def solicitar_permissao_overlay(self):
    if platform == 'android':
        try:
            from jnius import autoclass
            Settings = autoclass('android.provider.Settings')
            PythonActivity = autoclass('org.kivy.android.PythonActivity')
            activity = PythonActivity.mActivity

            # Se ainda nao puder desenhar sobre outros apps, abre a tela do sistema
            if not Settings.canDrawOverlays(activity):
                Intent = autoclass('android.content.Intent')
                Uri = autoclass('android.net.Uri')
                intent = Intent(
                    Settings.ACTION_MANAGE_OVERLAY_PERMISSION,
                    Uri.parse(f"package:{activity.getPackageName()}")
                )
                activity.startActivity(intent)
        except Exception as e:
            print(f"Erro ao solicitar overlay: {e}")
    
    
    
    def _update_rect(self, instance, value):
        self.rect.pos = instance.pos
        self.rect.size = instance.size

    def iniciar_servico_android(self, alvo, modo):
        if platform == 'android':
            try:
                from jnius import autoclass
                PythonActivity = autoclass('org.kivy.android.PythonActivity')
                activity = PythonActivity.mActivity
                
                # Monta os dados para o servico de segundo plano
                dados = json.dumps({"alvo": alvo, "modo": modo})
                
                service_class = autoclass('org.btcalarm.ServiceMonitoramento')
                service_class.start(activity, dados)
            except Exception as e:
                print(f"Erro ao iniciar servico: {e}")

    def parar_servico_android(self):
        if platform == 'android':
            try:
                from jnius import autoclass
                PythonActivity = autoclass('org.kivy.android.PythonActivity')
                activity = PythonActivity.mActivity
                service_class = autoclass('org.btcalarm.ServiceMonitoramento')
                service_class.stop(activity)
            except Exception as e:
                print(f"Erro ao parar servico: {e}")

    def disparar_busca_ui(self, dt=None):
        threading.Thread(target=self.buscar_preco_btc, daemon=True).start()

    def buscar_preco_btc(self):
        try:
            import requests
            res = requests.get("https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT", timeout=3).json()
            preco = float(res["price"])
            self.atualizar_preco_ui(preco)
        except Exception:
            pass

    @mainthread
    def atualizar_preco_ui(self, preco_obtido):
        self.preco_atual_global = float(preco_obtido)
        self.txt_preco.text = f"U$ {self.preco_atual_global:,.2f}"

    def alternar_alarme(self, instance):
        if not self.alarme_ativo:
            if self.input_alvo.text and self.preco_atual_global > 0:
                try:
                    limpo = self.input_alvo.text.replace(",", ".").strip()
                    self.preco_alvo = float(limpo)
                    self.alarme_ativo = True
                    
                    if self.preco_alvo > self.preco_atual_global:
                        self.modo_alarme = "ACIMA"
                        texto_direcao = "se SUBIR para"
                    else:
                        self.modo_alarme = "ABAIXO"
                        texto_direcao = "se CAIR para"
                        
                    self.txt_status.text = f"Alerta ativo no escuro {texto_direcao}: U$ {self.preco_alvo:,.2f}"
                    self.txt_status.color = get_color_from_hex('#FFB300')
                    
                    self.btn_acao.text = "Desativar Alarme"
                    self.btn_acao.background_color = get_color_from_hex('#C62828')

                    # Dispara o monitoramento nativo no escuro
                    self.iniciar_servico_android(self.preco_alvo, self.modo_alarme)
                except ValueError:
                    pass
        else:
            self.parar_servico_android()
            self.alarme_ativo = False
            self.preco_alvo = None
            self.modo_alarme = None
            self.input_alvo.text = ""
            self.txt_status.text = "Nenhum alarme programado"
            self.txt_status.color = get_color_from_hex('#808080')
            self.btn_acao.text = "Ativar Alarme"
            self.btn_acao.background_color = get_color_from_hex('#00A843')

if __name__ == '__main__':
    BtcAlarmApp().run()