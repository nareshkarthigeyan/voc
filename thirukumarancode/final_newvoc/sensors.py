import time
import math
import busio, board
from adafruit_ads1x15.ads1115 import ADS1115
from adafruit_ads1x15.analog_in import AnalogIn
import adafruit_dht
from gpiozero import DigitalInputDevice, DigitalOutputDevice, LED

# ==== GPIO Pin Mapping ====
IR_PIN = 17        # IR sensor
FAN_PIN = 16       # Fan control (active LOW relay)
LED1_PIN = 1       # LED 1
LED2_PIN = 12      # LED 2
DHT_PIN = board.D4 # DHT11 data pin (GPIO4)

# ==== GPIO Setup ====
ir_sensor = DigitalInputDevice(IR_PIN, pull_up=False)  # IR sensor
fan = DigitalOutputDevice(FAN_PIN, active_high=False, initial_value=True)  # relay
led1 = LED(LED1_PIN)
led2 = LED(LED2_PIN)

# ==== VOC Sensor Class ====
class VOCSensor:
    def __init__(self):
        # I2C bus
        i2c = busio.I2C(board.SCL, board.SDA)

        # ADS1115 modules
        self.ads1 = ADS1115(i2c, address=0x48)
        self.ads2 = ADS1115(i2c, address=0x49)
        self.ads3 = ADS1115(i2c, address=0x4A)

        # ---- ADS1 ----
        self.mq6_1      = AnalogIn(self.ads1, 0)
        self.mq135_1    = AnalogIn(self.ads1, 1)
        self.mq137_1    = AnalogIn(self.ads1, 2)
        self.mems_nh3_1 = AnalogIn(self.ads1, 3)
        # ---- ADS2 ----
        self.mems_ethanol_1 = AnalogIn(self.ads2, 0)
        self.mems_odor_1    = AnalogIn(self.ads2, 1)
        self.mq6_2          = AnalogIn(self.ads2, 2)
        self.mq135_2        = AnalogIn(self.ads2, 3)
        # ---- ADS3 ----
        self.mq137_2        = AnalogIn(self.ads3, 0)
        self.mems_nh3_2     = AnalogIn(self.ads3, 1)
        self.mems_ethanol_2 = AnalogIn(self.ads3, 2)
        self.mems_odor_2    = AnalogIn(self.ads3, 3)

        # Calibration constants
        self.RL = 10000
        self.VC = 5.0
        self.RO = {"mq135": 3000, "mq137": 3500, "mq6": 5000}

        # MEMS scaling ranges (ppm)
        self.MEMS_MAX_PPM = {"nh3": 300, "ethanol": 500, "odor": 50}

        # DHT11
        self.dhtDevice = adafruit_dht.DHT11(DHT_PIN)

    # ====== Helper functions ======
    def calculate_rs(self, vout):
        return ((self.VC - vout) / vout) * self.RL if vout > 0.01 else 99999

    def get_ppm(self, rs_ro, sensor):
        try:
            if sensor == "mq6":
                return 10 ** (-0.47 * math.log10(rs_ro) + 1.68)
            elif sensor == "mq135":
                return 10 ** (-0.42 * math.log10(rs_ro) + 2.3)
            elif sensor == "mq137":
                return 10 ** (-0.35 * math.log10(rs_ro) + 1.9)
        except Exception:
            return 0
        return rs_ro

    def mems_to_ppm(self, voltage, gas):
        max_ppm = self.MEMS_MAX_PPM.get(gas, 100)
        return round((voltage / 5.0) * max_ppm, 2)

    def _read_dht(self):
        """Read DHT values (retry if fails)."""
        try:
            temperature = self.dhtDevice.temperature
            humidity = self.dhtDevice.humidity
            if temperature is not None and humidity is not None:
                return round(temperature, 1), round(humidity, 1)
        except RuntimeError as e:
            print("DHT error:", e.args[0])
        return 0, 0

    # ====== Public API ======
    def read_sensors(self):
        readings = {}

        # MQ Sensors
        mq_list = [
            ("mq6_1", self.mq6_1, "mq6"),
            ("mq135_1", self.mq135_1, "mq135"),
            ("mq137_1", self.mq137_1, "mq137"),
            ("mq6_2", self.mq6_2, "mq6"),
            ("mq135_2", self.mq135_2, "mq135"),
            ("mq137_2", self.mq137_2, "mq137"),
        ]
        for label, chan, typ in mq_list:
            try:
                v = chan.voltage
                rs = self.calculate_rs(v)
                rs_ro = rs / self.RO[typ]
                readings[label] = round(self.get_ppm(rs_ro, typ), 2)
            except Exception:
                readings[label] = 0
            time.sleep(0.05)  # 50 ms delay per MQ sensor

        # MEMS Sensors
        mems_list = [
            ("mems_nh3_1", self.mems_nh3_1, "nh3"),
            ("mems_ethanol_1", self.mems_ethanol_1, "ethanol"),
            ("mems_odor_1", self.mems_odor_1, "odor"),
            ("mems_nh3_2", self.mems_nh3_2, "nh3"),
            ("mems_ethanol_2", self.mems_ethanol_2, "ethanol"),
            ("mems_odor_2", self.mems_odor_2, "odor"),
        ]
        for label, chan, gas in mems_list:
            try:
                readings[label] = self.mems_to_ppm(chan.voltage, gas)
            except Exception:
                readings[label] = 0
            time.sleep(0.02)  # 20 ms delay per MEMS sensor

        # DHT Sensor
        temp, hum = self._read_dht()
        readings["dht_temp"] = temp
        readings["dht_hum"] = hum
        time.sleep(0.2)  # 200 ms delay for DHT11

        return readings

# ==== Main loop ====
def main():
    system = VOCSensor()
    last_hand_state = None

    try:
        while True:
            data = system.read_sensors()
            hand_detected = not ir_sensor.is_active  # LOW = hand detected

            if hand_detected != last_hand_state:
                if hand_detected:
                    fan.off()
                    led1.on()
                    led2.on()
                    print(f"🤚 Hand detected! Fan ON, LEDs ON. IR raw: {ir_sensor.value}")
                    print("Sensor Data (raw ppm/volts):", data)
                else:
                    fan.on()
                    led1.off()
                    led2.off()
                    print(f"💨 No hand. Fan OFF, LEDs OFF. IR raw: {ir_sensor.value}")
                    print("Sensor Data (raw ppm/volts):", data)

                last_hand_state = hand_detected

            time.sleep(2)  # main loop delay

    except KeyboardInterrupt:
        fan.off()
        led1.off()
        led2.off()
        print("Exiting safely.")

if __name__ == "__main__":
    main()
