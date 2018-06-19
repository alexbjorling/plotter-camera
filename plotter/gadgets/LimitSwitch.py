"""
General limit switch.
"""

try:
    import RPi.GPIO as GPIO
except ImportError:
    from . import DummyIO as GPIO

class LimitSwitch(object):
    def __init__(self, pin, mode='NO', load=0):
        """
        Arguments:

        pin: the GPIO pin
        type: 'NO' (default) or 'NC'
        load: 1 (the switch is fed a high level) or 0 (the switch is 
              fed) a low level
        """

        if load == 1 and mode == 'NO':
            self.pull_up_down = GPIO.PUD_DOWN
            self.trigger_level = GPIO.HIGH
        elif load == 1 and mode == 'NC':
            self.pull_up_down = GPIO.PUD_DOWN
            self.trigger_level = GPIO.LOW
        elif load == 0 and mode == 'NO':
            self.pull_up_down = GPIO.PUD_UP
            self.trigger_level = GPIO.LOW
        elif load == 0 and mode == 'NC':
            self.pull_up_down = GPIO.PUD_UP
            self.trigger_level = GPIO.HIGH
        else:
            raise Exception('Invalid input')

        self.pin = pin
        GPIO.setup(pin, GPIO.IN, pull_up_down=self.pull_up_down)

    @property
    def triggered(self):
        return (GPIO.input(self.pin) == self.trigger_level)

if __name__ == '__main__':
    l = LimitSwitch(14)
