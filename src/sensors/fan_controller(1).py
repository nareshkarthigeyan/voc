
from gpiozero import DigitalOutputDevice, DigitalInputDevice
import time

FAN_PIN = 24        
#IR_PIN = 17         


fan = DigitalOutputDevice(FAN_PIN, active_high=False, initial_value=True)
#ir_sensor = DigitalInputDevice(IR_PIN, pull_up=True)

#fan = OutputDevice(FAN_PIN, active_high=True, initial_value=False)
#ir_sensor = InputDevice(IR_PIN)

print("System Ready...")

try:
    while True:
        print("Hand Detected → Fan ON")
        print(fan)
        print("No Hand → Fan OFF")
        print(fan)
        time.sleep(0.2)

except KeyboardInterrupt:
    print("Exiting...")
    fan.off()


##import RPI.GPIO as GPIO
##import time
##
##GPIO.setmode(GPIO.BCM)
##GPIO.setup(16, GPIO.OUT)
##print("LOW")
##GPIO.output(16, GPIO.LOW)
##time.sleep(5)
##print("HIGH")
##GPIO.output(16, GPIO.HIGH)
##time.sleep(5)

'''
import lgpio
import time

FAN_PIN = 24        
IR_PIN = 17         


h = lgpio.gpiochip_open(0)
lgpio.gpio_claim_output(h, FAN_PIN)
lgpio.gpio_claim_input(h, IR_PIN)
#ir_sensor = DigitalInputDevice(IR_PIN, pull_up=True)

#fan = OutputDevice(FAN_PIN, active_high=True, initial_value=False)
#ir_sensor = InputDevice(IR_PIN)
print("System Ready...")

try:
    while True:
        ir_value = lgpio.gpio_read(h, IR_PIN)
        print(f"IR Value:{ir_value}")
        if ir_value==0: 
            print("Hand Detected → Fan ON")
            lgpio.gpio_write(h, FAN_PIN, 0)
        else:
            print("No Hand → Fan OFF")
            lgpio.gpio_write(h, FAN_PIN, 1)

        time.sleep(0.2)

except KeyboardInterrupt:
    print("Exiting...")
    lgpio.gpiochip_close(h, FAN_PIN, 0)
    lgpio.gpiochip_close(h)
'''
