import ssl
import time
import uasyncio as asyncio
from machine import UART, Pin, SPI

from mqtt_as import MQTTClient, config as mqtt_cfg
from config import (
    MQTT_PASSWORD,
    MQTT_SERVER,
    MQTT_USER,
    TOPIC_C_TO_W,
    TOPIC_W_TO_C,
    WIFI_PASSWORD,
    WIFI_SSID,
)

try:
    from mqtt_local import wifi_led
except ImportError:
    def wifi_led(_state):
        pass


# ============================================================================
# MOTOR SUBSYSTEM (W) - MQTT + UART DAISY CHAIN
# Team 202 - Asadbek - Motor/Wheel Subsystem
# ============================================================================

# ---------------------------------------------------------------------------
# SPI Configuration for Motor Control
# ---------------------------------------------------------------------------

SCK_PIN = 12
MOSI_PIN = 11
MISO_PIN = 13
CS_PIN1 = 5
CS_PIN2 = 6
CS_PIN3 = 7
CS_PIN4 = 8

spi = SPI(
    2,
    baudrate=1_000_000,
    polarity=0,
    phase=1,
    sck=Pin(SCK_PIN),
    mosi=Pin(MOSI_PIN),
    miso=Pin(MISO_PIN),
)

cs1 = Pin(CS_PIN1, Pin.OUT)
cs2 = Pin(CS_PIN2, Pin.OUT)
cs3 = Pin(CS_PIN3, Pin.OUT)
cs4 = Pin(CS_PIN4, Pin.OUT)

for cs_pin in (cs1, cs2, cs3, cs4):
    cs_pin.value(1)

time.sleep(0.1)

WR_FORWARD = 0b11111111
WR_REVERSE = 0b11111101
WR_STOP = 0b11111000

# ---------------------------------------------------------------------------
# UART Configuration for Daisy Chain to other subsystems
# ---------------------------------------------------------------------------

UART_DAISY_ID = 1
UART_DAISY_TX = 43
UART_DAISY_RX = 44
UART_DAISY_BAUD = 9600

uart_daisy = UART(UART_DAISY_ID, baudrate=UART_DAISY_BAUD, tx=UART_DAISY_TX, rx=UART_DAISY_RX)
uart_daisy.init(UART_DAISY_BAUD, bits=8, parity=None, stop=1)

# ---------------------------------------------------------------------------
# Protocol Constants
# ---------------------------------------------------------------------------

PREFIX = b"AZ"
SUFFIX = b"YB"

MY_ID = ord("w")
BCAST_ID = ord("X")
TEAM_IDS = {ord("h"), ord("c"), ord("w"), ord("p"), ord("a"), ord("m"), ord("t")}

MAX_DATA_LENGTH = 58
MAX_PACKET_LENGTH = 2 + 1 + 1 + MAX_DATA_LENGTH + 2

# ---------------------------------------------------------------------------
# LEDs
# ---------------------------------------------------------------------------

led_red = Pin(10, Pin.OUT)
led_green = Pin(9, Pin.OUT)
led_broadcast = Pin(1, Pin.OUT)  # Broadcast indicator on IO1

# ---------------------------------------------------------------------------
# State / Buffers
# ---------------------------------------------------------------------------

motor_running = False
motor_direction = "STOPPED"
last_motion_command_ms = 0
MOTOR_FAILSAFE_MS = 350

rx_buffer_daisy = b""
mqtt_client = None


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def id_to_char(value):
    try:
        return chr(value)
    except Exception:
        return "?"


def blink(pin, duration_ms=100):
    pin.value(1)
    time.sleep_ms(duration_ms)
    pin.value(0)


def blink_red():
    blink(led_red)


def blink_green():
    blink(led_green)


# ---------------------------------------------------------------------------
# Motor Control
# ---------------------------------------------------------------------------

def write_one(cs_pin, cmd_byte):
    cs_pin.value(0)
    time.sleep_us(2)
    spi.write(bytearray([cmd_byte]))
    time.sleep_us(2)
    cs_pin.value(1)
    time.sleep_us(2)


def set_all_motors(cmd_byte, direction_label):
    global motor_running, motor_direction

    for cs_pin in (cs1, cs2, cs3, cs4):
        write_one(cs_pin, cmd_byte)

    motor_running = direction_label != "STOPPED"
    motor_direction = direction_label


def set_h_bridge_spi(direction_forward):
    global last_motion_command_ms

    if direction_forward:
        set_all_motors(WR_FORWARD, "FORWARD")
    else:
        set_all_motors(WR_REVERSE, "BACKWARD")
    last_motion_command_ms = time.ticks_ms()


