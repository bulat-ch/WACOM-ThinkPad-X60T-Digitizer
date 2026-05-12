# WACOM-ThinkPad-X60T-Digitizer (WIP!)

It works!  [Youtube link](https://youtu.be/RoAJn2lIkPo)

## Hardware part.

### What you need:
- USB <-> UART converter, wich support 3.3V (I used CH343);
- Wires or connector with wires;
- Digitizer module with coil array (I used SU-1208E-01X).

### How co connect:
All connecions on connector CN1.
```
Pin 14 - GND
Pin 13 - 3.3V
Pin 10 - UART TX
Pin 9 - UART RX
```
It's all.

![](https://github.com/bulat-ch/WACOM-ThinkPad-X60T-Digitizer/blob/main/images/Connections-Thinkpad-forum-de_Mystic-X.jpg)

Thanks for ```Mystic-X``` from [thinkpad-forum.de](https://thinkpad-forum.de/threads/wacom-digitizer-aus-x6-tablet-etwas-analysiert.159569/)! 


How I did:
![My version](https://github.com/bulat-ch/WACOM-ThinkPad-X60T-Digitizer/blob/main/images/photo_2026-05-12_19-55-46.jpg)
## OS part.

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




TO DO:
1. via rp2040, STM32?
2. add support for resistive touchpanel
