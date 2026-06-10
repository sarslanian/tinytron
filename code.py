import gc
import time
import board
import busio
import displayio
import adafruit_connection_manager
from adafruit_esp32spi.adafruit_esp32spi import ESP_SPIcontrol
from digitalio import DigitalInOut
from adafruit_matrixportal.matrixportal import MatrixPortal
import json
import adafruit_minimqtt.adafruit_minimqtt as MQTT
from secrets import secrets
from utils import wifi_tests, DEBUG_WIFI
from render import renderShape, renderText, renderImage

esp32_cs = DigitalInOut(board.ESP_CS)
esp32_ready = DigitalInOut(board.ESP_BUSY)
esp32_reset = DigitalInOut(board.ESP_RESET)
spi = busio.SPI(board.SCK, board.MOSI, board.MISO)
radio = ESP_SPIcontrol(spi, esp32_cs, esp32_ready, esp32_reset)

# --- MQTT Vars --- #
mqtt_broker = secrets["mqtt_broker"]
mqtt_port = secrets["mqtt_port"]
mqtt_topic = secrets["mqtt_topic"]

# --- MatrixPortal Setup --- #
matrixportal = MatrixPortal(
    status_neopixel=board.NEOPIXEL,
    debug=True,
    esp=radio,
    external_spi=spi,
)

pool = adafruit_connection_manager.get_radio_socketpool(radio)
ssl_context = adafruit_connection_manager.get_radio_ssl_context(radio)

# --- Connect to WiFi --- #
print("Connecting to WiFi...")
while not radio.is_connected:
    try:
        radio.connect_AP(secrets["CIRCUITPY_WIFI_SSID"], secrets["CIRCUITPY_WIFI_PASSWORD"])
    except OSError as e:
        print(f"WiFi connect failed, retrying: {e}")
        time.sleep(2)
print(f"WiFi connected, IP: {radio.ipv4_address}")

if DEBUG_WIFI:
    wifi_tests(radio, secrets)

# Create a display group for shapes and text
group = displayio.Group()

# Set the display to show the group
color_bitmap = displayio.Bitmap(64, 32, 1)
color_palette = displayio.Palette(1)
color_palette[0] = 0x000000  # Black color
bg_sprite = displayio.TileGrid(color_bitmap, x=0, y=0, pixel_shader=color_palette)
group.append(bg_sprite)

# --- Status display helper --- #
def show_status(text, color=0xFFFFFF):
    """Show a short status message on the matrix during boot/error."""
    from adafruit_display_text.label import Label
    from render import get_font
    while len(group) > 0:
        group.pop()
    font = get_font()
    if font:
        label = Label(font, text=text, color=color, x=1, y=8)
        group.append(label)
    matrixportal.display.root_group = group
    print(text)

# --- Function to Set Payload --- #
_last_message = None

def setDisplay(message, group):
    global _last_message
    if message == _last_message:
        return
    _last_message = message
    temp_payload = json.loads(message)

    # Free old display objects before allocating new ones — avoids peak where
    # both old and new sets are live simultaneously (OOM with large payloads).
    while len(group) > 0:
        group.pop()
    gc.collect()

    for item in temp_payload["data"]:
        if item["t"] == "s":
            shape = renderShape(item)
            if shape is not None:
                group.append(shape)
        elif item["t"] == "t":
            group.append(renderText(item))
        elif item["t"] == "i":
            print("Image found")
            group.append(renderImage(item))
        else:
            print("Unsupported type found")

# --- MQTT Callback Functions --- #
def connected(client, userdata, flags, rc):
    print(f"Connected to MQTT broker with result code {rc}")
    client.subscribe(mqtt_topic, 0)

def disconnected(client, userdata, rc):
    print("Disconnected from MQTT broker")

def message_received(client, topic, message):
    print(f"Received message on topic {topic}: {message}")
    try:
        setDisplay(message, group)
    except Exception as e:
        print(f"Error in message_received: {e}")

def subscribed(client, userdata, mid, granted_qos):
    print("Subscribed to topic")

# --- Derive client_id from MAC address --- #
mac = radio.MAC_address
client_id = "tinytron-" + "".join([f"{b:02x}" for b in mac])