def stop_all_motors():
    global last_motion_command_ms

    set_all_motors(WR_STOP, "STOPPED")
    last_motion_command_ms = 0


def motor_right():
    global motor_running, motor_direction, last_motion_command_ms

    write_one(cs1, WR_FORWARD)
    write_one(cs2, WR_REVERSE)
    write_one(cs3, WR_FORWARD)
    write_one(cs4, WR_REVERSE)

    motor_running = True
    motor_direction = "RIGHT"
    last_motion_command_ms = time.ticks_ms()


def motor_left():
    global motor_running, motor_direction, last_motion_command_ms

    write_one(cs1, WR_REVERSE)
    write_one(cs2, WR_FORWARD)
    write_one(cs3, WR_REVERSE)
    write_one(cs4, WR_FORWARD)

    motor_running = True
    motor_direction = "LEFT"
    last_motion_command_ms = time.ticks_ms()


# ---------------------------------------------------------------------------
# Packet Utilities
# ---------------------------------------------------------------------------

def validate_packet(packet):
    if not isinstance(packet, (bytes, bytearray)):
        print("ERROR: Packet is not bytes")
        blink_red()
        return False

    packet = bytes(packet).strip()

    if len(packet) < 6:
        print("ERROR: Packet too short")
        blink_red()
        return False

    if len(packet) > MAX_PACKET_LENGTH:
        print("ERROR: Packet too long")
        blink_red()
        return False

    if not packet.startswith(PREFIX) or not packet.endswith(SUFFIX):
        print("ERROR: Bad prefix/suffix")
        blink_red()
        return False

    sender = packet[2]
    if sender not in TEAM_IDS:
        print("ERROR: Unknown sender '%s'" % id_to_char(sender))
        blink_red()
        return False

    return True


def parse_packet(packet):
    sender = packet[2]
    receiver = packet[3]
    data = packet[4:-2].decode("utf-8", "ignore")
    return sender, receiver, data


def build_packet(receiver, data):
    if isinstance(receiver, str):
        receiver = ord(receiver)

    payload = data.encode("utf-8")
    if len(payload) > MAX_DATA_LENGTH:
        print("WARNING: Data too long, truncating")
        payload = payload[:MAX_DATA_LENGTH]

    return PREFIX + bytes([MY_ID, receiver]) + payload + SUFFIX


# ---------------------------------------------------------------------------
# Command Processing
# ---------------------------------------------------------------------------

def process_motor_command(sender, data):
    """
    Process motor commands - ONLY send response for specific queries
    Don't broadcast on every wheel movement!
    """
    try:
        parts = data.split(":")

        # Bluetooth check command
        if len(parts) >= 3 and parts[0] == "BT" and parts[1] == "S":
            bt_value = parts[2].rstrip(";")
            if bt_value == "check":
                blink_green()
                print(">>> BLUETOOTH CHECK RECEIVED")
                return ord("c"), "BT:S:T;"
            return ord("c"), "BT:S:F;"

        # Wheel drive commands - NO BROADCAST NEEDED
        if len(parts) >= 3 and parts[0] == "WD" and parts[1] == "S":
            direction = parts[2].rstrip(";").upper()

            print("\n" + "=" * 50)
            print("MOTOR COMMAND FROM '%s'" % id_to_char(sender))
            print("Data:", data)
            print("Direction:", direction)
            print("=" * 50)

            if direction == "F":
                set_h_bridge_spi(True)
                blink_green()
                print(">>> MOTORS: FORWARD")
                return None  # Don't send response - just move

            if direction == "B":
                set_h_bridge_spi(False)
                blink_green()
                print(">>> MOTORS: BACKWARD")
                return None  # Don't send response - just move

            if direction == "R":
                motor_right()
                blink_green()
                print(">>> MOTORS: RIGHT TURN")
                return None  # Don't send response - just move

            if direction == "L":
                motor_left()
                blink_green()
                print(">>> MOTORS: LEFT TURN")
                return None  # Don't send response - just move

            if direction == "S":
                stop_all_motors()
                blink_red()
                print(">>> MOTORS: STOPPED")
                return None  # Don't send response

            print(">>> Unknown direction:", direction)
            return None

        # Start message - respond with broadcast
        if len(parts) >= 3 and parts[0] == "ST" and parts[1] == "S":
            blink_green()
            print(">>> START MESSAGE RECEIVED")
            return BCAST_ID, "ST:S:WheelReady;"

        return None

    except Exception as exc:
        print("ERROR processing command:", exc)
        stop_all_motors()
        return None


# ---------------------------------------------------------------------------
# Packet Handling
# ---------------------------------------------------------------------------

