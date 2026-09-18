# MicroPython SSD1327 OLED I2C driver
# Reference: https://github.com/mcauser/micropython-ssd1327

from micropython import const
import framebuf

# Commands
SET_COL_ADDR          = const(0x15)
SET_SCROLL_DEACTIVATE = const(0x2E)
SET_ROW_ADDR          = const(0x75)
SET_CONTRAST          = const(0x81)
SET_SEG_REMAP         = const(0xA0)
SET_DISP_START_LINE   = const(0xA1)
SET_DISP_OFFSET       = const(0xA2)
SET_DISP_MODE         = const(0xA4)  # 0xA4 normal, 0xA7 inverted
SET_MUX_RATIO         = const(0xA8)
SET_FN_SELECT_A       = const(0xAB)
SET_DISP              = const(0xAE)  # 0xAE power off, 0xAF power on
SET_PHASE_LEN         = const(0xB1)
SET_DISP_CLK_DIV      = const(0xB3)
SET_SECOND_PRECHARGE  = const(0xB6)
SET_GRAYSCALE_LINEAR  = const(0xB9)
SET_PRECHARGE         = const(0xBC)
SET_VCOM_DESEL        = const(0xBE)
SET_FN_SELECT_B       = const(0xD5)
SET_COMMAND_LOCK      = const(0xFD)

REG_CMD  = const(0x80)
REG_DATA = const(0x40)


class SSD1327:
    def __init__(self, width=128, height=128):
        self.width = width
        self.height = height
        self.buffer = bytearray(self.width * self.height // 2)
        self.framebuf = framebuf.FrameBuffer(self.buffer, self.width, self.height, framebuf.GS4_HMSB)

        self.col_addr = ((128 - self.width) // 4, 63 - ((128 - self.width) // 4))
        self.row_addr = (0, self.height - 1)
        self.offset = 128 - self.height

        self.poweron()
        self.init_display()

    def init_display(self):
        for cmd in (
            SET_COMMAND_LOCK, 0x12,
            SET_DISP,
            SET_DISP_START_LINE, 0x00,
            SET_DISP_OFFSET, self.offset,
            SET_SEG_REMAP, 0x51,
            SET_MUX_RATIO, self.height - 1,
            SET_FN_SELECT_A, 0x01,
            SET_PHASE_LEN, 0x51,
            SET_DISP_CLK_DIV, 0x01,
            SET_PRECHARGE, 0x08,
            SET_VCOM_DESEL, 0x07,
            SET_SECOND_PRECHARGE, 0x01,
            SET_FN_SELECT_B, 0x62,
            SET_GRAYSCALE_LINEAR,
            SET_CONTRAST, 0x7F,
            SET_DISP_MODE,
            SET_COL_ADDR, self.col_addr[0], self.col_addr[1],
            SET_ROW_ADDR, self.row_addr[0], self.row_addr[1],
            SET_SCROLL_DEACTIVATE,
            SET_DISP | 0x01,
        ):
            self.write_cmd(cmd)
        self.fill(0)
        self.show()

    def poweroff(self):
        self.write_cmd(SET_FN_SELECT_A)
        self.write_cmd(0x00)
        self.write_cmd(SET_DISP)

    def poweron(self):
        self.write_cmd(SET_FN_SELECT_A)
        self.write_cmd(0x01)
        self.write_cmd(SET_DISP | 0x01)

    def contrast(self, contrast):
        self.write_cmd(SET_CONTRAST)
        self.write_cmd(contrast)

    def invert(self, invert):
        self.write_cmd(SET_DISP_MODE | (invert & 1) << 1 | (invert & 1))

    def show(self):
        self.write_cmd(SET_COL_ADDR)
        self.write_cmd(self.col_addr[0])
        self.write_cmd(self.col_addr[1])
        self.write_cmd(SET_ROW_ADDR)
        self.write_cmd(self.row_addr[0])
        self.write_cmd(self.row_addr[1])
        self.write_data(self.buffer)

    def fill(self, col):
        self.framebuf.fill(15 if col else 0)

    def pixel(self, x, y, col=1):
        self.framebuf.pixel(x, y, 15 if col else 0)

    def line(self, x1, y1, x2, y2, col=1):
        self.framebuf.line(x1, y1, x2, y2, 15 if col else 0)

    def rect(self, x, y, w, h, col=1):
        self.framebuf.rect(x, y, w, h, 15 if col else 0)

    def fill_rect(self, x, y, w, h, col=1):
        self.framebuf.fill_rect(x, y, w, h, 15 if col else 0)

    def text(self, string, x, y, col=1):
        self.framebuf.text(string, x, y, 15 if col else 0)


class SSD1327_I2C(SSD1327):
    def __init__(self, width=128, height=128, i2c=None, addr=0x3C):
        self.i2c = i2c
        self.addr = addr
        self.cmd_arr = bytearray([REG_CMD, 0])
        self.data_list = [bytes((REG_DATA,)), None]
        super().__init__(width, height)

    def write_cmd(self, cmd):
        self.cmd_arr[1] = cmd
        self.i2c.writeto(self.addr, self.cmd_arr)

    def write_data(self, data_buf):
        self.data_list[1] = data_buf
        self.i2c.writevto(self.addr, self.data_list)
