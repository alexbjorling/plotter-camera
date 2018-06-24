import os
# these constants have to be defined first to avoid import trouble
TEST_SVG = os.path.join(os.path.dirname(__file__), 'ABC.svg')
TEST_PNG = os.path.join(os.path.dirname(__file__), 'image.jpg')

from .Trajectory import Trajectory, Rose, TestPattern
from .Sketch import Sketch
