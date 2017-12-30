from plotter.controls.plotters import MiniPlotter

mp = MiniPlotter()

try:
    mp.test()
except:
    del mp
