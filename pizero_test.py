import drawing      # tools for image handling and designing drawings
import controls     # tools for running the hardware

# take an image
camera = controls.Camera()
image = camera.get_image()

# do the maths
sketch = drawing.Sketch(image)
trajectory = sketch.contourDrawing()

# dump
trajectory.dump('dump.npz')
