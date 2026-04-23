#!/bin/bash
set -e

OS="$(uname -s)"
echo ""

if [ "$OS" = "Darwin" ]; then
    echo "  detected macos!!"
    BIN_DIR="/usr/local/bin"
elif [ "$OS" = "Linux" ]; then
    echo "  detected linux!!"
    BIN_DIR="/usr/local/bin"
        if ! groups "$USER" | grep -qw dialout 2>/dev/null; then
        echo ""
        echo "  NOTE: '$USER' is not in the dialout group."
        echo "  Fix with:  sudo usermod -aG dialout $USER  (then re-login)"
        echo ""
    fi
else
    echo "  unsupported os: $OS ! :C"
    exit 1
fi

if ! command -v python3 &>/dev/null; then
    echo "  python3 not found!! please install: https://python.org/"
    exit 1
fi

if ! python3 -c "import serial" 2>/dev/null; then
    echo "  installing pyserial..."
    pip3 install pyserial --quiet
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SRC="$SCRIPT_DIR/ezserial.py"

# set ezserial alias
cp "$SRC" "$BIN_DIR/ezserial"
chmod +x "$BIN_DIR/ezserial"

# set ezs alias
cp "$SRC" "$BIN_DIR/ezs"
chmod +x "$BIN_DIR/ezs"

echo "  installed: $BIN_DIR/ezserial"
echo "  installed: $BIN_DIR/ezs"
echo ""
echo "  usage:"
echo "    ezserial / ezs | opens up the main tui!"
echo "    ezs --baud 9600 | set a custom baud rate!"
echo "    ezs --log session.txt | save the session to a log file!"
echo "    ezs --list | list all serial ports without filtering for boards!"
echo "    ezs --port {port_hint().split()[0]} | force a specific port!"
if [ "$OS" = "Darwin" ]; then # shower thought why is mac called darwijn i never understood that t-t
    echo "    ezserial --port /dev/cu.xxx  force a specific port"
else
    echo "    ezserial --port /dev/ttyUSB0  force a specific port"
fi
echo ""
echo "  have fun! ^-^/"
echo ""