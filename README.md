# WACOM-ThinkPad-X60T-Digitizer
It's working now as a tablet

Dependencies (for ArchLinux): ```python-pyserial``` and ```python-evdev```
```
sudo pacman -S python-pyserial python-evdev
```
Load ```uinput``` module:
```
sudo modprobe uinput
```

Add yourself to ```uucp``` group:
```
sudo usermod -aG uucp $USER
```
And run (check rights if couldn't execute):
```
sudo python ./wacom_tp_x60t_isdv4.py
```
