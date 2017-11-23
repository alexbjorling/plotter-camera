import RPi.GPIO as GPIO
import time

PINS = [6, 13, 19, 26]

SEQ = [
    [1, 0, 0, 0],
    [0, 0, 1, 0],
    [0, 1, 0, 0],
    [0, 0, 0, 1],
    ]

# set up pin addresses
GPIO.setmode(GPIO.BCM)

for pin in PINS:
    GPIO.setup(pin, GPIO.OUT, initial=GPIO.LOW)

try:
    for i in range(10000000):
        i_ = i % len(PINS)
        for j in range(len(PINS)):
            GPIO.output(PINS[j], SEQ[i][j])
        time.time(.050)
except KeyboardInterrupt:
    GPIO.cleanup()
GPIO.cleanup()
