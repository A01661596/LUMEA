from PyQt5.QtWidgets import QWidget, QVBoxLayout, QSizePolicy
import pyqtgraph as pg
import numpy as np
from scipy.signal import medfilt

class PlethCurve(QWidget):
    def __init__(self, parent=None, curve_color="#AEF7BD"):
        super().__init__(parent)
        self.ir_values = [0] * 150
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)

        self.plot_widget = pg.PlotWidget(background='k')
        self.plot_widget.setMouseEnabled(False, False)
        self.plot_widget.hideAxis('bottom')
        self.plot_widget.hideAxis('left')
        self.plot_widget.setYRange(40, 60)

        self.curve = self.plot_widget.plot(
            pen=pg.mkPen(color=curve_color, width=2, cosmetic=True)
        )

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.plot_widget)

    def update_plot(self, new_ir):
        self.ir_values.append(new_ir)
        if len(self.ir_values) > 150:
            self.ir_values.pop(0)

        data = np.array(self.ir_values)
        data = -data
        data = medfilt(data, kernel_size=3)

        if np.max(data) - np.min(data) < 5:
            centered = np.array([50] * len(data))
        else:
            centered = self.normalize_signal(data, center=50, spread=8)

        x = np.arange(len(centered))
        if len(x) > 1 and len(centered) > 1 and len(x) == len(centered):
            self.curve.setData(x, centered)

    def clear(self):
        self.ir_values = [0] * 150
        self.curve.setData(self.ir_values)

    @staticmethod
    def normalize_signal(values, center=50, spread=10):
        min_val = min(values)
        max_val = max(values)
        if max_val == min_val:
            return [center for _ in values]
        return [
            ((v - min_val) / (max_val - min_val)) * (2 * spread) + (center - spread)
            for v in values
        ]
