from motors.L9110 import L9110
import RPi.GPIO as GPIO
import time

class MiniPlotter(object):
    """
    Class representing the small 2-axis plotter built from three L9110
    stepper controllers.
    """

    def __init__(self):

        # set up pin addressing
        GPIO.setmode(GPIO.BCM)

        # single motor for x/j axis
        self.m1 = L9110([6, 13, 19, 26], twophase=False)
        # two parallel motors for y/i axis
        self.m2 = L9110([12, 16, 20, 21], twophase=True)
        self.m3 = L9110([24, 25, 8, 7], twophase=True)

    def plot(self, traj):
        """
        Plot an entire Trajectory object.
        """
        pass

    def __del__(self):
        """
        The GPIO has to be cleaned up.
        """
        print 'Destroying %s object, cleaning up GPIO' % self.__class__.__name__
        GPIO.cleanup()

    def test(self):
        """
        Development test method that draws a simple pattern. To be replaced
        with Trajectory plotting.
        """
        m1, m2, m3 = self.m1, self.m2, self.m3
        L = 2600
        index = 0
        dm2 = 0
        dm1 = 0
        while L > 0:
            choice = index % 4
            if choice == 0:
                m2.move(L)
                m3.move(L)
                dm2 += L
            elif choice == 1:
                m1.move(L)
                dm1 += L
            elif choice == 2:
                m2.move(-L)
                m3.move(-L)
                dm2 -= L
            elif choice == 3:
                m1.move(-L)
                dm1 -= L
            while m1.running or m2.running or m3.running:
                time.sleep(.1)

            L -= 100
            index += 1

        time.sleep(3)
        m1.move(-dm1)
        m2.move(-dm2)
        m3.move(-dm2)
        while m1.running or m2.running or m3.running:
            time.sleep(.1)
