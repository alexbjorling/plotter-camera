from plotter.plotters import BigVPlotter, SmallVPlotter
from plotter.drawing import TestPattern
import time

# first the GPIO has to be set up
import RPi.GPIO as GPIO
GPIO.setmode(GPIO.BCM)

# create a plotter object which represents the whole device. The
# constructor call takes a bunch of parameters but we will use the
# defaults now.
myPlotter = BigVPlotter()

# we now have two motors which we can act on independently
print myPlotter.m1.position
print myPlotter.m2.position

# we can move them with non-blocking calls
myPlotter.m1.relmove(-100) # 100 mm negative move
myPlotter.m2.relmove(50)   # 50 mm positive move
while myPlotter.m1.running or myPlotter.m2.running:
    time.sleep(.1)

# we also have a pen which can go manually up and down
myPlotter.pen.down()
time.sleep(1)
myPlotter.pen.up()

# the plotter needs to know where its motors are. we can either measure
# the strings and set the individual motor positions,
myPlotter.m1.position = 2000
myPlotter.m2.position = 2000
# or we can use the plotter's position property if the (x,y) position is known.
print myPlotter.position
myPlotter.position = (100, 200)

# we also need to define the area in which to draw. The origin is at the
# left-land motor point.
myPlotter.xrange = (200, 800) # from 200 to 800 mm horizontally from the left motor point.
myPlotter.yrange = (300, 1000) # from 300 to 1000 mm vertically from the left motor point.

# ok now we can plot something. The plotter class has a built-in test
# method which plots a test pattern.
myPlotter.test()

