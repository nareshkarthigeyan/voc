import time
import math
import warnings
import busio, board
from adafruit_ads1x15.ads1115 import ADS1115
from adafruit_ads1x15.analog_in import AnalogIn
import adafruit_dht
import numpy as np

warnings.filterwarnings("ignore")

MAX_IO_ERRORS = 3
MIN_ACTIVE_SENSORS = 4
MIN_VARIANCE_THRESHOLD = 0.01


class VOCSensor:
    def __init__(self):

        # ---------- I2C ----------
        self.i2c = busio.I2C(board.SCL, board.SDA)

        # ---------- ADC Modules ----------
        self.ads1 = ADS1115(self.i2c, address=0x48)
        self.ads2 = ADS1115(self.i2c, address=0x49)
        self.ads3 = ADS1115(self.i2c, address=0x4B)

        # ---------- ADS1 ----------
        self.mq6_1      = AnalogIn(self.ads1, 0)
        self.mq135_1    = AnalogIn(self.ads1, 1)
        self.mq137_1    = AnalogIn(self.ads1, 2)
        self.mems_nh3_1 = AnalogIn(self.ads1, 3)

        # ---------- ADS2 ----------
        self.mems_ethanol_1 = AnalogIn(self.ads2, 0)
        self.mems_odor_1    = AnalogIn(self.ads2, 1)
        self.mq6_2          = AnalogIn(self.ads2, 2)
        self.mq135_2        = AnalogIn(self.ads2, 3)

        # ---------- ADS3 ----------
        self.mq137_2        = AnalogIn(self.ads3, 0)
        self.mems_nh3_2     = AnalogIn(self.ads3, 1)
        self.mems_ethanol_2 = AnalogIn(self.ads3, 2)
        self.mems_odor_2    = AnalogIn(self.ads3, 3)

        # ---------- Calibration ----------
        self.RL = 10000
        self.VC = 5.0

        self.RO = {
            "mq135": 3000,
            "mq137": 3500,
            "mq6": 5000
        }

        self.MEMS_MAX_PPM = {
            "nh3": 300,
            "ethanol": 500,
            "odor": 50
        }

        # ---------- DHT ----------
        self.dhtDevice = adafruit_dht.DHT11(board.D4, use_pulseio=False)


    def _safe_voltage(self, channel, retries=3):
        for _ in range(retries):
            try:
                return channel.voltage
            except (OSError, IOError):
                time.sleep(0.05)
        return None

    def calculate_rs(self, vout):
        if vout is None or vout <= 0.01:
            return None
        return ((self.VC - vout) / vout) * self.RL

    def get_ppm(self, rs_ro, sensor):
        if rs_ro is None:
            return None
        try:
            if sensor == "mq6":
                return 10 ** (-0.47 * math.log10(rs_ro) + 1.68)
            elif sensor == "mq135":
                return 10 ** (-0.42 * math.log10(rs_ro) + 2.3)
            elif sensor == "mq137":
                return 10 ** (-0.35 * math.log10(rs_ro) + 1.9)
        except Exception:
            return None
        return None

    def mems_to_ppm(self, voltage, gas):
        if voltage is None:
            return None
        max_ppm = self.MEMS_MAX_PPM.get(gas, 100)
        return round((voltage / 5.0) * max_ppm, 2)


    def _read_dht(self):
        for _ in range(3):
            try:
                t = self.dhtDevice.temperature
                h = self.dhtDevice.humidity
                if t is not None and h is not None:
                    return round(t, 2), round(h, 2)
            except RuntimeError:
                time.sleep(0.5)
        return 0.0, 0.0

    def _validate_signal(self, voc_readings):

        values = [v for v in voc_readings.values() if v is not None]

        if len(values) == 0:
            return False

        # How many sensors are producing meaningful signal?
        active_sensors = sum(1 for v in values if abs(v) > 0.5)

        variance = np.var(values)

        if active_sensors < MIN_ACTIVE_SENSORS:
            return False

        if variance < MIN_VARIANCE_THRESHOLD:
            return False

        return True


    def read_sensors(self):

        voc_readings = {}
        env_readings = {}

        try:
            # ---------- MQ ----------
            mq_list = [
                ("mq6_1", self.mq6_1, "mq6"),
                ("mq135_1", self.mq135_1, "mq135"),
                ("mq137_1", self.mq137_1, "mq137"),
                ("mq6_2", self.mq6_2, "mq6"),
                ("mq135_2", self.mq135_2, "mq135"),
                ("mq137_2", self.mq137_2, "mq137"),
            ]

            for label, chan, typ in mq_list:
                v = self._safe_voltage(chan)
                rs = self.calculate_rs(v)
                rs_ro = rs / self.RO[typ] if rs is not None else None
                ppm = self.get_ppm(rs_ro, typ)
                voc_readings[label] = ppm

            # ---------- MEMS ----------
            voc_readings["mems_nh3_1"]     = self.mems_to_ppm(self._safe_voltage(self.mems_nh3_1), "nh3")
            voc_readings["mems_ethanol_1"] = self.mems_to_ppm(self._safe_voltage(self.mems_ethanol_1), "ethanol")
            voc_readings["mems_odor_1"]    = self.mems_to_ppm(self._safe_voltage(self.mems_odor_1), "odor")

            voc_readings["mems_nh3_2"]     = self.mems_to_ppm(self._safe_voltage(self.mems_nh3_2), "nh3")
            voc_readings["mems_ethanol_2"] = self.mems_to_ppm(self._safe_voltage(self.mems_ethanol_2), "ethanol")
            voc_readings["mems_odor_2"]    = self.mems_to_ppm(self._safe_voltage(self.mems_odor_2), "odor")

            # ---------- Validate ----------
            if not self._validate_signal(voc_readings):
                return "ERROR", {}, {}

            # ---------- ENV ----------
            temp, hum = self._read_dht()
            env_readings["temperature"] = temp
            env_readings["humidity"] = hum

            return "OK", voc_readings, env_readings

        except Exception as e:
            print("[SENSOR ERROR]", e)
            return "ERROR", {}, {}
