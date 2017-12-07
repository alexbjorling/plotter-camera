from picamera import PiCamera
from picamera.array import PiRGBArray

class Camera(PiCamera):
    """
    Class representing the hardware camera, wrapping the 
    picamera.PiCamera class in order to encapsulate settings and return
    an array.

    Currently setting the full field of view of the sensor doesn't work
    and the behaviour is not as described in the API doc. Just leaving
    the default sensor_mode and resolution, it'll do.
    """

    def get_image(self):
        """
        Acquire an image from the camera and return BGR ndarray.
        """
        self.vflip = True
        self.capture('test.jpg', resize=None)#, resize=SHAPE)
        output = PiRGBArray(self)
        self.capture(output, 'bgr')
        return output.array

# test
if __name__ == '__main__':
    import time
    import cv2
    cam = Camera()
    time.sleep(2)
    im = cam.get_image()
    cv2.imwrite('test.jpg', im)
