try:
    from .Camera import Camera
except ImportError:
    print 'No picamera!'
from .LED import LED
from .LimitSwitch import LimitSwitch
