from .BaseStepper import BaseStepper
try:
    import RPi.GPIO as GPIO
except ImportError:
    from ..gadgets import DummyIO as GPIO
import time
import numpy as np

class TMC2130(BaseStepper):
    """
    Driver class for the Trinamic TMC2130 stepper driver. Very basic
    functionality for now.
    """

    def __init__(self, pins, microstepping=16, per_step=360/400.0):
        """
        Input:

        pins (list):         I/O pins connected to the A4983 (step,
                             direction) pins.
        microstepping (int): Number of microsteps per full step:
                             For now, only 16 is possible.
                             Default: 16
        per_step (float):    Physical units (mm or degrees, perhaps) per
                             full motor step.
                             Default: 360/400.0
        """

        super(self.__class__, self).__init__()

        # Parse input
        self.step_pin, self.dir_pin = pins
        self.ms = int(microstepping)
        self.per_step = float(per_step) / self.ms

        # set up GPIO pins (some through properties)
        GPIO.setup(self.step_pin, GPIO.OUT, initial=GPIO.LOW)
        self.direction = 1

        # absolute step position for keeping track of the position. set externally.
        self.abs_steps = 0

        # an internal stop signal
        self._stopped = False

    @property
    def direction(self):
        return self._direction

    @direction.setter
    def direction(self, val):
        self._direction = val
        if val == 1:
            GPIO.setup(self.dir_pin, GPIO.OUT, initial=GPIO.LOW)
        elif val == -1:
            GPIO.setup(self.dir_pin, GPIO.OUT, initial=GPIO.HIGH)
        else:
            raise Exception()

    def step(self, dir):
        """
        Bare minimum single-step method.
        """
        if dir == 1:
            self.abs_steps += 1
            self.direction = 1
            self._step()
        elif dir == -1:
            self.abs_steps -= 1
            self.direction = -1
            self._step()

    @property
    def position(self):
        return self.abs_steps * self.per_step

    @position.setter
    def position(self, val):
        self.abs_steps = val / self.per_step

    def _step(self):
        GPIO.output(self.step_pin, GPIO.HIGH)
        time.sleep(1e-6) # hard to get from the datasheet...
        GPIO.output(self.step_pin, GPIO.LOW)

    def _move(self, steps, delay=.002):
        """
        Blocking relative move in steps, hardware step direction.
        """

        self.running = True
        self._stopped = False
        reverse = False
        self.direction = 1
        if steps < 0:
            reverse = True
            steps = -steps
            self.direction = -1

        for i in range(steps):
            if self._stopped == True:
                self._stopped = False
                return
            if reverse:
                self.abs_steps -= 1
            else:
                self.abs_steps += 1

            self._step()
            time.sleep(delay)

        self.running = False

    def stop(self):
        self._stopped = True

if __name__ == '__main__':
    import RPi.GPIO as GPIO
    GPIO.setmode(GPIO.BCM)
    motor = TMC2130(pins=[13, 6], microstepping=16)
    try:
        motor.relmove(360, delay=1e-3)
        while motor.running:
            time.sleep(.5)
    except KeyboardInterrupt:
        motor.stop()
    #GPIO.cleanup()
