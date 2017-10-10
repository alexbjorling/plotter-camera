"""
Sketch of the main program.
"""

import RPi.GPIO as GPIO
import time
import controls
import drawing

# set up pin addresses
BUTTON_PIN = 17
LED_PIN = 18
GPIO.setmode(GPIO.BCM)

def go_callback(par):
    """
    This is where the functionality is.
    """
    print "go callback called"
    # disable more callbacks and enable an LED
    GPIO.remove_event_detect(BUTTON_PIN)
    GPIO.output(LED_PIN, GPIO.HIGH)

    # acquire an image
    image = camera.get_image()

    # calculate how to draw it
    sketch = drawing.Sketch(image)
    trajectory = sketch.contourDrawing() # SEGFAULTS THE SECOND TIME - NOT SURE WHY

    # draw it
    plotter = controls.Plotter()
    plotter.plot(trajectory)

    # restore everything
    GPIO.output(LED_PIN, GPIO.LOW)    
    activate_go_button()

def activate_go_button():
    """
    Activate background edge detection on the button.
    """
    GPIO.add_event_detect(BUTTON_PIN, GPIO.FALLING, callback=go_callback, bouncetime=200)

if __name__ == '__main__':
    # set up pins
    GPIO.setup(LED_PIN, GPIO.OUT, initial=GPIO.LOW)
    GPIO.setup(BUTTON_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    activate_go_button()

    # make a camera instance
    camera = controls.Camera()

    # main loop: doesn't have to run very fast
    try:
        while True:
            print "main loop running %s" % time.time()
            time.sleep(1)
    except:
        GPIO.cleanup()
        camera.close()
        raise

    GPIO.cleanup()
    camera.close()
