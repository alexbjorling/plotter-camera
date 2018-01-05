import RPi.GPIO as GPIO

class LED(object):
    def __init__(self, pin):
        GPIO.setup(pin, GPIO.OUT)
        self.p = GPIO.PWM(18, 1.0)

    def fast(self):
        self.p.ChangeFrequency(4.)
        self.p.start(20.0)

    def slow(self):
        self.p.ChangeFrequency(.6)      
        self.p.start(50.0)

    def on(self):
        self.p.start(100.0)

    def off(self):
        self.p.stop()

if __name__ == '__main__':
    GPIO.setmode(GPIO.BCM)
    led = LED(18)

    import time
    led.slow(); time.sleep(3)
    led.fast(); time.sleep(3)
    led.on(); time.sleep(3)
    led.off()
