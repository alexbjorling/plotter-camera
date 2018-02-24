import RPi.GPIO as GPIO
import time
import threading
import numpy as np

class A4983(object):
    """
    Driver class for the Allegro A4983 stepper motor controller chip, as
    found for example in the Olimex BB-A4983 or Pololu drivers. It
    assumes the pull up/down configuration of the Olimex board, but
    probably works for the Pololu as well.

    The basic step/direction functionality also works for the Trinamic
    TMC2130 driver.
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

        # map from the number of microsteps to ms1, ms2, ms3 pin values.
        self.MS_MAP = {
            1: [0, 0, 0],
            2: [1, 0, 0],
            4: [0, 1, 0],
            8: [1, 1, 0],
            16: [1, 1, 1]
        }

        # Parse input
        self.per_step = float(per_step)
        self.step_pin, self.dir_pin, self.sleep_pin = pins
        if mspins is not None:
            self.ms1_pin, self.ms2_pin, self.ms3_pin = mspins
        self.soft = soft_start
        self.ms = int(microstepping)
        assert self.ms in self.MS_MAP.keys()
        if not self.ms == 1:
            assert mspins is not None

        # set up GPIO pins
        GPIO.setup(self.step_pin, GPIO.OUT, initial=GPIO.LOW)
        GPIO.setup(self.dir_pin, GPIO.OUT, initial=GPIO.LOW)
        self.sleeping = False
        if mspins is not None:
            GPIO.setup(self.ms1_pin, GPIO.OUT, initial=self.MS_MAP[self.ms][0])
            GPIO.setup(self.ms2_pin, GPIO.OUT, initial=self.MS_MAP[self.ms][1])
            GPIO.setup(self.ms3_pin, GPIO.OUT, initial=self.MS_MAP[self.ms][2])

        # absolute step position for keeping track of the position. set externally.
        self.abs_steps = 0

        # an internal stop signal
        self._stopped = False

        self.running = False

    @property
    def position(self):
        return self.abs_steps * self.per_step / self.ms

    @position.setter
    def position(self, val):
        self.abs_steps = val / self.per_step * self.ms

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

    def absmove(self, position, delay=.003):
        """
        Non-blocking absolute move in millimeters.
        """
        distance = position - self.position
        self.relmove(distance, delay=delay)

    def relmove(self, distance, delay=.003):
        """
        Non-blocking relative move in millimeters.
        """
        self.running = True
        steps = int(round(distance / self.per_step * self.ms))
        t = threading.Thread(target=self._move, kwargs={'steps': steps, 'delay': delay})
        t.start()

    def _step(self):
        GPIO.output(self.step_pin, GPIO.HIGH)
        GPIO.output(self.step_pin, GPIO.LOW)

    def _move(self, steps, delay=.002):
        """
        Blocking relative move in steps.

        """
        N_ACC = 200
        X_ACC = 5

        self.sleeping = False
        self._stopped = False
        reverse = False
        GPIO.output(self.dir_pin, GPIO.LOW)
        if steps < 0:
            reverse = True
            steps = -steps
            GPIO.output(self.dir_pin, GPIO.HIGH)

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
    motor = A4983(pins=[15, 18, 14], mspins=[2, 3, 4], microstepping=8, soft_start=True)
    try:
        motor.relmove(2*360, delay=1e-3)
        while motor.running:
            time.sleep(.5)
    except KeyboardInterrupt:
        motor.stop()
    #GPIO.cleanup()
