# Código adaptado de Ravivarman Rajendiran

# -*- coding:utf-8 -*-

from time import sleep
import time
import RPi.GPIO as GPIO
import smbus

# Direcciones de registro
REG_INTR_STATUS_1 = 0x00
REG_INTR_STATUS_2 = 0x01
REG_FIFO_DATA = 0x07
REG_MODE_CONFIG = 0x09
REG_TEMP_INTR = 0x1F
REG_TEMP_FRAC = 0x20

class MAX30102:
    def __init__(self, channel=1, address=0x57, gpio_pin=7):
        """
        Inicializa el sensor MAX30102.
        """
        print(f"Channel: {channel}, address: 0x{address:x}")
        self.address = address
        self.channel = channel
        self.bus = smbus.SMBus(self.channel)
        self.interrupt = gpio_pin

        # Configura el modo GPIO
        GPIO.setmode(GPIO.BOARD)
        GPIO.setup(self.interrupt, GPIO.IN)

        print("→ Haciendo reset")
        self.reset()

        print("→ Sleep 1 segundo")
        sleep(1)

        print("→ Leyendo registro de interrupciones")
        try:
            self.bus.read_i2c_block_data(self.address, REG_INTR_STATUS_1, 1)
        except Exception as e:
            print("⚠️ Error al leer interrupción:", e)

        print("→ Ejecutando setup()")
        self.setup()

        print("→ Sensor inicializado completamente")

    def shutdown(self):
        """
        Apaga el dispositivo.
        """
        self.bus.write_i2c_block_data(self.address, REG_MODE_CONFIG, [0x80])

    def reset(self):
        """
        Resetea el dispositivo, lo que borra todos los ajustes.
        """
        self.bus.write_i2c_block_data(self.address, REG_MODE_CONFIG, [0x40])

    def setup(self, led_mode=0x03):
        """
        Configura el dispositivo manualmente (modo SpO2, LEDs a 36.4mA, etc.)
        """
        self.bus.write_byte_data(self.address, 0x09, 0x03)  # Modo SpO2
        self.bus.write_byte_data(self.address, 0x0A, 0x27)  # SPO2 config: 100Hz, 411us, 18-bit ADC
        self.bus.write_byte_data(self.address, 0x0C, 0x24)  # LED1 (Rojo): 36.4mA
        self.bus.write_byte_data(self.address, 0x0D, 0x24)  # LED2 (IR): 36.4mA
        self.bus.write_byte_data(self.address, 0x08, 0x0F)  # FIFO config
        self.bus.write_byte_data(self.address, 0x04, 0x00)  # FIFO_WR_PTR
        self.bus.write_byte_data(self.address, 0x05, 0x00)  # FIFO_OVF
        self.bus.write_byte_data(self.address, 0x06, 0x00)  # FIFO_RD_PTR

    def set_config(self, reg, value):
        """
        Cambia la configuración de un registro.
        """
        self.bus.write_i2c_block_data(self.address, reg, value)

    def read_fifo(self):
        """
        Lee los datos de los registros FIFO.
        """
        self.bus.read_i2c_block_data(self.address, REG_INTR_STATUS_1, 1)
        self.bus.read_i2c_block_data(self.address, REG_INTR_STATUS_2, 1)

        data = self.bus.read_i2c_block_data(self.address, 0x07, 6)
        red_led = (data[0] << 16 | data[1] << 8 | data[2]) & 0x03FFFF
        ir_led = (data[3] << 16 | data[4] << 8 | data[5]) & 0x03FFFF

        return red_led, ir_led

    def read_sequential(self, amount=100):
        """
        Lee `amount` de muestras de los LEDs rojo e infrarrojo de manera secuencial.
        Sin bloqueo por interrupción.
        """
        red_buf = []
        ir_buf = []
        for _ in range(amount):
            red, ir = self.read_fifo()
            red_buf.append(red)
            ir_buf.append(ir)
            time.sleep(0.002)  # pequeño delay para simular muestreo real

        return red_buf, ir_buf


