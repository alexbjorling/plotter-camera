from plotter.drawing import Spiral
import numpy as np
import matplotlib.pyplot as plt
plt.ion()

s1 = Spiral(turns=50, deformation_ampl=.01, deformation_per=2)
s2 = Spiral(turns=50, deformation_ampl=.01, deformation_per=7, b=s1.b*.94)
s1.append(s2.paths[0])
s1.plot(linewidth=2)