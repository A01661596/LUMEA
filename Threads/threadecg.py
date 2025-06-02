import time
import numpy as np
import serial
from enum import Enum

from PyQt5.QtCore import QThread, pyqtSignal
from scipy.signal import butter, lfilter, find_peaks
import neurokit2 as nk

class DeteccionModo(Enum):
    FIND_PEAKS = 1
    PAN_TOMPKINS = 2

class ECGThread(QThread):
    new_ecg = pyqtSignal(float)
    new_bpm = pyqtSignal(float)
    new_peaks = pyqtSignal(list, list)
    evento_detectado = pyqtSignal(str)
    buffer_listo = pyqtSignal(list)

    def __init__(self, parent=None, port='/dev/ttyACM0', baudrate=115200, metodo_deteccion=DeteccionModo.FIND_PEAKS):
        super().__init__(parent)
        self.metodo_deteccion = metodo_deteccion
        self.running = False
        self.alertas_activadas = False  # 🔇 Desactivar alertas por defecto
        self.SAMPLING_RATE = 500
        self.BUFFER_SIZE = 3750
        self.data = []
        self.last_event_time = 0
        self.port = port
        self.baudrate = baudrate
        self.ser = None

    def run(self):
        try:
            self.ser = serial.Serial(self.port, self.baudrate, timeout=1)
            time.sleep(2)
            self.running = True
            print("📡 Lectura desde Arduino iniciada")

            while self.running:
                if self.ser.in_waiting > 0:
                    linea = self.ser.readline().decode('utf-8', errors='ignore').strip()
                    if linea.isdigit():
                        val = int(linea)
                        val = (val / 32768.0) * 4.096  # Escala para ADS1115 (GAIN_ONE)
                        self.data.append(val)
                        self.new_ecg.emit(val)

                        if len(self.data) > self.BUFFER_SIZE:
                            self.data.pop(0)

                        if len(self.data) >= self.SAMPLING_RATE * 5:
                            self.check_for_events()
        except Exception as e:
            print(f"❌ Error de conexión serial: {e}")

    def check_for_events(self):
        ecg_segment = self.bandpass_filter(self.data[-self.SAMPLING_RATE * 5:])

        if self.metodo_deteccion == DeteccionModo.FIND_PEAKS:
            peaks, _ = find_peaks(ecg_segment, distance=0.25 * self.SAMPLING_RATE, prominence=0.5)
        elif self.metodo_deteccion == DeteccionModo.PAN_TOMPKINS:
            try:
                processed = nk.ecg_process(ecg_segment, sampling_rate=self.SAMPLING_RATE)
                peaks = processed[1]["ECG_R_Peaks"]
            except Exception as e:
                print(f"❌ Error en Pan-Tompkins: {e}")
                return
        else:
            print("⚠️ Modo de detección no válido.")
            return

        if len(peaks) > 2:
            rr_intervals = np.diff(peaks) / self.SAMPLING_RATE
            rr_valid = [r for r in rr_intervals if 0.25 < r < 2.0]
            if len(rr_valid) > 1:
                bpm = 60 / np.mean(rr_valid)
                self.new_bpm.emit(bpm)

                # 🔇 Bloque de alertas (controlado por bandera)
                if self.alertas_activadas:
                    now = time.time()
                    if bpm > 120 and now - self.last_event_time > 30:
                        self.evento_detectado.emit("taquicardia")
                        self.buffer_listo.emit(self.data[-self.BUFFER_SIZE:])
                        self.last_event_time = now
                    elif bpm < 50 and now - self.last_event_time > 30:
                        self.evento_detectado.emit("bradicardia")
                        self.buffer_listo.emit(self.data[-self.BUFFER_SIZE:])
                        self.last_event_time = now

    def bandpass_filter(self, signal, lowcut=0.5, highcut=40):
        nyq = 0.5 * self.SAMPLING_RATE
        low = lowcut / nyq
        high = highcut / nyq
        b, a = butter(1, [low, high], btype='band')
        return lfilter(b, a, signal)

    def stop(self):
        self.running = False
        if self.ser and self.ser.is_open:
            self.ser.close()
        self.wait()