# --- Set Up MQTT Client --- #
mqtt_client = MQTT.MQTT(
    broker=mqtt_broker,
    port=mqtt_port,
    client_id=client_id,
    username=secrets["mqtt_username"],
    password=secrets["mqtt_password"],
    keep_alive=30,
    is_ssl=False,
    socket_pool=pool,
    ssl_context=ssl_context
)

# Setup callbacks
mqtt_client.on_connect = connected
mqtt_client.on_disconnect = disconnected
mqtt_client.on_message = message_received
mqtt_client.on_subscribe = subscribed

# Set root_group so show_status works during connect attempts
matrixportal.display.root_group = group

# --- Network sanity check --- #
for label, host in [("Google", "8.8.8.8"), ("Broker", "144.202.63.142")]:
    show_status(f"Ping {label}...", color=0x4444FF)
    try:
        ping_ms = radio.ping(host)
        print(f"Ping {label} ({host}): {ping_ms} ms")
        color = 0x00FF00 if ping_ms < 65535 else 0xFF0000
        show_status(f"{label}: {ping_ms}ms", color=color)
    except Exception as e:
        print(f"Ping {label} failed: {e}")
        show_status(f"{label}: FAIL", color=0xFF0000)
    time.sleep(2)

# --- Initial connect with retry --- #
RETRY_DELAY = 10
attempt = 0
while True:
    attempt += 1
    show_status(f"MQTT {attempt}...", color=0xFFCC00)
    try:
        mqtt_client.connect()
        show_status("Connected!", color=0x00FF00)
        time.sleep(1)
        break
    except Exception as e:
        print(f"Connect failed: {e}")
        show_status(f"ERR retry {attempt}", color=0xFF0000)
        # Reset the ESP32 co-processor to clear any bad socket state
        try:
            radio.reset()
            time.sleep(2)
        except Exception as re:
            print(f"Radio reset failed: {re}")
        time.sleep(RETRY_DELAY)

# --- Main Loop --- #
loop_count = 0
reconnect_attempt = 0
MAX_RECONNECT_ATTEMPTS = 5
RECONNECT_BASE_DELAY = 10  # seconds

while True:
    try:
        mqtt_client.loop(1)
        reconnect_attempt = 0  # reset on successful loop
    except Exception as e:
        print(f"MQTT loop error: {e}")
        gc.collect()
        print(f"Free memory after GC: {gc.mem_free()} bytes")
        reconnect_attempt += 1

        # Packet corruption or OOM — reconnect() on the same socket won't recover.
        error_str = str(e)
        needs_hard_reset = (
            "exceeds remaining length" in error_str
            or "Topic length" in error_str
            or "memory allocation failed" in error_str
        )

        if needs_hard_reset or reconnect_attempt > MAX_RECONNECT_ATTEMPTS:
            print(f"Too many reconnect failures ({reconnect_attempt}), resetting radio and reconnecting from scratch...")
            show_status("RESET...", color=0xFF4400)
            reconnect_attempt = 0
            try:
                radio.reset()
                time.sleep(3)
                radio.connect_AP(secrets["CIRCUITPY_WIFI_SSID"], secrets["CIRCUITPY_WIFI_PASSWORD"])
            except Exception as we:
                print(f"WiFi reconnect failed: {we}")
                time.sleep(10)
            try:
                mqtt_client.connect()
                show_status("Connected!", color=0x00FF00)
                time.sleep(1)
            except Exception as ce:
                print(f"MQTT reconnect after radio reset failed: {ce}")
                show_status("MQTT FAIL", color=0xFF0000)
                time.sleep(30)
        else:
            delay = RECONNECT_BASE_DELAY * reconnect_attempt
            print(f"Attempting reconnect (attempt {reconnect_attempt}/{MAX_RECONNECT_ATTEMPTS}, waiting {delay}s)...")
            show_status(f"Retry {reconnect_attempt}/{MAX_RECONNECT_ATTEMPTS}", color=0xFFCC00)
            time.sleep(delay)
            try:
                mqtt_client.reconnect()
                print("Reconnected.")
                show_status("Connected!", color=0x00FF00)
                time.sleep(1)
            except Exception as re:
                print(f"Reconnect failed: {re}")

    # Periodic GC and memory monitoring
    if loop_count % 100 == 0:
        gc.collect()
    if loop_count % 1000 == 0:
        print(f"Free memory: {gc.mem_free()} bytes")
    loop_count += 1

    time.sleep(0.05)
