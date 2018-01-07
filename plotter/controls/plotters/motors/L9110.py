import RPi.GPIO as GPIO
import time
import threading

class L9110(object):
    """
    Driver class for the L9110 stepper motor controller.
    """

    def __init__(self, pins, twophase=False, halfstep=False, power_saving=True):
        """
        Input:

        pins (list):         I/O pins connected to the [B-1A, B-1B, A-1A, A-1B]
                             inputs on the L9110s stepper driver.
        twophase (bool):     Whether to run in two-phase mode full step mode.
        halfstep (bool):     Whether to use eight steps per revolution.
        power_saving (bool): Power down motor between movements.
        """

        self.MM_PER_STEP = .025

        self.pins = pins

        if twophase:
            self.SEQ = [
                [0, 1, 1, 0],
                [0, 1, 0, 1],
                [1, 0, 0, 1],
                [1, 0, 1, 0],
                ]
        elif halfstep:
            self.MM_PER_STEP *= .5
            self.SEQ = [
                [0, 1, 0, 1],
                [0, 0, 0, 1],
                [1, 0, 0, 1],
                [1, 0, 0, 0],
                [1, 0, 1, 0],
                [0, 0, 1, 0],
                [0, 1, 1, 0],
                [0, 1, 0, 0],
                ]
        else:
            self.SEQ = [
                [1, 0, 0, 0],
                [0, 0, 1, 0],
                [0, 1, 0, 0],
                [0, 0, 0, 1],
                ]

        self.power_saving = power_saving

        for pin in self.pins:
            GPIO.setup(pin, GPIO.OUT, initial=GPIO.LOW)

        # global counter of steps taken, to keep consecutive movements smooth
        self.rel_steps = 0

        # absolute step position for keeping track of the position. set externally.
        self.abs_steps = 0

        # an internal stop signal
        self._stopped = False

        self.running = False

    @property
    def position(self):
        return self.abs_steps * self.MM_PER_STEP

    @position.setter
    def position(self, val):
        self.abs_steps = val / self.MM_PER_STEP

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
        steps = int(round(distance / self.MM_PER_STEP))
        t = threading.Thread(target=self._move, kwargs={'steps': steps, 'delay': delay})
        t.start()

    def _current_seq(self):
            i_ = self.rel_steps % len(self.SEQ)
            return self.SEQ[i_]

    def _output_seq(self, seq):
            for j in range(len(self.pins)):
                GPIO.output(self.pins[j], seq[j])

    def _move(self, steps, delay=.002):
        """
        Blocking relative move in steps.
        """
        self._stopped = False
        reverse = False
        if steps < 0:
            reverse = True
            steps = -steps

        if self.power_saving:
            self._output_seq(self._current_seq())

        for i in range(steps):
            if self._stopped == True:
                self._stopped = False
                return
            if reverse:
                self.rel_steps -= 1
                self.abs_steps -= 1
            else:
                self.rel_steps += 1
                self.abs_steps += 1
            i_ = self.rel_steps % len(self.SEQ)

            self._output_seq(self._current_seq())
            time.sleep(delay)

        if self.power_saving:
            self._output_seq([(GPIO.LOW),] * len(self.SEQ))

        self.running = False

    def stop(self):
        self._stopped = True

    def off(self):
        for j in range(len(self.pins)):
            GPIO.output(self.pins[j], GPIO.LOW)
