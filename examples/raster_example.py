"""
Shows how to make a raster plot from a photograph, and how to preview
the plot on screen.
"""

from plotter.drawing import Sketch, TEST_PNG
import matplotlib.pyplot as plt

# Create a Sketch, an object which holds an image and has the power to
# turn it into a drawing. Replace TEST_PNG by the path to your image.
mySketch = Sketch(image=TEST_PNG, max_size=500)

# Make a raster plot from the image, which is then a Trajectory object.
# You could also use mySketch.frequency_mod_scan() which has its own
# parameters.
myTrajectory = mySketch.amplitude_mod_scan(n_lines=50,
                                           pixels_per_period=6,
                                           waveform='sawtooth',
                                           gain=1.5)

# Preview the Trajectory on screen...
myTrajectory.plot()
plt.show()

# ...or save the trajectory as an npz file
myTrajectory.dump('/tmp/my_raster_plot.npz')
