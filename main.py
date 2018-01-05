"""
Sketch of the main program.
"""

import RPi.GPIO as GPIO
import time
from plotter.controls.plotters import MiniPlotter
from plotter.controls.plotters.motors import LED
from plotter.controls import Camera
from plotter.drawing import Sketch
from plotter.drawing import utils

# set up pin addresses
LED_PIN = 18
BUTTON_PIN = 23

class App(object):
    def __init__(self, debug=False):
        self.do_debug = debug

        GPIO.setmode(GPIO.BCM)
        GPIO.setup(BUTTON_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)

        self.led = LED(LED_PIN)
        self.camera = Camera()
        self.debug('initializing plotter...')
        self.led.slow()
        self.plotter = MiniPlotter()
        self.plotter.home()
        self.led.off()
        self.debug('  ...done')

    def debug(self, msg):
        if self.do_debug:
            print msg

    def run(self):
        # threaded callback is hopeless, this is robust
        GPIO.add_event_detect(BUTTON_PIN, GPIO.FALLING, bouncetime=200)
        while True:
            if GPIO.event_detected(BUTTON_PIN):
                self.go()
            time.sleep(.5)
            self.debug('.')

    def go(self):
        """
        Take a picture and plot it.
        """
        try:
            # acquire an image
            self.debug('capturing...')
            image = self.camera.get_image(dump='dump.jpg')
            image = utils.square(image)
            self.debug('  ...done')

            # calculate how to draw it
            self.led.fast()
            sketch = Sketch(image)
            self.debug('calculating...')
            #trajectory = sketch.amplitude_mod_scan(n_lines=50, pixels_per_period=4, gain=1.3, waveform='sawtooth')
            trajectory = sketch.contour_drawing()
            trajectory.dump('dump.npz')
            self.led.off()
            self.debug('  ...done')
            a = raw_input('plot? [Y/n]: ')

            # draw it
            if not 'n' in a.lower():
                self.debug('drawing...')
                self.led.slow()
                self.plotter.plot(trajectory)
                self.led.off()
                self.debug('...done')

        except KeyboardInterrupt:
            self.debug('...cancelled')
            self.led.off()
            return

    def __del__(self):
        self.debug('cleaning up GPIO')
        GPIO.cleanup()
        self.debug('closing camera')
        self.camera.close()

if __name__ == '__main__':
    app = App(debug=True)
    app.run()
