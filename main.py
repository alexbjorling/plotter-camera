"""
Sketch of the main program.
"""

import RPi.GPIO as GPIO
import time
#import controls
#import drawing

# set up pin addresses
BUTTON_PIN = 17
BUZZER_PIN = 18
GPIO.setmode(GPIO.BCM)

class Worker(object):
    """
    Emulates the work being done by classes like Sketch, Plotter, etc.
    """
    def __init__(self):
        self.n = 0
        self.cancelled = False

    def work(self):
        print "worker working..."
        for i in range(500):
            if self.cancelled:
                self.cancelled = False
                print "worker cancelled!"
                break
            self.n += 1
            time.sleep(.005)
        print 'worker worked, n = %d' % self.n

    def cancel(self):
        self.cancelled = True

def go_callback(par):
    """
    This is where the action is:

    # acquire an image
    camera = controls.Camera()
    image = camera.get_image()

    # calculate how to draw it
    sketch = drawing.Sketch(image)
    trajectory = sketch.contourDrawing()

    # draw it
    plotter = controls.Plotter()
    plotter.plot(trajectory)
    """
    print "go callback called"
    GPIO.remove_event_detect(BUTTON_PIN)
    worker.work()
    activate_go_button()

def activate_go_button():
    """
    Activate background edge detection on the button.
    """
    GPIO.add_event_detect(BUTTON_PIN, GPIO.FALLING, callback=go_callback, bouncetime=200)

# set up pins
GPIO.setup(BUZZER_PIN, GPIO.OUT, initial=GPIO.LOW)
GPIO.setup(BUTTON_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
activate_go_button()

# main loop: doesn't have to run very fast
try:
    worker = Worker()
    while True:
        print "main loop running %s" % time.time()
        time.sleep(1)
except:
    GPIO.cleanup()
    raise

GPIO.cleanup()
