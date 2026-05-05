---
title: Module Lessons
---

### Overview


## Project code
Following is my Zip for the code available for download from [*here*](Motor subsystem.zip).

This code includes certificates for the ESP32, boot.py, main.py, and config.py for WiFi configuration. To run it, make sure to use either pymaker or mpremote in VS Code. I would highly suggest using mpremote to download the code to the ESP32. To do that, download the mpremote library from VS Code.

Use the following commands on the terminal, once you open the folder on VS Code and set up the mpremote: 

To use the ESP32, type in the terminal: mpremote connect auto
<br>

To program ESP32 type: mpremote fs ls -r
Make sure to change the config.py with your local WiFi name and password so that the ESP32 can work wirelessly and you can control motors.



---
## Individual motor code

```python title="main.py"
import machine
import time

SCK_PIN = 12
SI_PIN = 11
SO_PIN = 13

# From your schematic
CS_FRONT_LEFT  = 5   # CSN1
CS_FRONT_RIGHT = 6    # CSN2
CS_BACK_LEFT   = 7    # CSN3
CS_BACK_RIGHT  = 8    # CSN4

WR_FORWARD = 0xFF
WR_REVERSE = 0xFD
WR_STOP    = 0xF8

spi = machine.SPI(
    2,
    baudrate=1000000,
    polarity=0,
    phase=1,
    sck=machine.Pin(SCK_PIN),
    mosi=machine.Pin(SI_PIN),
    miso=machine.Pin(SO_PIN),
)

fl = machine.Pin(CS_FRONT_LEFT, machine.Pin.OUT, value=1)
fr = machine.Pin(CS_FRONT_RIGHT, machine.Pin.OUT, value=1)
bl = machine.Pin(CS_BACK_LEFT, machine.Pin.OUT, value=1)
br = machine.Pin(CS_BACK_RIGHT, machine.Pin.OUT, value=1)

time.sleep(0.1)

def send_one(cs_pin, cmd_byte):
    cs_pin.value(0)
    time.sleep_us(2)
    spi.write(bytearray([cmd_byte]))
    time.sleep_us(2)
    cs_pin.value(1)
    time.sleep_us(2)

def stop_all():
    for cs in (fl, fr, bl, br):
        send_one(cs, WR_STOP)

def move_forward():
    send_one(fl, WR_FORWARD)
    send_one(fr, WR_REVERSE)
    send_one(bl, WR_FORWARD)
    send_one(br, WR_REVERSE)

def move_backward():
    send_one(fl, WR_REVERSE)
    send_one(fr, WR_FORWARD)
    send_one(bl, WR_REVERSE)
    send_one(br, WR_FORWARD)

print("4 motors ready")

try:
    while True:
        move_forward()
        print("forward")
        time.sleep(2)

        move_backward()
        print("backward")
        time.sleep(2)

except KeyboardInterrupt:
    stop_all()
    print("Program stopped")


```

---