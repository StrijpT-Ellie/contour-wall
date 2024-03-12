# contourwall_core

This library provides an interface for controlling the tiles using the ContourWall protocol over serial communication
with an ESP32 device mounted on each tile of the ContourWall.
The ContourWallCore struct represents the core functionality, allowing you to initialize a connection to a COM port, 
send commands to update LED colors, retrieve tile identifiers, and more.
For more details on available commands and usage, refer to the individual function documentation.

## Example Usage

Add `contourwall_core = "0.1.0"` to your Cargo.toml file.

To utilize this library, ensure you have the necessary serial port permissions 
and ESP32 firmware flashed with the ContourWall protocol support.

```rust
use std::ffi::CString;
use contourwall_core::*;
fn main() {
    let com_port = CString::new("/dev/ttyUSB3").expect("CString conversion failed").into_raw();
    let baud_rate = 921_600;
    let mut cw = new(com_port, baud_rate);
    let status_code = command_1_solid_color(&mut cw, 255, 0, 255); // Sets all LEDs to purple
    assert_eq!(status_code, StatusCode::Ok.as_u8());
    let status_code = command_0_show(&mut cw); // Shows the changes on the LED tiles
    assert_eq!(status_code, StatusCode::Ok.as_u8());
}
```

## Compatibility

This library is compatible with both Windows and Linux systems, It has been tested on Windows devices and a 
Raspberry Pi 5. MacOS is untested, however it should work.

## Errors

Errors encountered during serial communication or protocol execution are indicated 
through StatusCode values returned by the library functions.

## Safety

This library uses unsafe Rust code to interface with C-style pointers and raw bytes for serial communication. 
Extra care should be taken to ensure proper usage to avoid memory unsafety and undefined behavior.

## Protocol Documentation

As this library and the protocol are still constantly under development, there is no documentation of the protocol yet.
However, protocol document is in the working and will be published once it is mostly stable and tested.

## License

This library is distributed under the terms of the MIT license. 
See the [LICENSE](https://github.com/StrijpT-Ellie/contour-wall/blob/main/LICENSE) file for details.