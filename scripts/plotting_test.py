from plotter.plotters import MiniPlotter
import time

mp = MiniPlotter()

time.sleep(1)
mp.test()

time.sleep(1)
mp.collective_move(mp.xrange[0], mp.yrange[0])
