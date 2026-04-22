#!/usr/bin/env python3
import sys, time, argparse, threading, datetime, os, re, platform, tty, termios, select

try:
    import serial
    from serial.tools import list_ports
except ImportError:
    print("  pip3 install pyserial  and try again :c")
    sys.exit(1)

_sys = platform.system()
ON_MAC = _sys == "Darwin"

def platform_name():
    if ON_MAC:
        ver = platform.mac_ver()[0]
        return f"macOS {ver}" if ver else "macOS"
    try:
        import distro
        return distro.name(pretty=True) or f"Linux {platform.release()}"
    except ImportError:
        return f"Linux {platform.release()}"

def port_hint():
    return "/dev/cu.usbmodem0" if ON_MAC else "/dev/ttyUSB0  or  /dev/ttyACM0"

def perm_hint(dev):
    if not ON_MAC:
        return f"  sudo chmod a+rw {dev}  (quick fix)  |  sudo usermod -aG dialout $USER  (permanent)"
    return "  check System Settings > Privacy & Security for a blocked driver"

R        = "\033[0m"
BOLD     = "\033[1m"
DIM      = "\033[2m"
RED      = "\033[31m"
GREEN    = "\033[32m"
YELLOW   = "\033[33m"
BLUE     = "\033[34m"
MAGENTA  = "\033[35m"
CYAN     = "\033[36m"
WHITE    = "\033[37m"
BRED     = "\033[91m"
BGREEN   = "\033[92m"
BYELLOW  = "\033[93m"
BBLUE    = "\033[94m"
BMAGENTA = "\033[95m"
BCYAN    = "\033[96m"
BWHITE   = "\033[97m"
BGRAY    = "\033[90m"
BG_RED   = "\033[41m"
CLR_LINE = "\033[2K\r"

# the following matrix is ai-gen

