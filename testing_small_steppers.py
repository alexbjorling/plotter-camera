import RPi.GPIO as GPIO
import time
import threading

class L9110(object):

    def __init__(self, pins, twophase=False):
        """
        Input:

        pins (list):     I/O pins connected to the [B-1A, B-1B, A-1A, A-1B]
                         inputs on the L9110s stepper driver.
        twophase (bool): Whether to run in two-phase mode.
        """

        print 'initializing motor...'
        self.pins = pins

        if twophase:
            self.SEQ = [
                [0, 1, 1, 0],
                [0, 1, 0, 1],
                [1, 0, 0, 1],
                [1, 0, 1, 0],
                ]
        else:
            self.SEQ = [
                [1, 0, 0, 0],
                [0, 0, 1, 0],
                [0, 1, 0, 0],
                [0, 0, 0, 1],
                ]

        # set up pin addresses
        GPIO.setmode(GPIO.BCM)

        for pin in self.pins:
            GPIO.setup(pin, GPIO.OUT, initial=GPIO.LOW)

        self.running = False

        print '  ...done'

    def move(self, steps, delay=.003):
        self.running = True        
        t = threading.Thread(target=self._move, kwargs={'steps': steps, 'delay': delay})
        t.start()

    def _move(self, steps, delay=.002):
        reverse = False
        if steps < 0:
            reverse = True
            steps = -steps
        for i in range(steps):
            i_ = i % len(self.SEQ)
            if reverse:
                i_ = len(self.SEQ) - 1 - i_
            for j in range(len(self.pins)):
                GPIO.output(self.pins[j], self.SEQ[i_][j])
            time.sleep(delay)
        self.running = False

if __name__ == '__main__':
    try:
        m1 = L9110([6, 13, 19, 26], twophase=False)
        m2 = L9110([12, 16, 20, 21], twophase=True)
        m3 = L9110([24, 25, 8, 7], twophase=True)

        if False:
            #m1.move(20)
            m2.move(-50)
            m3.move(-50)
            while m1.running or m2.running or m3.running:
                print 'running'
                time.sleep(.1)
            GPIO.cleanup(); exit(0)

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
            while m1.running or m2.running or m3.running:
                time.sleep(.1)

        time.sleep(10)
        m1.move(-dm1)
        m2.move(-dm2)
        m3.move(-dm2)
        while m1.running or m2.running or m3.running:
                time.sleep(.1)        

        print 'cleaning up'
        GPIO.cleanup()

    except:
        GPIO.cleanup()
        print 'cleaning up after error'
        raise
