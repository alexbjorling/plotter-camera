"""
Shows how to parse a Trajectory from an svg file, and how to preview
the plot on screen.
"""

from plotter.drawing import Trajectory, TEST_SVG
import matplotlib.pyplot as plt

myTraj = Trajectory()
myTraj.add_from_svg(TEST_SVG)

# Preview the Trajectory on screen...
myTraj.plot()
plt.show()

# ...or save the trajectory as an npz file
myTraj.dump('/tmp/my_svg_plot.npz')
