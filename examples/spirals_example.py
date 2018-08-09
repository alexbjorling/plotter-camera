from plotter.drawing import Trajectory
import numpy as np
import matplotlib.pyplot as plt
plt.ion()

class Spiral(Trajectory):
    """
    An Archimedean spiral r = a + b * \theta. The pitch is then 2*pi*b.

    Also: Apply a periodic radial deformation with given relative amplitude,
          periodicity, and phase.
    """
    def __init__(self, a=0, b=1/(2*np.pi), turns=10, resolution=180,
                 deformation_ampl=0.01, deformation_per=3, deformation_ph=0.0):
        super(Spiral, self).__init__()
        self.a = a
        self.b = b
        spiral = []
        for theta in np.linspace(0, turns * 2 * np.pi, turns * resolution):
            r = a + b * theta * (1 + deformation_ampl * np.sin(theta * deformation_per + deformation_ph))
            x = r * np.cos(theta)
            y = r * np.sin(theta)
            spiral.append([x, y])
        self.append(np.array(spiral))

s1 = Spiral(turns=50, deformation_ampl=.01, deformation_per=2)
s2 = Spiral(turns=50, deformation_ampl=.01, deformation_per=7, b=s1.b*.94)
s1.append(s2.paths[0])
s1.plot(linewidth=2)