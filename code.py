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
from utils import wifi_tests
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

wifi_tests(radio, secrets)

# Create a display group for shapes and text
group = displayio.Group()

# Set the display to show the group
color_bitmap = displayio.Bitmap(64, 32, 1)
color_palette = displayio.Palette(1)
color_palette[0] = 0x000000  # Black color
bg_sprite = displayio.TileGrid(color_bitmap, x=0, y=0, pixel_shader=color_palette)
group.append(bg_sprite)

# # Load the sprite sheet (bitmap)
# bitmap = displayio.OnDiskBitmap("/sd/test32.bmp")

# # Create the sprite TileGrid
# sprite = displayio.TileGrid(
#     bitmap,
#     pixel_shader=bitmap.pixel_shader,
#     # width=1,
#     # height=1,
#     # tile_width=16,
#     # tile_height=16,
#     # default_tile=0,
# )

# sprite_group = displayio.Group()
# sprite_group.append(sprite)

# # Create a Group to hold the sprite and castle
# group = displayio.Group()

# # Add the sprite and castle to the group
# group.append(sprite_group)

# --- Function to Set Payload --- #
def setDisplay(message, group):
    temp_payload = json.loads(message)
    
    # Create a new display group inside this function to handle the payload
    formated_array = []
    for item in temp_payload["data"]:
        if item["type"] == "shape":
            shape = renderShape(item)
            formated_array.append(shape)
        elif item["type"] == "text":
            label = renderText(item)
            formated_array.append(label)
        elif item["type"] == "image":
            print("Image found")
            sprite_group = renderImage(item)
            formated_array.append(sprite_group)
        else:
            print("Unsupported type found")

    while len(group) > 0  :
        group.pop()
    for item in formated_array:
        group.append(item)

# --- MQTT Callback Functions --- #
def connected(client, userdata, flags, rc):
    print(f"Connected to MQTT broker with result code {rc}")
    client.subscribe(mqtt_topic, 0)  # Subscribe to the topic you're interested in
    client.publish(mqtt_topic, "Hello from CircuitPython!")

def disconnected(client, userdata, rc):
    print("Disconnected from MQTT broker")

def message_received(client, topic, message):
    print(f"Received message on topic {topic}: {message}")
    try:
        setDisplay(message, group)
    except:
        print("Message is not in JSON format")

def subscribed(client, userdata, mid, granted_qos):
    print("Subscribed to topic")

# --- Set Up MQTT Client --- #
mqtt_client = MQTT.MQTT(
    broker=mqtt_broker,
    port=mqtt_port,
    client_id="user",
    is_ssl=False,
    socket_pool=pool,
    ssl_context=ssl_context
)

# Setup callbacks
mqtt_client.on_connect = connected
mqtt_client.on_disconnect = disconnected
mqtt_client.on_message = message_received
mqtt_client.on_subscribe = subscribed

print("Attempting to connect to %s" % mqtt_client.broker)
# --- Connect to MQTT Broker --- #
print(mqtt_client.is_connected())
mqtt_client.connect()
print(mqtt_client.is_connected())
print("Connected to MQTT broker, waiting for messages...")


# --- Main Loop --- #
refresh_time = None
while True:
#    # --- MQTT Loop --- #
    mqtt_client.loop(1)
    matrixportal.display.root_group = group
    # --- Update Display --- #

    if (not refresh_time) or (time.monotonic() - refresh_time) > 60:  # Refresh every 30 seconds
        try:
            refresh_time = time.monotonic()

        except RuntimeError as e:
            print("Unable to obtain time from the server, retrying - ", e)
            continue

    time.sleep(0.05)