async def handle_packet(packet):
    packet = bytes(packet).strip()

    if not validate_packet(packet):
        print("REJECTED:", packet)
        return

    sender, receiver, data = parse_packet(packet)

    # ERROR HANDLING: Discard messages from self
    if sender == MY_ID:
        print("\n" + "*" * 50)
        print(">>> MESSAGE FROM SELF - DISCARDING")
        print(">>> Packet:", packet.decode("utf-8", "ignore"))
        print("*" * 50 + "\n")
        blink_red()
        return

    # MESSAGE FOR ME or BROADCAST
    if receiver == MY_ID or receiver == BCAST_ID:
        print("\n" + "#" * 60)
        print("### MESSAGE FOR WHEEL SUBSYSTEM ###")
        print("### From:", id_to_char(sender))
        print("### To  :", id_to_char(receiver))
        print("### Data:", data)
        print("### Full:", packet.decode("utf-8", "ignore"))
        print("#" * 60)

        # Visual feedback - different for broadcast vs direct message
        if receiver == BCAST_ID:
            # BROADCAST - Turn on IO1 LED
            print(">>> BROADCAST RECEIVED - Turning on IO1 LED")
            led_broadcast.value(1)
            await asyncio.sleep_ms(500)
            led_broadcast.value(0)
        else:
            # Direct message - blink green
            for _ in range(3):
                led_green.value(1)
                await asyncio.sleep_ms(100)
                led_green.value(0)
                await asyncio.sleep_ms(100)

        # Process command and get optional response
        response = process_motor_command(sender, data)
        
        # Only send MQTT response if command returned one AND it's not a broadcast
        if response and mqtt_client and receiver != BCAST_ID:
            response_receiver, response_data = response
            response_packet = build_packet(response_receiver, response_data)
            print(">>> Sending response via MQTT:", response_packet)
            await mqtt_client.publish(TOPIC_W_TO_C, response_packet, qos=1)

        # If it was a BROADCAST, forward it down the daisy chain
        if receiver == BCAST_ID:
            print(">>> FORWARDING BROADCAST TO DAISY CHAIN")
            uart_daisy.write(packet + b'\r\n')  # Add line ending!
        
        return

    # MESSAGE FOR OTHER SUBSYSTEM (a, p, m, t) - Forward via UART
    print("\n" + ">" * 50)
    print(">>> FORWARDING TO DAISY CHAIN")
    print(">>> From '%s' to '%s'" % (id_to_char(sender), id_to_char(receiver)))
    print(">>> Data:", data)
    print(">>> Full:", packet.decode("utf-8", "ignore"))
    print(">" * 50 + "\n")

    # CRITICAL FIX: Add \r\n to match Jacob's format
    uart_daisy.write(packet + b'\r\n')


# ---------------------------------------------------------------------------
# MQTT -> Motor (receive from Communication)
# ---------------------------------------------------------------------------

def mqtt_sub_cb(topic, msg, retained):
    """Callback when message received from MQTT"""
    try:
        topic_name = topic.decode() if isinstance(topic, (bytes, bytearray)) else str(topic)
    except Exception:
        topic_name = str(topic)

    print("\n[MQTT] Received from topic:", topic_name)
    print("[MQTT] Message:", msg)
    asyncio.create_task(handle_packet(msg))


# ---------------------------------------------------------------------------
# UART Daisy Chain -> MQTT (receive from other subsystems)
# ---------------------------------------------------------------------------

async def publish_uart_packet(packet):
    """Send packet from daisy chain back to Communication via MQTT"""
    if packet and mqtt_client:
        print("\n[UART DAISY] Received packet from subsystems")
        print("[UART DAISY] Sending to MQTT:", packet)
        await mqtt_client.publish(TOPIC_W_TO_C, packet, qos=1)


async def uart_daisy_task():
    """Read from UART daisy chain and forward to MQTT"""
    global rx_buffer_daisy

    while True:
        if uart_daisy.any():
            chunk = uart_daisy.read()
            if chunk:
                rx_buffer_daisy += chunk

                # Look for complete packets
                while True:
                    start_idx = rx_buffer_daisy.find(PREFIX)
                    if start_idx == -1:
                        if len(rx_buffer_daisy) > MAX_PACKET_LENGTH * 2:
                            rx_buffer_daisy = b""
                        break

                    if start_idx > 0:
                        rx_buffer_daisy = rx_buffer_daisy[start_idx:]

                    end_idx = rx_buffer_daisy.find(SUFFIX, 4)
                    if end_idx == -1:
                        if len(rx_buffer_daisy) > MAX_PACKET_LENGTH * 2:
                            rx_buffer_daisy = rx_buffer_daisy[-MAX_PACKET_LENGTH:]
                        break

                    packet = rx_buffer_daisy[:end_idx + len(SUFFIX)]
                    rx_buffer_daisy = rx_buffer_daisy[end_idx + len(SUFFIX):]

                    if validate_packet(packet):
                        await publish_uart_packet(packet)
        else:
            await asyncio.sleep_ms(1)


