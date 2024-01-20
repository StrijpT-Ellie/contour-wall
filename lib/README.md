# contourwall.py

`contourwall.py` is the proof-of-concept Python library to control the Contour Wall. It implements its custom communcation which is based on UART. The implemenation is cross-platform, and thus will work on E.G. Raspberry Pi's and your Windows laptop. 

On the "slave-side" of this protocol is designed to be a [ESP32](https://www.espressif.com/en/products/socs/esp32) as that is with which the LED is designed. However, it should work with other micro-controllers. For the slave-side implementation of the protocol go to [firmware.ino](../firmware/)

In the [samples](/lib/samples/) directory are a variety of samples to run with this libary on a tile. These could be used to test new code, or as a demo to interesed people.

## How to run

1. Have python3.11 installed
2. Install PiP packages: `python3.11 -m pip install -r requirments.txt`