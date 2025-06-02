import numpy as np
import time
import math

class SpO2Calculator:
    def __init__(self, window_size=100):
        self.ir_values = []
        self.red_values = []
        self.window_size = window_size
        self.last_spo2 = "---"
        self.last_time = time.time()
        self.spo2_buffer = []  # buffer para suavizado

    def update(self, ir_val, red_val):
        self.ir_values.append(ir_val)
        self.red_values.append(red_val)

        if len(self.ir_values) > self.window_size:
            self.ir_values.pop(0)
            self.red_values.pop(0)

        if len(self.ir_values) < 20:
            return "---"

        spo2 = self._calculate_spo2()

        if spo2 == "---" or math.isnan(spo2):
            self.last_spo2 = "---"
            self.spo2_buffer.clear()
            return "---"

        # Agregar al buffer y limitar tamaño
        self.spo2_buffer.append(spo2)
        if len(self.spo2_buffer) > 5:
            self.spo2_buffer.pop(0)

        # Calcular promedio suavizado
        spo2_avg = sum(self.spo2_buffer) / len(self.spo2_buffer)

        now = time.time()
        if spo2_avg > 90:
            if now - self.last_time >= 1.5:
                self.last_time = now
                self.last_spo2 = f"{int(spo2_avg)} %"
        else:
            # Si está bajo, mostrar inmediatamente
            self.last_spo2 = f"{int(spo2_avg)} %"
            self.last_time = now

        return self.last_spo2

    def _calculate_spo2(self):
        ir_ac = np.std(self.ir_values)
        red_ac = np.std(self.red_values)
        ir_dc = np.mean(self.ir_values)
        red_dc = np.mean(self.red_values)

        if ir_dc == 0 or red_dc == 0:
            return "---"

        ratio = (red_ac / red_dc) / (ir_ac / ir_dc)
        spo2 = 110 - 25 * ratio  # fórmula empírica

        if spo2 < 0 or spo2 > 100:
            return "---"

        return spo2
