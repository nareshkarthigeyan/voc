import board
import busio
import digitalio
from PIL import Image, ImageDraw, ImageFont
import adafruit_rgb_display.st7735 as st7735

# SPI setup
spi = busio.SPI(clock=board.SCK, MOSI=board.MOSI)
tft_dc = digitalio.DigitalInOut(board.D24)
tft_cs = digitalio.DigitalInOut(board.D27)
tft_rst = digitalio.DigitalInOut(board.D25)

# Correct ST7735 variant
disp = st7735.ST7735R(
    spi,
    cs=tft_cs,
    dc=tft_dc,
    rst=tft_rst,
    width=128,
    height=160,
    bgr=True  # **IMPORTANT: specify BGR mode**
)

disp.rotation = 0  # **Set rotation to 0 first to avoid swap**

print("disp.width:", disp.width)
print("disp.height:", disp.height)

# Create image
image = Image.new("RGB", (disp.width, disp.height), "black")
draw = ImageDraw.Draw(image)
font = ImageFont.load_default()
draw.text((10, 10), "Hello Display!", font=font, fill=(255, 255, 255))

# Force correct mode
image = image.convert("RGB")

# Final strict crop
image = image.crop((0, 0, disp.width, disp.height))
print("Image size after crop:", image.size)

# Display
disp.image(image)
print("✅ Display test done")
