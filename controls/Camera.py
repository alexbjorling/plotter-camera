import matplotlib.pyplot as plt


class Camera(object):
    """
    Class representing the hardware camera.
    """

    def __init__(self):
        pass

    def get_image(self):
        """
        Acquire an image from the camera and return ndarray. Dummy for now.
        """
        return plt.imread('drawing/image.jpg')