BOARDS = {
    (0x2E8A, 0x0003): ("RP2040",  "Pico [BOOT]",             BCYAN),
    (0x2E8A, 0x0004): ("RP2040",  "PicoProbe",               BCYAN),
    (0x2E8A, 0x0005): ("RP2040",  "Pico [MicroPython]",      BCYAN),
    (0x2E8A, 0x0009): ("RP2040",  "Pico [SDK CDC]",          BCYAN),
    (0x2E8A, 0x000A): ("RP2040",  "Pico [SDK CDC]",          BCYAN),
    (0x2E8A, 0x000B): ("RP2040",  "Pico [CircuitPython]",    BCYAN),
    (0x2E8A, 0x000C): ("RP2040",  "Pico [CDC REPL]",         BCYAN),
    (0x2E8A, 0x000F): ("RP2350",  "Pico 2 [BOOT]",           BBLUE),
    (0x2E8A, 0x0010): ("RP2350",  "Pico 2 [MicroPython]",    BBLUE),
    (0x2E8A, 0x0011): ("RP2350",  "Pico 2 [CircuitPython]",  BBLUE),
    (0x2E8A, 0x0012): ("RP2350",  "Pico 2 [SDK CDC]",        BBLUE),
    (0x2E8A, None):   ("RP2040",  "Raspberry Pi Board",      BCYAN),

    (0x239A, 0x0001): ("Adafruit",  "CDC Bootloader",         BMAGENTA),
    (0x239A, 0x000F): ("SAMD21",    "Feather M0",             BMAGENTA),
    (0x239A, 0x0013): ("SAMD21",    "Feather M0 Express",     BMAGENTA),
    (0x239A, 0x0018): ("SAMD21",    "Circuit Playground Exp", BMAGENTA),
    (0x239A, 0x001B): ("SAMD21",    "Feather M0 Adalogger",   BMAGENTA),
    (0x239A, 0x001D): ("SAMD21",    "Feather M0 Basic",       BMAGENTA),
    (0x239A, 0x001F): ("SAMD21",    "ItsyBitsy M0",           BMAGENTA),
    (0x239A, 0x0021): ("SAMD21",    "Metro M0 Express",       BMAGENTA),
    (0x239A, 0x0023): ("SAMD21",    "Gemma M0",               BMAGENTA),
    (0x239A, 0x0025): ("SAMD21",    "Trinket M0",             BMAGENTA),
    (0x239A, 0x0027): ("SAMD21",    "QT Py M0",               BMAGENTA),
    (0x239A, 0x8019): ("SAMD51",    "Feather M4 Express",     BMAGENTA),
    (0x239A, 0x801B): ("SAMD51",    "ItsyBitsy M4",           BMAGENTA),
    (0x239A, 0x801D): ("SAMD51",    "Metro M4 Express",       BMAGENTA),
    (0x239A, 0x8020): ("SAMD51",    "Grand Central M4",       BMAGENTA),
    (0x239A, 0x8022): ("SAMD51",    "PyPortal",               BMAGENTA),
    (0x239A, 0x8031): ("nRF52840",  "Feather nRF52840",       BMAGENTA),
    (0x239A, 0x8040): ("RP2040",    "Feather RP2040",         BMAGENTA),
    (0x239A, 0x80F4): ("RP2040",    "Pico [Adafruit CP]",     BMAGENTA),
    (0x239A, 0x80F6): ("RP2040",    "KB2040",                 BMAGENTA),
    (0x239A, 0x80F8): ("RP2040",    "QT Py RP2040",           BMAGENTA),
    (0x239A, 0x80FA): ("RP2040",    "ItsyBitsy RP2040",       BMAGENTA),
    (0x239A, 0x80FC): ("RP2040",    "Feather RP2040",         BMAGENTA),
    (0x239A, 0x80FE): ("RP2040",    "Trinkey RP2040",         BMAGENTA),
    (0x239A, 0x8100): ("RP2040",    "QT Py RP2040",           BMAGENTA),
    (0x239A, None):   ("Adafruit",  "Adafruit Board",         BMAGENTA),

    (0x303A, 0x0002): ("ESP32-S2",  "ESP32-S2 [JTAG/Serial]", BYELLOW),
    (0x303A, 0x1001): ("ESP32-C3",  "ESP32-C3 [JTAG/Serial]", BYELLOW),
    (0x303A, 0x1002): ("ESP32-S3",  "ESP32-S3 [JTAG/Serial]", BYELLOW),
    (0x303A, 0x4001): ("ESP32-S2",  "ESP32-S2 [TinyUSB CDC]", BYELLOW),
    (0x303A, 0x4002): ("ESP32-S3",  "ESP32-S3 [TinyUSB CDC]", BYELLOW),
    (0x303A, 0x80D4): ("ESP32-S2",  "ESP32-S2 [CircuitPy]",   BYELLOW),
    (0x303A, 0x80E8): ("ESP32-S3",  "ESP32-S3 [CircuitPy]",   BYELLOW),
    (0x303A, None):   ("ESP32",     "Espressif Board",         BYELLOW),

    (0x10C4, 0xEA60): ("CP2102",   "Serial Adapter [CP2102]", YELLOW),
    (0x10C4, 0xEA61): ("CP2104",   "Serial Adapter [CP2104]", YELLOW),
    (0x10C4, 0xEA70): ("CP2105",   "Serial Adapter [CP2105]", YELLOW),
    (0x10C4, 0xEA71): ("CP2108",   "Serial Adapter [CP2108]", YELLOW),
    (0x10C4, 0xEA80): ("CP2110",   "Serial Adapter [CP2110]", YELLOW),
    (0x10C4, None):   ("CP210x",   "Serial Adapter",          YELLOW),

    (0x1A86, 0x7522): ("CH340",    "Serial Adapter [CH340]",  YELLOW),
    (0x1A86, 0x7523): ("CH340",    "Serial Adapter [CH340]",  YELLOW),
    (0x1A86, 0x5523): ("CH341",    "Serial Adapter [CH341]",  YELLOW),
    (0x1A86, 0x55D4): ("CH9102",   "Serial Adapter [CH9102]", YELLOW),
    (0x1A86, 0xAAF0): ("CH347",    "Serial Adapter [CH347]",  YELLOW),
    (0x1A86, None):   ("WCH",      "Serial Adapter",          YELLOW),

    (0x0403, 0x6001): ("FT232RL",  "FTDI Adapter [FT232RL]",  MAGENTA),
    (0x0403, 0x6010): ("FT2232H",  "FTDI Adapter [FT2232H]",  MAGENTA),
    (0x0403, 0x6011): ("FT4232H",  "FTDI Adapter [FT4232H]",  MAGENTA),
    (0x0403, 0x6014): ("FT232H",   "FTDI Adapter [FT232H]",   MAGENTA),
    (0x0403, 0x6015): ("FT231X",   "FTDI Adapter [FT231X]",   MAGENTA),
    (0x0403, None):   ("FTDI",     "Serial Adapter",          MAGENTA),

    (0x067B, 0x2303): ("PL2303",   "Serial Adapter [PL2303]", WHITE),
    (0x067B, 0x23A3): ("PL2303HX", "Serial Adapter [PL2303HX]", WHITE),
    (0x067B, None):   ("Prolific", "Serial Adapter",          WHITE),

    (0x2886, 0x0044): ("SAMD21",   "XIAO SAMD21",             BGREEN),
    (0x2886, 0x0045): ("SAMD21",   "Seeeduino XIAO",          BGREEN),
    (0x2886, 0x802F): ("SAMD51",   "Wio Terminal",            BGREEN),
    (0x2886, 0x8044): ("SAMD21",   "XIAO SAMD21 [CP]",        BGREEN),
    (0x2886, 0x8050): ("RP2040",   "XIAO RP2040",             BGREEN),
    (0x2886, 0x8052): ("nRF52840", "XIAO nRF52840",           BGREEN),
    (0x2886, 0x8055): ("ESP32-S3", "XIAO ESP32-S3",           BGREEN),
    (0x2886, 0x8056): ("ESP32-C3", "XIAO ESP32-C3",           BGREEN),
    (0x2886, 0x805A): ("RP2350",   "XIAO RP2350",             BGREEN),
    (0x2886, None):   ("Seeed",    "Seeed Studio Board",      BGREEN),

    (0x1B4F, 0x0013): ("SAMD21",   "SparkFun RedBoard Turbo", BRED),
    (0x1B4F, 0x0016): ("SAMD21",   "SparkFun SAMD21 Mini",    BRED),
    (0x1B4F, 0x0017): ("SAMD21",   "SparkFun SAMD21 Dev",     BRED),
    (0x1B4F, 0x002B): ("RP2040",   "SparkFun Thing Plus RP2040", BRED),
    (0x1B4F, 0x8D22): ("SAMD21",   "SparkFun Pro Micro M0",   BRED),
    (0x1B4F, 0x8D23): ("SAMD21",   "SparkFun Qwiic Micro",    BRED),
    (0x1B4F, None):   ("SparkFun", "SparkFun Board",          BRED),

    (0x2341, 0x0001): ("ATmega328", "Arduino Uno [DFU]",      BCYAN),
    (0x2341, 0x0010): ("ATmega328", "Arduino Mega",           BCYAN),
    (0x2341, 0x0036): ("ATmega328", "Arduino Leonardo Bootloader", BCYAN),
    (0x2341, 0x0037): ("ATmega32U4","Arduino Micro Bootloader",BCYAN),
    (0x2341, 0x003D): ("SAMD21",   "Arduino Zero",            BCYAN),
    (0x2341, 0x003E): ("SAMD21",   "Arduino Zero [native]",   BCYAN),
    (0x2341, 0x0042): ("ATmega16U2","Arduino Mega 2560",      BCYAN),
    (0x2341, 0x0043): ("ATmega16U2","Arduino Uno R3",         BCYAN),
    (0x2341, 0x0044): ("ATmega16U2","Arduino Mega ADK",       BCYAN),
    (0x2341, 0x0049): ("SAMD21",   "Arduino Zero [prog]",     BCYAN),
    (0x2341, 0x004D): ("SAMD21",   "Arduino MKR1000",         BCYAN),
    (0x2341, 0x804D): ("SAMD21",   "Arduino MKR1000 [CDC]",   BCYAN),
    (0x2341, 0x8036): ("ATmega32U4","Arduino Leonardo",       BCYAN),
    (0x2341, 0x8037): ("ATmega32U4","Arduino Micro",          BCYAN),
    (0x2341, 0x8054): ("SAMD51",   "Arduino Metro M4",        BCYAN),
    (0x2341, 0x824D): ("SAMD21",   "Arduino MKRZero",         BCYAN),
    (0x2341, None):   ("Arduino",  "Arduino Board",           BCYAN),

    (0x16C0, 0x0483): ("Teensy",   "Teensy Serial",           BYELLOW),
    (0x16C0, 0x04D0): ("Teensy",   "Teensy Keyboard+Serial",  BYELLOW),
    (0x16C0, 0x04D1): ("Teensy",   "Teensy MIDI+Serial",      BYELLOW),
    (0x16C0, 0x04D2): ("Teensy",   "Teensy MIDIx4+Serial",    BYELLOW),
    (0x16C0, 0x04D3): ("Teensy",   "Teensy MIDIx16+Serial",   BYELLOW),
    (0x16C0, 0x04D4): ("Teensy",   "Teensy Audio+Serial",     BYELLOW),
    (0x16C0, 0x0487): ("Teensy",   "Teensy 4.x Serial",       BYELLOW),
    (0x16C0, None):   ("Teensy",   "Teensy Board",            BYELLOW),

    (0xF055, 0x9800): ("STM32",    "PyBoard [MicroPython]",   BBLUE),
    (0xF055, 0x9801): ("STM32",    "PyBoard CDC+HID",         BBLUE),
    (0xF055, None):   ("STM32",    "MicroPython Board",       BBLUE),

    (0x1915, 0x520F): ("nRF52840", "Nordic nRF52840 DK",      BBLUE),
    (0x1915, 0x5210): ("nRF52840", "Nordic nRF52840 Dongle",  BBLUE),
    (0x1915, None):   ("Nordic",   "Nordic Board",            BBLUE),

    (0xCAFE, None):   ("TinyUSB",  "TinyUSB Dev Board",       BGRAY),

    (0x03EB, 0x2045): ("SAMD21",   "Atmel SAMD21 DFU",        WHITE),
    (0x03EB, 0x2157): ("SAMD51",   "Atmel SAMD51 DFU",        WHITE),
    (0x03EB, 0x6124): ("SAM",      "Atmel SAM-BA Bootloader", WHITE),
    (0x03EB, None):   ("Microchip","Atmel/Microchip Board",   WHITE),

    (0x0483, 0x374B): ("STM32",    "ST-Link/V2",              BBLUE),
    (0x0483, 0x374E): ("STM32",    "ST-Link/V3",              BBLUE),
    (0x0483, 0x5740): ("STM32",    "STM32 VCP",               BBLUE),
    (0x0483, 0xDF11): ("STM32",    "STM32 DFU Bootloader",    BBLUE),
    (0x0483, None):   ("STM32",    "STM32 Board",             BBLUE),

    (0x2A19, None):   ("Numato",   "Numato Board",            WHITE),

    (0x1FFB, 0x00A9): ("ATmega32U4","Pololu A-Star 32U4",     WHITE),
    (0x1FFB, None):   ("Pololu",   "Pololu Board",            WHITE),

    (0x2B04, 0xC006): ("STM32",    "Particle Photon",         BBLUE),
    (0x2B04, 0xC008): ("STM32",    "Particle Electron",       BBLUE),
    (0x2B04, None):   ("Particle", "Particle Board",          BBLUE),

    (0x0525, 0xA4A7): ("RPi Zero", "RPi Zero [USB Gadget]",   BCYAN),
    (0x0525, None):   ("RPi",      "Raspberry Pi USB Gadget", BCYAN),

    (0x0D28, 0x0204): ("nRF51",    "BBC micro:bit",           BYELLOW),
    (0x0D28, None):   ("micro:bit","BBC micro:bit",           BYELLOW),

    (0x1443, None):   ("Digilent", "Digilent Board",          WHITE),

    (0x1366, 0x0105): ("J-Link",   "Segger J-Link CDC",       BGRAY),
    (0x1366, None):   ("Segger",   "Segger J-Link",           BGRAY),

    (0x1A86, 0x8010): ("CH32V",    "WCH CH32V Board",         BGREEN),
}

