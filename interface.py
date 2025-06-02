from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QPushButton, QVBoxLayout, QHBoxLayout, QFrame, QSizePolicy
from PyQt5.QtCore import Qt, QTimer, QThread, pyqtSignal
from datetime import datetime
import sys, glob, time
from pleth_curve import PlethCurve
from threadpleth import PlethThread
from resp_curve import RespCurve
from rpm_calc import RPMCalculator
from spo2_calc import SpO2Calculator
from PyQt5.QtWidgets import QMessageBox
import RPi.GPIO as GPIO
from PyQt5.QtCore import QThread, pyqtSignal
import numpy as np
import pyqtgraph as pg
from threadecg import ECGThread, DeteccionModo # Asegúrate de que el archivo se llame así

ecg_thread = ECGThread()

ecg_thread.metodo_deteccion = DeteccionModo.PAN_TOMPKINS  # <- aquí cambias el modo



GPIO.setwarnings(False)

# Config buzzer
BUZZER_PIN = 12  # Pin físico 12 (GPIO18)
#Variables globales
silencio_activado = False
silencio_inicio = None
inicio_medicion = None  # para guardar el tiempo en que se inicia

GPIO.setmode(GPIO.BOARD)
GPIO.setup(BUZZER_PIN, GPIO.OUT)
GPIO.output(BUZZER_PIN, GPIO.LOW)  # ← Inicialmente apagado

def silenciar_alarma():
    global silencio_activado, silencio_inicio
    silencio_activado = True
    silencio_inicio = time.time()
    detener_buzzer()  # Esto también ocultará el botón

def activar_buzzer():
    try:
        GPIO.output(BUZZER_PIN, GPIO.HIGH)
        btn_silenciar.show()
    except RuntimeError as e:
        print(f"[ERROR] Error al activar buzzer: {e}")


def detener_buzzer():
    try:
        GPIO.output(BUZZER_PIN, GPIO.LOW)
    except RuntimeError:
        pass
    btn_silenciar.hide()

def actualizar_estado_silencio():
    global silencio_activado, silencio_inicio
    if silencio_activado:
        segundos_restantes = int(60 - (time.time() - silencio_inicio))
        if segundos_restantes > 0:
            alarma_silenciada_label.setText(f"Alarma silenciada ({segundos_restantes}s)")
            alarma_silenciada_label.show()
        else:
            silencio_activado = False
            alarma_silenciada_label.hide()

# Sensor de temperatura
base_dir = '/sys/bus/w1/devices/'
device_folder = glob.glob(base_dir + '28*')[0]``
device_file = device_folder + '/w1_slave'

class TempReader(QThread):
    update_temp = pyqtSignal(str)
    def __init__(self):
        super().__init__()
        self.running = False

    def run(self):
        self.running = True
        while self.running:
            try:
                with open(device_file, 'r') as f:
                    lines = f.readlines()
                while lines[0].strip()[-3:] != 'YES':
                    with open(device_file, 'r') as f:
                        lines = f.readlines()
                equals_pos = lines[1].find('t=')
                if equals_pos != -1:
                    temp_string = lines[1][equals_pos + 2:]
                    temp_c = float(temp_string) / 1000.0
                    self.update_temp.emit(f"{temp_c:.1f} °C")
            except:
                self.update_temp.emit("Error")
            time.sleep(0.5)

    def stop(self):
        self.running = False
        self.wait()

# App
app = QApplication(sys.argv)
screen = app.primaryScreen()
size = screen.size()

ventana = QWidget()
ventana.setWindowTitle("LUMEA - Monitor de Signos Vitales")
ventana.setStyleSheet("background-color: #000000;")

# Encabezado
reloj = QLabel()
reloj.setStyleSheet("font-size: 14pt; color: #FCEDFA;")
titulo = QLabel("LUMEA")
titulo.setStyleSheet("font-size: 14pt; font-weight: bold; color: #FCEDFA;")
alarma_silenciada_label = QLabel("")
alarma_silenciada_label.setStyleSheet("font-size: 12pt; color: yellow;")
alarma_silenciada_label.hide()

