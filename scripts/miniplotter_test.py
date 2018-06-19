from plotter.plotters import MiniPlotter
import RPi.GPIO as GPIO

GPIO.setmode(GPIO.BCM)

mp = MiniPlotter()
mp.test()
