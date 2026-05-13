#!/usr/bin/env python3
import serial
import evdev
from evdev import UInput, AbsInfo, ecodes as e

# --- Конфигурация ---
SERIAL_PORT = "/dev/ttyACM0"    # поменяйте если нужно
BAUD_RATE = 38400               # поменяйте если нужно

# Разрешение дигитайзера
# У WACOM DIGITIZER UNIT SU-1208E-01X это 6144x4608, максимальное давление 16383
MAX_X = 6144
MAX_Y = 4608
MAX_PRESSURE = 16383

def open_serial():
    return serial.Serial(port=SERIAL_PORT, baudrate=BAUD_RATE, timeout=0.05)

def create_uinput():
    capabilities = {
        e.EV_KEY: [
            e.BTN_TOOL_PEN, 
            e.BTN_TOOL_RUBBER, 
            e.BTN_TOUCH, 
            e.BTN_STYLUS
        ],
        e.EV_ABS: [
            (e.ABS_X,        AbsInfo(value=0, min=0, max=MAX_X,      fuzz=0, flat=0, resolution=1)),
            (e.ABS_Y,        AbsInfo(value=0, min=0, max=MAX_Y,      fuzz=0, flat=0, resolution=1)),
            (e.ABS_PRESSURE, AbsInfo(value=0, min=0, max=MAX_PRESSURE, fuzz=0, flat=0, resolution=0)),
        ],
    }
    return UInput(capabilities, name="Wacom ISDV4 Fixed", version=0x1)

def parse_isdv4_8byte(packet):
    header = packet[0]
    
    # 0x20 - признак нахождения в зоне, 0x04 - ластик
    proximity = bool(header & 0x20)
    eraser    = bool(header & 0x04)
    tip       = bool(header & 0x01)
    side1     = bool(header & 0x02)

    # Координаты и давление по индексам из дампа xxd
    x = (packet[1] << 7) | packet[2]
    y = (packet[3] << 7) | packet[4]
    pressure = (packet[5] << 7) | packet[6]

    return {
        "x": x, "y": y, "pressure": pressure,
        "proximity": proximity, "eraser": eraser,
        "tip": tip, "btn1": side1
    }

def main():
    print(f"Драйвер активен на {SERIAL_PORT}")
    try:
        ser = open_serial()
        ui = create_uinput()
    except Exception as ex:
        print(f"Ошибка инициализации: {ex}"); return

    buf = bytearray()
    last_eraser = None 

    try:
        while True:
            data = ser.read(16)
            if not data: continue
            buf.extend(data)

            while len(buf) >= 8:
                if not (buf[0] & 0x80):
                    buf.pop(0)
                    continue
                
                pkt_data = buf[:8]
                buf = buf[8:]
                pkt = parse_isdv4_8byte(pkt_data)

                # Логика чистого переключения инструментов (как мы выяснили, так лучше всего)
                if last_eraser is not None and last_eraser != pkt["eraser"]:
                    ui.write(e.EV_KEY, e.BTN_TOUCH, 0)
                    ui.write(e.EV_ABS, e.ABS_PRESSURE, 0)
                    ui.write(e.EV_KEY, e.BTN_TOOL_PEN, 0)
                    ui.write(e.EV_KEY, e.BTN_TOOL_RUBBER, 0)
                    ui.syn()
                
                last_eraser = pkt["eraser"]

                if pkt["proximity"]:
                    # Выбираем активный инструмент
                    ui.write(e.EV_KEY, e.BTN_TOOL_RUBBER if pkt["eraser"] else e.BTN_TOOL_PEN, 1)
                    ui.write(e.EV_KEY, e.BTN_TOOL_PEN if pkt["eraser"] else e.BTN_TOOL_RUBBER, 0)
                    
                    ui.write(e.EV_ABS, e.ABS_X, pkt["x"])
                    ui.write(e.EV_ABS, e.ABS_Y, pkt["y"])
                    ui.write(e.EV_ABS, e.ABS_PRESSURE, pkt["pressure"])

                    # Нажатие: по биту tip или по порогу давления
                    is_touch = pkt["tip"] or pkt["pressure"] > 50
                    ui.write(e.EV_KEY, e.BTN_TOUCH, 1 if is_touch else 0)
                    ui.write(e.EV_KEY, e.BTN_STYLUS, 1 if pkt["btn1"] else 0)
                else:
                    # Вне зоны - сбрасываем всё
                    ui.write(e.EV_KEY, e.BTN_TOOL_PEN, 0)
                    ui.write(e.EV_KEY, e.BTN_TOOL_RUBBER, 0)
                    ui.write(e.EV_KEY, e.BTN_TOUCH, 0)
                    ui.write(e.EV_ABS, e.ABS_PRESSURE, 0)

                ui.syn()

    except KeyboardInterrupt:
        print("\nОстановка драйвера...")
    finally:
        ser.close()
        ui.close()

if __name__ == "__main__":
    main()
