from .BaseStepper import BaseStepper
try:
    import RPi.GPIO as GPIO
except ImportError:
    from ..gadgets import DummyIO as GPIO
import time
import numpy as np

class A4983(BaseStepper):
    """
    Driver class for the Allegro A4983 stepper motor controller chip, as
    found for example in the Olimex BB-A4983 or Pololu drivers. It
    assumes the pull up/down configuration of the Olimex board, but
    probably works for the Pololu as well.
    """

    def __init__(self, pins, mspins=None, microstepping=1, 
                 per_step=360/400.0, soft_start=False):
        """
        Input:

        pins (list):         I/O pins connected to the A4983 (step,
                             direction, sleep) pins.
        mspins (list):       I/O pins connected to the A4983 microstep
                             configuration (MS1, MS2, MS3) pins.
                             Default: None
        microstepping (int): Number of microsteps per full step:
                             1, 2, 4, 8, 16.
                             Default: 1
        per_step (float):    Physical units (mm or degrees, perhaps) per
                             full motor step.
                             Default: 360/400.0
        soft_start (bool):   Start motions with 5x delay and accelerate
                             linearly over 200 steps.
                             Default: False
        """

        super(self.__class__, self).__init__()

        # map from the number of microsteps to ms1, ms2, ms3 pin values.
        self.MS_MAP = {
            1: [0, 0, 0],
            2: [1, 0, 0],
            4: [0, 1, 0],
            8: [1, 1, 0],
            16: [1, 1, 1]
        }

        # Parse input
        self.step_pin, self.dir_pin, self.sleep_pin = pins
        if mspins is not None:
            self.ms1_pin, self.ms2_pin, self.ms3_pin = mspins
        self.soft = soft_start
        self.ms = int(microstepping)
        self.per_step = float(per_step) / self.ms
        assert self.ms in self.MS_MAP.keys()
        if not self.ms == 1:
            assert mspins is not None

        # set up GPIO pins (some through properties)
        GPIO.setup(self.step_pin, GPIO.OUT, initial=GPIO.LOW)
        self.direction = 1
        self.sleeping = False
        if mspins is not None:
            GPIO.setup(self.ms1_pin, GPIO.OUT, initial=self.MS_MAP[self.ms][0])
            GPIO.setup(self.ms2_pin, GPIO.OUT, initial=self.MS_MAP[self.ms][1])
            GPIO.setup(self.ms3_pin, GPIO.OUT, initial=self.MS_MAP[self.ms][2])

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

    @property
    def sleeping(self):
        return self._sleeping

    @sleeping.setter
    def sleeping(self, val):
        self._sleeping = bool(val)
        if self._sleeping:
            GPIO.setup(self.sleep_pin, GPIO.OUT, initial=GPIO.LOW)
        else:
            GPIO.setup(self.sleep_pin, GPIO.OUT, initial=GPIO.HIGH)

    def _step(self):
        GPIO.output(self.step_pin, GPIO.HIGH)
        time.sleep(10e-6)
        GPIO.output(self.step_pin, GPIO.LOW)

    def _move(self, steps, delay=.002):
        """
        Blocking relative move in steps, hardware step direction.
        """
        N_ACC = 200
        X_ACC = 5

        self.running = True
        self.sleeping = False
        self._stopped = False
        reverse = False
        self.direction = 1
        if steps < 0:
            reverse = True
            steps = -steps
            self.direction = -1

        # acceleration?
        if self.soft:
            delays = np.linspace(delay * X_ACC, delay, N_ACC)
        else:
            delays = np.ones(N_ACC) * delay

        for i in range(steps):
            if self._stopped == True:
                self._stopped = False
                return
            if reverse:
                self.abs_steps -= 1
            else:
                self.abs_steps += 1

            self._step()
            time.sleep(delays[i] if i < N_ACC else delay)

        self.running = False

    def stop(self):
        self._stopped = True

    def off(self):
        self.sleeping = True

if __name__ == '__main__':
    import RPi.GPIO as GPIO
    GPIO.setmode(GPIO.BCM)
    motor = A4983(pins=[15, 18, 14], mspins=[2, 3, 4], microstepping=2, soft_start=False)
    try:
        motor.relmove(360, delay=2e-3)
        while motor.running:
            time.sleep(.5)
    except KeyboardInterrupt:
        motor.stop()
    #GPIO.cleanup()
