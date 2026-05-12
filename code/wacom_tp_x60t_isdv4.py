#!/usr/bin/env python3
"""
Wacom ISDV4 serial digitizer driver
Reads data from serial port and creates a uinput tablet device
"""

import serial
import evdev
from evdev import UInput, AbsInfo, ecodes as e
import time
import sys

# --- Настройки ---
SERIAL_PORT = "/dev/ttyACM0"    # поменяйте если нужно
BAUD_RATE = 38400               # поменяйте если нужно

# Разрешение дигитайзера 
# У WACOM DIGITIZER UNIT SU-1208E-01X это 6144x4608, максимальное давление 16383
MAX_X = 6144
MAX_Y = 4608
MAX_PRESSURE = 16383

def open_serial():
    ser = serial.Serial(
        port=SERIAL_PORT,
        baudrate=BAUD_RATE,
        bytesize=serial.EIGHTBITS,
        parity=serial.PARITY_NONE,
        stopbits=serial.STOPBITS_ONE,
        timeout=1
    )
    return ser

def create_uinput():
    capabilities = {
        e.EV_KEY: [
            e.BTN_TOOL_PEN,
            e.BTN_TOOL_RUBBER,
            e.BTN_TOUCH,
            e.BTN_STYLUS,
            e.BTN_STYLUS2,
        ],
        e.EV_ABS: [
            (e.ABS_X,        AbsInfo(value=0, min=0, max=MAX_X,      fuzz=0, flat=0, resolution=100)),
            (e.ABS_Y,        AbsInfo(value=0, min=0, max=MAX_Y,      fuzz=0, flat=0, resolution=100)),
            (e.ABS_PRESSURE, AbsInfo(value=0, min=0, max=MAX_PRESSURE, fuzz=0, flat=0, resolution=0)),
            (e.ABS_TILT_X,   AbsInfo(value=0, min=-63, max=63,       fuzz=0, flat=0, resolution=0)),
            (e.ABS_TILT_Y,   AbsInfo(value=0, min=-63, max=63,       fuzz=0, flat=0, resolution=0)),
        ],
    }
    ui = UInput(capabilities, name="Wacom Serial Digitizer", version=0x1)
    return ui

def parse_isdv4(buf):
    """
    ISDV4 пакет: 9 байт
    Байт 0: статус (бит7=1 - начало пакета)
    """
    if len(buf) < 9:
        return None
    if not (buf[0] & 0x80):
        return None  # не начало пакета

    x = ((buf[1] & 0x7f) << 7) | (buf[2] & 0x7f)
    y = ((buf[3] & 0x7f) << 7) | (buf[4] & 0x7f)
    pressure_raw = ((buf[5] & 0x7f) << 7) | (buf[6] & 0x7f)
    pressure = pressure_raw

    in_proximity = bool(buf[0] & 0x20)
    eraser       = bool(buf[0] & 0x04)  # бит2 = ластик
    tip          = pressure > 200
    btn1         = bool(buf[0] & 0x02)
    tilt_x       = (buf[7] & 0x3f)
    tilt_y       = (buf[8] & 0x3f)

    return {
        "x": x,
        "y": y,
        "pressure": pressure,
        "proximity": in_proximity,
        "eraser": eraser,
        "tip": tip,
        "btn1": btn1,
        "tilt_x": tilt_x,
        "tilt_y": tilt_y,
    }

def main():
    print(f"Открываю порт {SERIAL_PORT} @ {BAUD_RATE}...")
    try:
        ser = open_serial()
    except Exception as ex:
        print(f"Ошибка открытия порта: {ex}")
        sys.exit(1)

    print("Создаю виртуальное устройство uinput...")
    ui = create_uinput()
    print(f"Устройство создано: {ui.device.path}")
    print("Работаю... Ctrl+C для остановки.")

    buf = bytearray()
    last_eraser = None  # отслеживаем смену инструмента

    try:
        while True:
            data = ser.read(64)
            if not data:
                continue

            buf.extend(data)

            # Ищем начало пакета (бит7 = 1)
            while len(buf) >= 9:
                if not (buf[0] & 0x80):
                    buf.pop(0)
                    continue

                pkt = parse_isdv4(buf[:9])
                buf = buf[9:]

                if pkt is None:
                    continue

                # Сброс при смене инструмента
                if last_eraser is not None and last_eraser != pkt["eraser"]:
                    ui.write(e.EV_KEY, e.BTN_TOUCH,       0)
                    ui.write(e.EV_KEY, e.BTN_TOOL_PEN,    0)
                    ui.write(e.EV_KEY, e.BTN_TOOL_RUBBER, 0)
                    ui.write(e.EV_KEY, e.BTN_STYLUS,      0)
                    ui.write(e.EV_ABS, e.ABS_PRESSURE,    0)
                    ui.syn()
                last_eraser = pkt["eraser"]

                # Отправляем события
                ui.write(e.EV_ABS, e.ABS_X, pkt["x"])
                ui.write(e.EV_ABS, e.ABS_Y, pkt["y"])
                ui.write(e.EV_ABS, e.ABS_PRESSURE, pkt["pressure"])
                ui.write(e.EV_ABS, e.ABS_TILT_X, pkt["tilt_x"])
                ui.write(e.EV_ABS, e.ABS_TILT_Y, pkt["tilt_y"])
                if pkt["eraser"]:
                    ui.write(e.EV_KEY, e.BTN_TOOL_PEN,    0)
                    ui.write(e.EV_KEY, e.BTN_TOOL_RUBBER, 1 if pkt["proximity"] else 0)
                else:
                    ui.write(e.EV_KEY, e.BTN_TOOL_RUBBER, 0)
                    ui.write(e.EV_KEY, e.BTN_TOOL_PEN,    1 if pkt["proximity"] else 0)
                ui.write(e.EV_KEY, e.BTN_TOUCH,   1 if pkt["tip"] else 0)
                ui.write(e.EV_KEY, e.BTN_STYLUS,  1 if pkt["btn1"] else 0)
                ui.syn()

    except KeyboardInterrupt:
        print("\nОстановлено.")
    finally:
        ui.close()
        ser.close()

if __name__ == "__main__":
    main()

if __name__ == "__main__":
    main()
