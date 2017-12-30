"""
Sketch of the main program.
"""

import RPi.GPIO as GPIO
import time
from plotter.controls.plotters import MiniPlotter
from plotter.controls import Camera
from plotter.drawing import Sketch
from plotter.drawing import utils

# set up pin addresses
BUTTON_PIN = 23
GPIO.setmode(GPIO.BCM)

def go_callback(par):
    """
    This is where the functionality is.
    """
    print "capturing..."
    # disable more callbacks
    GPIO.remove_event_detect(BUTTON_PIN)

    # acquire an image
    image = camera.get_image(dump=None)
    image = utils.square(image)

    # calculate how to draw it
    sketch = Sketch(image)
    print 'calculating...'
    trajectory = sketch.frequencyModScan(nLines=30, pixelsPerTypicalPeriod=2.1, waveform='sawtooth')
    trajectory.dump('dump.npz')
    a = raw_input('plot? [Y/n]')

    # draw it
    if not 'n' in a.lower():
        print 'drawing...'
        plotter.plot(trajectory)
        print '...done'

    # restore everything
    activate_go_button()

def activate_go_button():
    """
    Activate background edge detection on the button.
    """
    GPIO.add_event_detect(BUTTON_PIN, GPIO.FALLING, callback=go_callback, bouncetime=200)

if __name__ == '__main__':
    # set up pins
    GPIO.setup(BUTTON_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    activate_go_button()

    # make a camera instance
    camera = Camera()

    # make a plotter instance
    plotter = MiniPlotter()

    # main loop: doesn't have to run very fast
    try:
        while True:
            time.sleep(1)
    except:
        GPIO.cleanup()
        camera.close()
        raise

    GPIO.cleanup()
    camera.close()
