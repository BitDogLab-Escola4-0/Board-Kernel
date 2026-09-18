# MicroPython SH1107 OLED driver, I2C interface
# Compatible with 128x128, 64x128, and 128x64 monochrome OLED displays

from micropython import const
import framebuf

# Register definitions
SET_CONTRAST        = const(0x81)
SET_ENTIRE_ON       = const(0xA4)
SET_NORM_INV        = const(0xA6)
SET_DISP            = const(0xAE)
SET_DCDC_MODE       = const(0xAD)
SET_MEM_MODE        = const(0x20)
SET_PAGE_ADDR       = const(0xB0)
SET_COL_LO_ADDR     = const(0x00)
SET_COL_HI_ADDR     = const(0x10)
SET_DISP_START_LINE = const(0xDC)
SET_SEG_REMAP       = const(0xA0)
SET_MUX_RATIO       = const(0xA8)
SET_COM_OUT_DIR     = const(0xC0)
SET_DISP_OFFSET     = const(0xD3)
SET_DISP_CLK_DIV    = const(0xD5)
SET_PRECHARGE       = const(0xD9)
SET_VCOM_DESEL      = const(0xDB)


class SH1107(framebuf.FrameBuffer):
    def __init__(self, width=128, height=128, external_vcc=False):
        self.width = width
        self.height = height
        self.external_vcc = external_vcc
        self.pages = self.height // 8
        self.buffer = bytearray(self.pages * self.width)
        super().__init__(self.buffer, self.width, self.height, framebuf.MONO_VLSB)
        self.init_display()

    def init_display(self):
        for cmd in (
            SET_DISP | 0x00,           # Display OFF
            SET_MEM_MODE,              # Page Addressing Mode (0x20)
            SET_DISP_START_LINE, 0x00, # Start Line 0
            SET_SEG_REMAP | 0x00,      # Normal segment remap (0xA0)
            SET_COM_OUT_DIR | 0x00,    # Normal scan direction (0xC0)
            SET_MUX_RATIO, self.height - 1, # Multiplex ratio (127 for 128 lines)
            SET_DISP_OFFSET, 0x00 if self.width == self.height else 0x60,
            SET_DISP_CLK_DIV, 0x50,    # Internal clock divider
            SET_PRECHARGE, 0x22 if self.external_vcc else 0xF1,
            SET_VCOM_DESEL, 0x35,      # 0.77 * Vref
            SET_DCDC_MODE, 0x81,       # DC-DC enable (charge pump on)
            SET_CONTRAST, 0x4F,        # Contrast
            SET_ENTIRE_ON | 0x00,      # Output follows RAM contents
            SET_NORM_INV | 0x00,       # Normal (not inverted)
            SET_DISP | 0x01,           # Display ON
        ):
            self.write_cmd(cmd)
        self.fill(0)
        self.show()

    def poweroff(self):
        self.write_cmd(SET_DISP | 0x00)

    def poweron(self):
        self.write_cmd(SET_DISP | 0x01)

    def contrast(self, contrast):
        self.write_cmd(SET_CONTRAST)
        self.write_cmd(contrast)

    def invert(self, invert):
        self.write_cmd(SET_NORM_INV | (invert & 1))

    def rotate(self, rotate_180=True):
        """Rotate display 180 degrees if True, normal if False."""
        if rotate_180:
            self.write_cmd(SET_SEG_REMAP | 0x01)
            self.write_cmd(SET_COM_OUT_DIR | 0x08)
        else:
            self.write_cmd(SET_SEG_REMAP | 0x00)
            self.write_cmd(SET_COM_OUT_DIR | 0x00)

    def show(self):
        for page in range(self.pages):
            self.write_cmd(SET_PAGE_ADDR | page)
            self.write_cmd(SET_COL_LO_ADDR | 0x00)
            self.write_cmd(SET_COL_HI_ADDR | 0x00)
            offset = page * self.width
            self.write_data(self.buffer[offset : offset + self.width])


class SH1107_I2C(SH1107):
    def __init__(self, width=128, height=128, i2c=None, addr=0x3C, external_vcc=False):
        self.i2c = i2c
        self.addr = addr
        self.temp = bytearray(2)
        self.write_list = [b"\x40", None]  # Co=0, D/C#=1
        super().__init__(width, height, external_vcc)

    def write_cmd(self, cmd):
        self.temp[0] = 0x80  # Co=1, D/C#=0
        self.temp[1] = cmd
        self.i2c.writeto(self.addr, self.temp)

    def write_data(self, buf):
        self.write_list[1] = buf
        self.i2c.writevto(self.addr, self.write_list)
