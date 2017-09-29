import drawing      # tools for image handling and designing drawings
import controls     # tools for running the hardware

# acquire an image
camera = controls.Camera()
image = camera.get_image()

# calculate how to draw it
sketch = drawing.Sketch(image)
trajectory = sketch.contourDrawing()

# draw it
plotter = controls.Plotter()
plotter.plot(trajectory)
