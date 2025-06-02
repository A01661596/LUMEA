from PyQt5.QtCore import QThread, pyqtSignal
import time
from max30102 import MAX30102

class PlethThread(QThread):
    new_ir = pyqtSignal(int)
    new_red = pyqtSignal(int)
    new_ir_red = pyqtSignal(int, int)  # ← para usar en SpO2

    def __init__(self, parent=None):
        super().__init__(parent)
        try:
            self.sensor = MAX30102()
            self.ready = True
        except Exception as e:
            print("❌ MAX30102 error:", e)
            self.ready = False
        self.running = False

    def run(self):
        if not self.ready:
            return
        self.running = True
        while self.running:
            try:
                red, ir = self.sensor.read_fifo()
                self.new_ir.emit(ir)
                self.new_red.emit(red)
                self.new_ir_red.emit(ir, red)
            except Exception as e:
                print("⚠️ Lectura fallida:", e)
            time.sleep(0.03)  # ~33 Hz

    def stop(self):
        self.running = False
        self.wait()


