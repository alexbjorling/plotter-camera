to do drawing:
* replace Canny with difference-of-Gaussians plus skeletonize
* handle the double countours generated by cv2.findContours (or use different method)
* think about using a hybrid filter (various gaussian filters plus Canny etc)
* semantics

to do controls:
* consider using edge event detection for the limit switches, but that part of the gpio lib doesn't seem entirely stable
* can we use threading timers instead of delays to improve the motor movement loop?
* if so, could we pre-load waveforms onto the motors to improve performance?