async def motor_failsafe_task():
    """Auto-stop motors if no command received within timeout"""
    global last_motion_command_ms

    while True:
        if motor_running and last_motion_command_ms:
            elapsed = time.ticks_diff(time.ticks_ms(), last_motion_command_ms)
            if elapsed >= MOTOR_FAILSAFE_MS:
                print(">>> MOTOR FAILSAFE: auto-stop")
                stop_all_motors()
                blink_red()
        await asyncio.sleep_ms(50)


# ---------------------------------------------------------------------------
# WiFi / MQTT Handlers
# ---------------------------------------------------------------------------

async def wifi_han(state):
    wifi_led(not state)
    print("[WiFi]", "UP" if state else "DOWN")
    await asyncio.sleep(1)


async def conn_han(cli):
    await cli.subscribe(TOPIC_C_TO_W, 1)
    print("[MQTT] Subscribed to C->W:", TOPIC_C_TO_W)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

async def main(cli):
    global mqtt_client
    mqtt_client = cli

    try:
        await mqtt_client.connect()
        print("[SUCCESS] MQTT connected")
    except Exception as exc:
        print("[ERROR] MQTT connect failed:", exc)
        return

    # Start background tasks
    asyncio.create_task(uart_daisy_task())
    asyncio.create_task(motor_failsafe_task())

    print("\n" + "=" * 70)
    print(" " * 15 + "MOTOR SUBSYSTEM READY")
    print("=" * 70)
    print("My ID: 'w' (Wheel/Motor)")
    print("MQTT Topics:")
    print("  Receive (C->W):", TOPIC_C_TO_W)
    print("  Send (W->C)   :", TOPIC_W_TO_C)
    print("UART Daisy Chain: TX=%d, RX=%d, Baud=%d" % (UART_DAISY_TX, UART_DAISY_RX, UART_DAISY_BAUD))
    print("Motors initialized and ready.")
    print("=" * 70 + "\n")

    # Startup blink
    for _ in range(3):
        led_green.value(1)
        led_red.value(1)
        await asyncio.sleep_ms(200)
        led_green.value(0)
        led_red.value(0)
        await asyncio.sleep_ms(200)

    # Main loop
    while True:
        await asyncio.sleep(5)


# ---------------------------------------------------------------------------
# MQTT Configuration
# ---------------------------------------------------------------------------

mqtt_cfg["server"] = MQTT_SERVER
mqtt_cfg["ssid"] = WIFI_SSID
mqtt_cfg["wifi_pw"] = WIFI_PASSWORD
mqtt_cfg["ssl"] = True

try:
    with open("certs/cert26/student_key.pem", "rb") as f:
        key = f.read()
    with open("certs/cert26/student_crt.pem", "rb") as f:
        cert = f.read()
    with open("certs/cert26/ca_crt.pem", "rb") as f:
        ca = f.read()

    mqtt_cfg["ssl_params"] = {
        "cert": cert,
        "key": key,
        "cadata": ca,
        "server_hostname": MQTT_SERVER,
        "cert_reqs": ssl.CERT_REQUIRED,
    }
    print("[SSL] Certificates loaded successfully")
except Exception as exc:
    print("[ERROR] Failed to load SSL certificates:", exc)
    print("Make sure certs/cert26 contains student_key.pem, student_crt.pem, and ca_crt.pem")

mqtt_cfg["time_server"] = MQTT_SERVER
mqtt_cfg["time_server_timeout"] = 10
mqtt_cfg["subs_cb"] = mqtt_sub_cb
mqtt_cfg["wifi_coro"] = wifi_han
mqtt_cfg["connect_coro"] = conn_han
mqtt_cfg["clean"] = True
mqtt_cfg["user"] = MQTT_USER
mqtt_cfg["password"] = MQTT_PASSWORD


# ---------------------------------------------------------------------------
# Run
# ---------------------------------------------------------------------------

MQTTClient.DEBUG = True
client = MQTTClient(mqtt_cfg)

try:
    asyncio.run(main(client))
finally:
    stop_all_motors()
    led_red.value(0)
    led_green.value(0)
    led_broadcast.value(0)
    client.close()
    asyncio.new_event_loop()
    print("\nMotor subsystem stopped")