encabezado = QVBoxLayout()
encabezado_superior = QHBoxLayout()
encabezado_superior.addWidget(reloj)
encabezado_superior.addStretch()
encabezado_superior.addWidget(titulo)

encabezado.addLayout(encabezado_superior)
encabezado.addWidget(alarma_silenciada_label)

# Curvas
ppg_curve = PlethCurve(curve_color="#AEF7BD")
ppg_curve.setFixedHeight(int(size.height() * 0.20))
ppg_curve.setFixedWidth(int(size.width() * 0.75))

resp_curve = RespCurve(curve_color="#33DFEB")
resp_curve.setFixedHeight(int(size.height() * 0.20))
resp_curve.setFixedWidth(int(size.width() * 0.75))

# ECG
ecg_plot = pg.PlotWidget(background='k')
ecg_plot.enableAutoRange(axis='y', enable=True)
ecg_plot.hideAxis('left')
ecg_plot.hideAxis('bottom')
ecg_curve = ecg_plot.plot(pen=pg.mkPen('m', width=2))
ecg_peaks_curve = ecg_plot.plot(pen=None, symbol='o', symbolBrush='r', symbolSize=6)


# 🔴 Bloque de temperatura, SpO₂ y respiración (orden modificado)
temp_block = QVBoxLayout()

# TEMP
temp_title = QLabel("TEMP")
temp_title.setStyleSheet("font-size: 14pt; color: #DC2EC4; font-weight: bold;")

temp_value = QLabel("--- °C")
temp_value.setStyleSheet("font-size: 22pt; color: #DC2EC4; font-weight: bold;")

temp_range = QLabel("36.5  37.5")
temp_range.setStyleSheet("font-size: 10pt; color: #DC2EC4;")

temp_block.addWidget(temp_title, alignment=Qt.AlignLeft)
temp_block.addWidget(temp_value, alignment=Qt.AlignLeft)
temp_block.addWidget(temp_range, alignment=Qt.AlignLeft)

# SpO₂ (sube de posición)
spo2_title = QLabel("SpO₂")
spo2_title.setStyleSheet("font-size: 14pt; color: #A0EEBB; font-weight: bold;")

spo2_value = QLabel("--- %")
spo2_value.setStyleSheet("font-size: 22pt; color: #A0EEBB; font-weight: bold;")

spo2_range = QLabel("95  100")
spo2_range.setStyleSheet("font-size: 10pt; color: #A0EEBB;")

temp_block.addSpacing(20)
temp_block.addWidget(spo2_title, alignment=Qt.AlignLeft)
temp_block.addWidget(spo2_value, alignment=Qt.AlignLeft)
temp_block.addWidget(spo2_range, alignment=Qt.AlignLeft)

# RESP (baja de posición)
rpm_title = QLabel("RESP")
rpm_title.setStyleSheet("font-size: 14pt; color: #33DFEB; font-weight: bold;")

rpm_value = QLabel("--- rpm")
rpm_value.setStyleSheet("font-size: 22pt; color: #33DFEB; font-weight: bold;")

rpm_range = QLabel("12  20")
rpm_range.setStyleSheet("font-size: 10pt; color: #33DFEB;")

temp_block.addSpacing(20)
temp_block.addWidget(rpm_title, alignment=Qt.AlignLeft)
temp_block.addWidget(rpm_value, alignment=Qt.AlignLeft)
temp_block.addWidget(rpm_range, alignment=Qt.AlignLeft)

# BPM
bpm_title = QLabel("BPM")
bpm_title.setStyleSheet("font-size: 14pt; color: #F99E4C; font-weight: bold;")

bpm_value = QLabel("---")
bpm_value.setStyleSheet("font-size: 22pt; color: #F99E4C; font-weight: bold;")

bpm_range = QLabel("60  100")
bpm_range.setStyleSheet("font-size: 10pt; color: #F99E4C;")

