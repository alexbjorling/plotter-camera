"""
Servo module using hardware PWM through pigpio. 

The pigpiod daemon must be running in the background for these classes.

This also requires one of the hardware PWM0/PWM1 channels to first be
configured on one of the IO pins. The following worked to get PWM1
exposed on pin 19, in /boot/config.txt. You can also set up both
channels with a different dtoverlay.

dtoverlay=pwm,pin=19
"""

import pigpio
import time
import numpy as np

class Servo(object):

    def __init__(self, pin=19, low=2.75, high=12.5, posrange=180, frequency=50):
        """
        low, high:  duty cycles limit in percent
        range:      range in some meaningful units, the motor will run
                    from 0 to +posrange
        frequency:  PWM frequency in Hz
        pin:        GPIO pin where the PWM channel is exposed
        """
        self._low = float(low)
        self._high = float(high)
        self._range = float(posrange)
        self._freq = frequency
        self._pin = pin
        self._duty = low + (high - low) / 2.0

        self._pi = pigpio.pi()
        self._update()

    def _update(self):
        self._pi.hardware_PWM(self._pin, self._freq, self._duty / 100 * 1e6)

    @property
    def position(self):
        return (self._duty - self._low) / (self._high - self._low) * self._range

    @position.setter
    def position(self, val):
        self._duty = self._low + val / self._range * (self._high - self._low)
        self._update()


class PenLifter(Servo):

    def __init__(self, up_pos=0, down_pos=90, move_time=.5, **kwargs):
        super(self.__class__, self).__init__(**kwargs)

        self._up = up_pos
        self._down = down_pos
        self._time = move_time
        self.up()

    def up(self):
        dt = self._time / 30.0
        for val in np.linspace(self.position, self._up, 30):
            self.position = val
            time.sleep(dt)
        #self.position = self._up

    def down(self):
        dt = self._time / 30.0
        for val in np.linspace(self.position, self._down, 30):
            self.position = val
            time.sleep(dt)
        #self.position = self._down
