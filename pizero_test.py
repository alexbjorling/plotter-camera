import drawing      # tools for image handling and designing drawings
import controls     # tools for running the hardware

# calculate how to draw it
sketch = drawing.Sketch('drawing/image.jpg')
trajectory = sketch.contourDrawing()
trajectory.dump('dump.npz')
