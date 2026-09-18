#Imports
from machine import Pin, PWM, I2C, ADC
import neopixel
import time
from lib.sh1107 import SH1107_I2C

# Constants:
# Width and Height of OLED Display
SCREEN_WIDTH = 128
SCREEN_HEIGHT = 128

# OLED Display constant used in snake_game
SEGMENT_WIDTH = 8
SEGMENT_PIXELS = 8
SEGMENTS_HIGH = int(SCREEN_HEIGHT / SEGMENT_PIXELS)  # 128 / 8 = 16 height segments
SEGMENTS_WIDE = int(SCREEN_WIDTH / SEGMENT_PIXELS)   # 128 / 8 = 16 width segments

# Valid range for grid coords (used to place the food)
VALID_RANGE = [[int(i / SEGMENTS_HIGH), i % SEGMENTS_HIGH] 
               for i in range(SEGMENTS_WIDE * SEGMENTS_HIGH - 1)]

# Number of leds from Neopixel
NUM_LEDS = 25

# Function to clear OLED
def clear_oled():
    oled.fill(0)
    oled.show()

# Function to update and display text on OLED
def update_oled(lines):
    oled.fill(0)
    max_lines = SCREEN_HEIGHT // 8
    for i, line in enumerate(lines):
        if i < max_lines:
            oled.text(line, 0, i * 8)
    oled.show()

# Components initialization:

# OLED Display (128x128)
i2c = I2C(1, sda=Pin(2), scl=Pin(3), freq=400000)

# Auto-detect I2C address (0x3C or 0x3D)
oled_addr = 0x3C
try:
    devices = i2c.scan()
    if 0x3D in devices:
        oled_addr = 0x3D
    elif 0x3C in devices:
        oled_addr = 0x3C
except Exception as e:
    print("Warning scanning I2C:", e)

oled = SH1107_I2C(SCREEN_WIDTH, SCREEN_HEIGHT, i2c, addr=oled_addr)
oled.fill(0)
oled.show()

# RGB Led (PWM)
led_r = PWM(Pin(12)); led_g = PWM(Pin(13)); led_b = PWM(Pin(11))
led_r.freq(1000); led_g.freq(1000); led_b.freq(1000)
led_r.duty_u16(0); led_g.duty_u16(0); led_b.duty_u16(0) # Turn off

# Buzzers (PWM)
buzzer = PWM(Pin(21)); buzzer2 = PWM(Pin(10))
buzzer.duty_u16(0); buzzer2.duty_u16(0) # Turn off

# Turns off all three channels of the onboard RGB LED
def rgb_off():
    led_r.duty_u16(0)
    led_g.duty_u16(0)
    led_b.duty_u16(0)


# Plays a tone on the main buzzer
def play_tone(frequency, duration_s=0.1, volume=500):
    global buzzer
    
    # Set frequency and duty cycle (volume)
    buzzer.freq(frequency)
    buzzer.duty_u16(volume)
    
    # Wait for the duration of the tone
    time.sleep(duration_s)
    
    # Stop the sound (set volume to 0)
    buzzer.duty_u16(0)


# Buttons A and B (Input)
button_a = Pin(5, Pin.IN, Pin.PULL_UP)
button_b = Pin(6, Pin.IN, Pin.PULL_UP)
# button_c =

# Joystick Analog (ADC) and Button (Input)
adc_vrx = ADC(Pin(26)); adc_vry = ADC(Pin(27))
joystick_button = Pin(22, Pin.IN, Pin.PULL_UP)

# Function to map a value from one range to another
def map_value(value, in_min, in_max, out_min, out_max):
    return (value - in_min) * (out_max - out_min) // (in_max - in_min) + out_min

# Joystick direction functions (using raw u16 readings from 0 to 65535)
def joy_up():
    # X-axis (Vertical) low value means Up
    return adc_vrx.read_u16() < 16384

def joy_down():
    # X-axis (Vertical) high value means Down
    return adc_vrx.read_u16() > 49152

def joy_left():
    # Y-axis (Horizontal) high value means Left
    return adc_vry.read_u16() > 49152

def joy_right():
    # Y-axis (Horizontal) low value means Right
    return adc_vry.read_u16() < 16384

# Led onboard (Pico W)
led = Pin("LED", Pin.OUT); led.off()

print("(✓) hardware.py")
