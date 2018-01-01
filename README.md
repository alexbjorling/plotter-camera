to do:

* consider using edge event detection for the limit switches, but that part of the gpio lib doesn't seem entirely stable
* can we use threading timers instead of delays to improve the motor movement loop?
* if so, could we pre-load waveforms onto the motors to improve performance?
