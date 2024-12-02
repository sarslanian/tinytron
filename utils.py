from adafruit_esp32spi import adafruit_esp32spi

def hex_to_rgb_bytes(hex_color):
    # Strip the "0x" prefix and convert to an integer
    hex_color = hex_color[2:]  # Remove the '0x' prefix
    rgb = int(hex_color, 16)

    # Extract the red, green, and blue components (each is an integer between 0 and 255)
    red = (rgb >> 16) & 0xFF
    green = (rgb >> 8) & 0xFF
    blue = rgb & 0xFF

    # Return as a tuple of RGB bytes
    return (red, green, blue)


def wifi_tests(radio, secrets):
    if radio.status == adafruit_esp32spi.WL_IDLE_STATUS:
        print("ESP32 found and in idle mode")
    print("Firmware vers.", radio.firmware_version)
    print("MAC addr:", ":".join("%02X" % byte for byte in radio.MAC_address))

    for ap in radio.scan_networks():
        print("\t%-23s RSSI: %d" % (ap.ssid, ap.rssi))

    print("Connecting to AP...")
    while not radio.is_connected:
        try:
            radio.connect_AP(secrets["CIRCUITPY_WIFI_SSID"], secrets["CIRCUITPY_WIFI_PASSWORD"])
        except OSError as e:
            print("could not connect to AP, retrying: ", e)
            continue
    print("Connected to", radio.ap_info.ssid, "\tRSSI:", radio.ap_info.rssi)
    print("My IP address is", radio.ipv4_address)
    print(
        "IP lookup adafruit.com: %s" % radio.pretty_ip(radio.get_host_by_name("adafruit.com"))
    )
    print("Ping google.com: %d ms" % radio.ping("google.com"))