def identify_port(port):
    if port.vid is None:
        return None
    return BOARDS.get((port.vid, port.pid)) or BOARDS.get((port.vid, None))

def scan_ports():
    return [(p, identify_port(p)) for p in list_ports.comports() if identify_port(p)]

def all_serial_ports():
    return list(list_ports.comports())

def tw():
    try: return os.get_terminal_size().columns
    except: return 80

def bar(ch="-", col=BGRAY):
    return col + ch * tw() + R

def dbar(col=BGRAY):
    return col + "=" * tw() + R

def center(text, width=None):
    w = width or tw()
    clean = re.sub(r'\033\[[0-9;]*m', '', text)
    pad = max(0, (w - len(clean)) // 2)
    return " " * pad + text

def ts():
    return BGRAY + DIM + datetime.datetime.now().strftime('%H:%M:%S') + R

class RawInput:
    UP = "UP"
    DOWN = "DOWN"
    ENTER = "ENTER"
    CTRL_C = "CTRL_C"
    OTHER = "OTHER"

    def __init__(self):
        self.fd = sys.stdin.fileno()
        self._old = None
    
    def __enter__(self):
        self._old = termios.tcgetattr(self.fd)
        tty.setraw(self.fd)
        return self
    
    def __exit__(self, *_):
        if self._old is not None:
            termios.tcsetattr(self.fd, termios.TCSADRAIN, self._old)
    
    def read(self):
        ch = os.read(self.fd, 1)
        if ch == b'\x03':              return self.CTRL_C
        if ch in (b'\r', b'\n'):       return self.ENTER
        if ch == b'\x1b':
            if select.select([sys.stdin], [], [], 0.05)[0]:
                ch2 = os.read(self.fd, 1)
                if ch2 == b'[':
                    ch3 = os.read(self.fd, 1)
                    if ch3 == b'A':    return self.UP
                    if ch3 == b'B':    return self.DOWN
            return self.OTHER
        return self.OTHER
    
CONNECT_FACES = []
WAIT_FACES = []
DISCO_FACES = []
BYE_FACES = []
MULTI_FACES = []

LOGO = [
    "  ███████╗███████╗███████╗",
    "  ██╔════╝╚══███╔╝██╔════╝",
    "  █████╗    ███╔╝ ███████╗",
    "  ██╔══╝   ███╔╝  ╚════██║",
    "  ███████╗███████╗███████║",
    "  ╚══════╝╚══════╝╚══════╝",
]

import random
rng = random.Random()
def face(pool): return rng.choice(pool)
def splash():
    pname = platform_name()
    pcol = BCYAN if ON_MAC else BGREEN
    print()
    print(dbar(BGREEN))
    for line in LOGO:
        print(BGREEN + BOLD + center(line) + R)
    print(center(f"{BGRAY}universal serial monitor  //  RP2040  RP2350  ESP32  CircuitPython  MicroPython  +more{R}"))
    print(center(f"{pcol}running on {pname}{R}"))
    print(dbar(BGREEN))
    print()