temp_block.addSpacing(20)
temp_block.addWidget(bpm_title, alignment=Qt.AlignLeft)
temp_block.addWidget(bpm_value, alignment=Qt.AlignLeft)
temp_block.addWidget(bpm_range, alignment=Qt.AlignLeft)


temp_block.addStretch()

temp_container = QFrame()
temp_container.setFixedWidth(size.width() // 6)
temp_container.setLayout(temp_block)



# Cuerpo principal
ppg_label = QLabel("PPG")
ppg_label.setStyleSheet("font-size: 12pt; color: white;")
resp_label = QLabel("Resp")
resp_label.setStyleSheet("font-size: 12pt; color: white;")

curvas_vertical = QVBoxLayout()
curvas_vertical.addWidget(ppg_label, alignment=Qt.AlignLeft)
curvas_vertical.addWidget(ppg_curve)
curvas_vertical.addWidget(resp_label, alignment=Qt.AlignLeft)
curvas_vertical.addWidget(resp_curve)
ecg_label = QLabel("ECG")
ecg_label.setStyleSheet("font-size: 12pt; color: white;")
curvas_vertical.addWidget(ecg_label, alignment=Qt.AlignLeft)
curvas_vertical.addWidget(ecg_plot)


main_content = QHBoxLayout()
main_content.addLayout(curvas_vertical, stretch=5)
main_content.addWidget(temp_container, stretch=1)

# Botones inferiores
boton_style = "font-size: 16pt; padding: 15px 30px; font-weight: bold;"
btn_salir = QPushButton("Salir")
btn_salir.setStyleSheet(boton_style + "background-color: #ccc; color: black;")

btn_iniciar = QPushButton("Iniciar medicion")
btn_iniciar.setStyleSheet(boton_style + "background-color: #4CAF50; color: black;")

btn_pausar = QPushButton("Interrumpir medicion")
btn_pausar.setStyleSheet(boton_style + "background-color: #f44336; color: black;")
btn_pausar.hide()

btn_continuar = QPushButton("Continuar medicion")
btn_continuar.setStyleSheet(boton_style + "background-color: #2196F3; color: black;")
btn_continuar.hide()

btn_limpiar = QPushButton("Limpiar datos")
btn_limpiar.setStyleSheet("font-size: 16pt; padding: 15px 40px; font-weight: bold; background-color: #FFE047; color: black;")
btn_limpiar.hide()

btn_silenciar = QPushButton("Silenciar alarma")
btn_silenciar.setStyleSheet("font-size: 16pt; padding: 15px 30px; font-weight: bold; background-color: #DDDDDD; color: black;")
btn_silenciar.hide()

botones_layout = QHBoxLayout()
botones_layout.addWidget(btn_salir)
botones_layout.addStretch()
botones_layout.addWidget(btn_iniciar)
botones_layout.addWidget(btn_pausar)
botones_layout.addWidget(btn_continuar)
botones_layout.addWidget(btn_limpiar)
botones_layout.addWidget(btn_silenciar)

# Integracion final
main_layout = QVBoxLayout()
main_layout.addLayout(encabezado)
main_layout.addSpacing(10)
main_layout.addLayout(main_content)
main_layout.addStretch()
main_layout.addLayout(botones_layout)

ventana.setLayout(main_layout)
ventana.showFullScreen()

def actualizar_hora():
    reloj.setText(datetime.now().strftime("%Y-%m-%d  %H:%M:%S"))

timer = QTimer()
timer.timeout.connect(actualizar_hora)
timer.timeout.connect(actualizar_estado_silencio)
timer.start(1000)
actualizar_hora()

pleth_thread = PlethThread()
rpm_calculator = RPMCalculator(sampling_rate=33)
spo2_calculator = SpO2Calculator(window_size=100)

def verificar_alerta():
    global silencio_activado, silencio_inicio, buzzer_encendido_desde

    print(f"[DEBUG] silencio_activado={silencio_activado}, inicio_medicion={inicio_medicion}")

    buzzer_permitido = True

    # Silencio activado manualmente
    if silencio_activado:
        if time.time() - silencio_inicio < 60:
            buzzer_permitido = False
            segundos_restantes = int(60 - (time.time() - silencio_inicio))
            alarma_silenciada_label.setText(f"Alarma silenciada ({segundos_restantes}s)")
            alarma_silenciada_label.show()
            print(f"[DEBUG] Buzzer silenciado. Tiempo restante: {segundos_restantes}s")
        else:
            silencio_activado = False
            alarma_silenciada_label.hide()
            print("[DEBUG] Fin del modo silencio, buzzer permitido.")

    # ⏳ Esperar tiempo de estabilización tras iniciar medición
    if inicio_medicion and (time.time() - inicio_medicion < 25):
        segundos_restantes = int(25 - (time.time() - inicio_medicion))
        alarma_silenciada_label.setText(f"Esperando estabilización ({segundos_restantes}s)")
        alarma_silenciada_label.show()
        detener_buzzer()
        return

    try:
        temp_text = temp_value.text().replace('°C', '').strip()
        spo2_text = spo2_value.text().replace('%', '').strip()
        rpm_text = rpm_value.text().replace('rpm', '').strip()
        bpm_text = bpm_value.text().strip()

        print(f"[DEBUG] Valores recibidos: Temp={temp_text}, SpO2={spo2_text}, RPM={rpm_text}, BPM={bpm_text}")

        if '---' in [temp_text, spo2_text, rpm_text]:
            print("[DEBUG] Valores incompletos, deteniendo buzzer.")
            detener_buzzer()
            return

        temp = float(temp_text)
        spo2 = int(spo2_text)
        rpm = rpm_calculator.get_rpm()
        bpm = float(bpm_text)

    except Exception as e:
        print(f"[ERROR] Exception en verificar_alerta: {e}")
        detener_buzzer()
        return

    # TEMP
    if temp < 36 or temp > 37.5:
        temp_title.setStyleSheet("font-size: 14pt; color: red; font-weight: bold;")
        temp_value.setStyleSheet("font-size: 22pt; color: red; font-weight: bold;")
        temp_range.setStyleSheet("font-size: 10pt; color: red;")
        temp_alarma = True
    else:
        temp_title.setStyleSheet("font-size: 14pt; color: #DC2EC4; font-weight: bold;")
        temp_value.setStyleSheet("font-size: 22pt; color: #DC2EC4; font-weight: bold;")
        temp_range.setStyleSheet("font-size: 10pt; color: #DC2EC4;")
        temp_alarma = False

    # SpO₂
    if spo2 < 90:
        spo2_title.setStyleSheet("font-size: 14pt; color: red; font-weight: bold;")
        spo2_value.setStyleSheet("font-size: 22pt; color: red; font-weight: bold;")
        spo2_range.setStyleSheet("font-size: 10pt; color: red;")
        spo2_alarma = True
    else:
        spo2_title.setStyleSheet("font-size: 14pt; color: #A0EEBB; font-weight: bold;")
        spo2_value.setStyleSheet("font-size: 22pt; color: #A0EEBB; font-weight: bold;")
        spo2_range.setStyleSheet("font-size: 10pt; color: #A0EEBB;")
        spo2_alarma = False

    # RPM
    rpm_history = rpm_calculator.rpm_history[-5:]
    fuera_de_rango = [r for r in rpm_history if r < 12 or r > 20]

    if len(fuera_de_rango) >= 3:
        rpm_prom = int(np.mean(fuera_de_rango))
        rpm_value.setText(f"{rpm_prom} rpm")
        if rpm_prom < 12 or rpm_prom > 20:
            rpm_title.setStyleSheet("font-size: 14pt; color: red; font-weight: bold;")
            rpm_value.setStyleSheet("font-size: 22pt; color: red; font-weight: bold;")
            rpm_range.setStyleSheet("font-size: 10pt; color: red;")
            rpm_alarma = True
        else:
            rpm_title.setStyleSheet("font-size: 14pt; color: #33DFEB; font-weight: bold;")
            rpm_value.setStyleSheet("font-size: 22pt; color: #33DFEB; font-weight: bold;")
            rpm_range.setStyleSheet("font-size: 10pt; color: #33DFEB;")
            rpm_alarma = False
    else:
        rpm_value.setText(f"{rpm} rpm")
        if rpm < 12 or rpm > 20:
            rpm_title.setStyleSheet("font-size: 14pt; color: red; font-weight: bold;")
            rpm_value.setStyleSheet("font-size: 22pt; color: red; font-weight: bold;")
            rpm_range.setStyleSheet("font-size: 10pt; color: red;")
            rpm_alarma = True
        else:
            rpm_title.setStyleSheet("font-size: 14pt; color: #33DFEB; font-weight: bold;")
            rpm_value.setStyleSheet("font-size: 22pt; color: #33DFEB; font-weight: bold;")
            rpm_range.setStyleSheet("font-size: 10pt; color: #33DFEB;")
            rpm_alarma = False

    # BPM
    if bpm < 60 or bpm > 100:
        bpm_title.setStyleSheet("font-size: 14pt; color: red; font-weight: bold;")
        bpm_value.setStyleSheet("font-size: 22pt; color: red; font-weight: bold;")
        bpm_range.setStyleSheet("font-size: 10pt; color: red;")
        bpm_alarma = True
    else:
        bpm_title.setStyleSheet("font-size: 14pt; color: #F99E4C; font-weight: bold;")
        bpm_value.setStyleSheet("font-size: 22pt; color: #F99E4C; font-weight: bold;")
        bpm_range.setStyleSheet("font-size: 10pt; color: #F99E4C;")
        bpm_alarma = False

    # Evaluar si se activa alarma general
    alarma_activa = temp_alarma or spo2_alarma or rpm_alarma or bpm_alarma

    if alarma_activa and buzzer_permitido:
        activar_buzzer()
    else:
        detener_buzzer()

    # Ocultar mensaje si todo está normal
    alarma_silenciada_label.hide()



def handle_ir(ir_val):
    ppg_curve.update_plot(ir_val)
    resp_curve.update_plot(ir_val)
    rpm = rpm_calculator.update(resp_curve.get_filtered_value())
    rpm_value.setText(f"{rpm} rpm")
    verificar_alerta()



def handle_ir_red(ir_val, red_val):
    spo2 = spo2_calculator.update(ir_val, red_val)
    spo2_value.setText(spo2 if '%' in str(spo2) else f"{spo2} %")
    verificar_alerta()

ecg_buffer = []

def update_ecg(val):
    ecg_buffer.append(val)
    if len(ecg_buffer) > 500:
        ecg_buffer.pop(0)
    ecg_curve.setData(ecg_buffer)

def update_ecg_peaks(indices, values):
    ecg_peaks_curve.setData(indices, values)

def update_bpm(val):
    bpm_value.setText(f"{val:.1f}")
    #print(f"❤️ BPM: {val:.1f}")
    if val < 60 or val > 100:
        bpm_title.setStyleSheet("font-size: 14pt; color: red; font-weight: bold;")
        bpm_value.setStyleSheet("font-size: 22pt; color: red; font-weight: bold;")
        bpm_range.setStyleSheet("font-size: 10pt; color: red;")
    else:
        bpm_title.setStyleSheet("font-size: 14pt; color: #F99E4C; font-weight: bold;")
        bpm_value.setStyleSheet("font-size: 22pt; color: #F99E4C; font-weight: bold;")
        bpm_range.setStyleSheet("font-size: 10pt; color: #F99E4C;")


pleth_thread.new_ir.connect(handle_ir)
pleth_thread.new_ir_red.connect(handle_ir_red)

ecg_thread.new_ecg.connect(update_ecg)

ecg_thread.new_bpm.connect(update_bpm)



sensor_thread = None
def iniciar_medicion():
    global inicio_medicion
    inicio_medicion = time.time()
    global sensor_thread
    sensor_thread = TempReader()
    sensor_thread.update_temp.connect(temp_value.setText)
    sensor_thread.start()
    pleth_thread.start()
    btn_iniciar.hide()
    btn_pausar.show()
    ecg_thread.start()


def pausar_medicion():
    global inicio_medicion, silencio_activado, silencio_inicio
    if sensor_thread and sensor_thread.isRunning():
        sensor_thread.stop()
    pleth_thread.stop()
    ecg_thread.stop()
    detener_buzzer()
    inicio_medicion = None

    # 🟡 Activa modo silencio por 60 segundos
    silencio_activado = True
    silencio_inicio = time.time()

    btn_pausar.hide()
    btn_continuar.show()
    btn_limpiar.show()

def continuar_medicion():
    iniciar_medicion()
    btn_continuar.hide()
    btn_limpiar.hide()

def limpiar_datos():
    confirm = QMessageBox()
    confirm.setWindowTitle("Confirmar limpieza de información")
    confirm.setText("¿Está seguro que desea borrar los datos actuales?")
    confirm.setIcon(QMessageBox.Warning)
    confirm.setStandardButtons(QMessageBox.Yes | QMessageBox.Cancel)
    confirm.setDefaultButton(QMessageBox.Cancel)
    detener_buzzer()

    respuesta = confirm.exec_()
    
    if respuesta == QMessageBox.Yes:
        if sensor_thread and sensor_thread.isRunning():
            sensor_thread.stop()

        if ecg_thread and ecg_thread.isRunning():
            ecg_thread.stop()

        ppg_curve.clear()
        resp_curve.clear()
        temp_value.setText("--- °C")
        rpm_value.setText("--- rpm")
        spo2_value.setText("--- %")
        temp_title.setStyleSheet("font-size: 14pt; color: #DC2EC4; font-weight: bold;")
        temp_value.setStyleSheet("font-size: 22pt; color: #DC2EC4; font-weight: bold;")
        temp_range.setStyleSheet("font-size: 10pt; color: #DC2EC4;")
        spo2_title.setStyleSheet("font-size: 14pt; color: #A0EEBB; font-weight: bold;")
        spo2_value.setStyleSheet("font-size: 22pt; color: #A0EEBB; font-weight: bold;")
        spo2_range.setStyleSheet("font-size: 10pt; color: #A0EEBB;")
        rpm_title.setStyleSheet("font-size: 14pt; color: #33DFEB; font-weight: bold;")
        rpm_value.setStyleSheet("font-size: 22pt; color: #33DFEB; font-weight: bold;")
        rpm_range.setStyleSheet("font-size: 10pt; color: #33DFEB;")
        ecg_curve.clear()
        bpm_value.setText("---")
        bpm_title.setStyleSheet("font-size: 14pt; color: #F99E4C; font-weight: bold;")
        bpm_value.setStyleSheet("font-size: 22pt; color: #F99E4C; font-weight: bold;")
        bpm_range.setStyleSheet("font-size: 10pt; color: #F99E4C;")
        rpm_calculator.last_rpm_display = "---"
        rpm_calculator.last_update_time = time.time()
        spo2_calculator.ir_values.clear()
        spo2_calculator.red_values.clear()
        spo2_calculator.last_spo2 = "---"
        spo2_calculator.last_time = time.time()
        btn_continuar.hide()
        btn_limpiar.hide()
        btn_iniciar.show()

def cerrar_app():
    if sensor_thread and sensor_thread.isRunning():
        sensor_thread.stop()
    pleth_thread.stop()
    try:
        detener_buzzer()
        GPIO.cleanup()
    except:
        pass
    ventana.close()

btn_iniciar.clicked.connect(iniciar_medicion)
btn_pausar.clicked.connect(pausar_medicion)
btn_continuar.clicked.connect(continuar_medicion)
btn_limpiar.clicked.connect(limpiar_datos)
btn_salir.clicked.connect(cerrar_app)
btn_silenciar.clicked.connect(silenciar_alarma)

sys.exit(app.exec_())