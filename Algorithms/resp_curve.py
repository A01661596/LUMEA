import numpy as np
import pyqtgraph as pg
from PyQt5.QtWidgets import QWidget, QVBoxLayout
from PyQt5.QtCore import Qt
from scipy.signal import butter, filtfilt

class RespCurve(QWidget):
    def __init__(self, curve_color="#33DFEB"):
        super().__init__()
        self.curve_color = curve_color
        self.fs = 33  # Frecuencia de muestreo (Hz)
        self.buffer_size = self.fs * 15 
        self.data_buffer = []
        self.filtered_value = 0

        self.plot_widget = pg.PlotWidget()
        self.plot_widget.setBackground("black")
        self.plot_widget.setYRange(40, 60)  # Zoom vertical ajustado
        self.plot_widget.setMouseEnabled(x=False, y=False)
        self.plot_widget.hideAxis('left')
        self.plot_widget.hideAxis('bottom')
        self.plot_widget.setClipToView(True)
        self.plot_widget.setDownsampling(mode='peak')

        self.curve = self.plot_widget.plot(
            pen=pg.mkPen(self.curve_color, width=2, style=Qt.SolidLine)
        )

        layout = QVBoxLayout()
        layout.addWidget(self.plot_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)

    def apply_bandpass_filter(self, data, lowcut=0.1, highcut=0.5, order=3):
        nyq = 0.5 * self.fs
        low = lowcut / nyq
        high = highcut / nyq
        b, a = butter(order, [low, high], btype='band', analog=False)
        return filtfilt(b, a, data)

    def normalize_signal(self, signal, center=50, spread=8):
        signal = np.array(signal)
        min_val = np.min(signal)
        max_val = np.max(signal)
        if max_val - min_val == 0:
            return np.full_like(signal, center)
        normalized = (signal - min_val) / (max_val - min_val)
        return center + (normalized - 0.5) * spread * 2

    def update_plot(self, new_value):
        self.data_buffer.append(new_value)
        if len(self.data_buffer) > self.buffer_size:
            self.data_buffer.pop(0)

        if len(self.data_buffer) >= self.fs:
            filtered = self.apply_bandpass_filter(self.data_buffer)
            smoothed = self.normalize_signal(filtered)
            self.curve.setData(smoothed)

            # Valor suavizado de referencia
            window = 5
            if len(filtered) >= window:
                recent = filtered[-window:]
                self.filtered_value = sum(recent) / len(recent)
            else:
                self.filtered_value = filtered[-1]

    def get_filtered_value(self):
        return self.filtered_value

    def clear(self):
        self.data_buffer = []
        self.filtered_value = 0
        self.curve.clear()

    def set_curve_color(self, color):
        self.curve.setPen(pg.mkPen(color, width=2, style=Qt.SolidLine))