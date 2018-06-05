to do drawing:
* path optimization
* add more filters and find good balance
* semantics
* SVG parsing: do the stepper math for Bezier curves or make a Trajectory.from_svg() method that bisects paths to lines?
    * pro: smooth lines at the resolution of the steppers
    * con: Trajectory has to be complicated to include curve type and control point info
    * con: maths might not be possible or at least have to be done for each curve type
    * con: operations on Trajectory (like optimization) won't work so well

bugs?:
* waveforms pause in between segments, especially large ones?
* think through the range signs and types wrt scaling

to do controls:
* move to pigpio and use a global pi() instace
* reorganize library, too complicated and "motors" should be "devices"
* consider using edge event detection for the limit switches, but that part of the gpio lib doesn't seem entirely stable
* small plotter: pre-load waveforms onto the motors to improve performance? use threading timers somehow?
* big plotter: polarograph subclass to Trajectory
