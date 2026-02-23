from gpiozero import DigitalOutputDevice
import time

# Use BCM numbering
FAN_PIN = 24   # Change if needed

class FanController:

    def __init__(self):
        # active_high=False → because your relay is active LOW
        # initial_value=True → keep relay OFF at startup
        self.fan = DigitalOutputDevice(
            FAN_PIN,
            active_high=False,
            initial_value=False
        )

    def turn_on(self):
        print("Fan ON")
        self.fan.on()   # This will pull GPIO LOW

    def turn_off(self):
        print("Fan OFF")
        self.fan.off()  # This will pull GPIO HIGH

    def flush(self, duration=25):
        """
        Turn fan ON for 'duration' seconds
        then turn it OFF.
        """
        self.turn_on()
        time.sleep(duration)
        self.turn_off()
'''      
if __name__=="__main__":
    fan = FanController()
    fan.flush(25)
'''
