"""
Dummy module corresponding to RPi.GPIO, for dry running on non RPi
machines.
"""

print "Using dummy GPIO."

IN, OUT = 0, 0
LOW, HIGH = 0, 0
BCM = 0

def setup(*args, **kwargs):
    pass

def output(*args, **kwargs):
    pass

def setmode(*args, **kwargs):
    pass