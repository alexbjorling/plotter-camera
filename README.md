installation:
* python setup.py install --user
* for PWM you have to set that up, see Servo.py
* then you also need pigpio running:
    sudo pigpiod


to do drawing:
* path optimization
* add more filters and find good balance
* semantics

bugs?:
* waveforms pause in between segments, especially large ones?
* think through the range signs and types wrt scaling

to do controls:
* move to pigpio and use a global pi() instace
* consider using edge event detection for the limit switches, but that part of the gpio lib doesn't seem entirely stable
* small plotter: pre-load waveforms onto the motors to improve performance? use threading timers somehow?
* big plotter: polarograph subclass to Trajectory
