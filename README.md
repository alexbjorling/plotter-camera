to do drawing:
* path optimization
* add more filters and find good balance
* semantics

to do controls:
* bug in big plotter: error accumulation for many small movements.
* consider using edge event detection for the limit switches, but that part of the gpio lib doesn't seem entirely stable
* small plotter: pre-load waveforms onto the motors to improve performance? use threading timers somehow?
* big plotter: polarograph subclass to Trajectory
