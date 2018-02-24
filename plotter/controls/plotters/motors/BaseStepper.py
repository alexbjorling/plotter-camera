import threading

class BaseStepper(object):

    def __init__(self):
        # status member
        self.running = False

        # calibration number, must be set in the subclass
        self.per_step = None

    @property
    def position(self):
        """
        Returns the physical position of the motor according to internal
        records.
        """
        raise NotImplementedError

    @position.setter
    def position(self, val):
        """
        Sets the physical motor position.
        """
        raise NotImplementedError

    def _move(self, steps, delay=.002):
        """
        Blocking relative move in steps. Should set the self.running
        flag at beginning and end of move.
        """
        raise NotImplementedError

    def stop(self):
        """
        Stop an ongoing movement.
        """
        raise NotImplementedError

    def off(self):
        """
        Turn off the motor current.
        """
        raise NotImplementedError

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
        steps = int(round(distance / self.per_step))
        t = threading.Thread(target=self._move, kwargs={'steps': steps, 'delay': delay})
        t.start()
