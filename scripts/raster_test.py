import plotter.drawing
import plotter.plotters

# read or acquire an image
#camera = plotter.controls.Camera()
#image = camera.get_image()
#sketch = drawing.Sketch(image)
sketch = plotter.drawing.Sketch('plotter/drawing/image.jpg')

# create a trajectory
traj = sketch.frequencyModScan(nLines=30, pixelsPerTypicalPeriod=2.1, waveform='sawtooth')

# plot it
mp = plotter.plotters.MiniPlotter()
mp.plot(traj)
