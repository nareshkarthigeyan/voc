from gpiozero import DigitalInputDevice, DigitalOutputDevice, LED
import time

IR_PIN = 17
FAN_PIN = 16
LED1_PIN = 1
LED2_PIN = 12

class HandController:
    def __init__(self):
        self.ir = DigitalInputDevice(IR_PIN, pull_up=False)
        self.fan = DigitalOutputDevice(FAN_PIN, active_high=False, initial_value=True)
        self.led1 = LED(LED1_PIN)
        self.led2 = LED(LED2_PIN)

    def hand_present(self):
        # IR LOW = hand detected
        return not self.ir.is_active

    def start_sampling(self):
        self.fan.off()
        self.led1.on()
        self.led2.on()

    def stop_sampling(self):
        self.fan.on()
        self.led1.off()
        self.led2.off()
