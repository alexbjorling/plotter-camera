"""
Shows how to make a contour plot from a photograph, and how to preview
the plot on screen.
"""

from plotter.drawing import Sketch, TEST_PNG
import matplotlib.pyplot as plt

# Create a Sketch, an object which holds an image and has the power to
# turn it into a drawing. Replace TEST_PNG by the path to your image.
mySketch = Sketch(image=TEST_PNG, max_size=1000)

# Make a contour plot from the image, which is then a Trajectory object.
# There are a few parameters to play with here, see help(Sketch).
myTrajectory = mySketch.contour_drawing()

# Preview the Trajectory on screen...
myTrajectory.plot()
plt.show()

# ...or save the trajectory as an npz file
myTrajectory.dump('/tmp/my_contour_plot.npz')
