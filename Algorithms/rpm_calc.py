import numpy as np
import time
from scipy.signal import welch

class RPMCalculator:
    def __init__(self, sampling_rate=33):
        self.sampling_rate = sampling_rate
        self.signal_window = []
        self.rpm = "---"
        self.rpm_history = []
        self.buffer_duration = 25  # segundos
        self.last_display_time = time.time()
        self.last_displayed_rpm = None
        self.rpm_raw = None
        self.ema_alpha = 0.1  # ✅ control del suavizado (0.1 más lento, 0.5 más reactivo)

    def update(self, value):
        self.signal_window.append(value)

        max_len = int(self.sampling_rate * self.buffer_duration)
        if len(self.signal_window) > max_len:
            self.signal_window = self.signal_window[-max_len:]

        if len(self.signal_window) < self.sampling_rate * 10:
            return self.rpm

        if time.time() - self.last_display_time >= 1.5:
            self.last_display_time = time.time()
            return self.calculate_rpm()
        else:
            return self.rpm

    def calculate_rpm(self):
        signal = np.array(self.signal_window)
        signal -= np.mean(signal)

        freqs, psd = welch(signal, fs=self.sampling_rate, nperseg=min(len(signal), 512))
        mask = (freqs >= 0.1) & (freqs <= 0.5)
        if not np.any(mask):
            return self.rpm

        peak_freq = freqs[mask][np.argmax(psd[mask])]
        rpm_estimate = int(peak_freq * 60)
        self.rpm_raw = rpm_estimate

        self.rpm_history.append(rpm_estimate)
        if len(self.rpm_history) > 7:
            self.rpm_history = self.rpm_history[-7:]

        averaged_rpm = int(np.mean(self.rpm_history))

        # ✅ Aplicar suavizado EWMA siempre
        if self.last_displayed_rpm is None:
            self.last_displayed_rpm = averaged_rpm
        else:
            self.last_displayed_rpm = (
                self.ema_alpha * averaged_rpm +
                (1 - self.ema_alpha) * self.last_displayed_rpm
            )

        self.rpm = int(round(self.last_displayed_rpm))
        return self.rpm

    def get_rpm(self):
        return self.rpm

    def clear(self):
        self.signal_window = []
        self.rpm_history = []
        self.rpm = "---"
        self.last_display_time = time.time()
        self.last_displayed_rpm = None
        self.rpm_raw = None
