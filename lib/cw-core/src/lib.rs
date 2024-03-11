//! This library provides an interface for controlling the tiles using the ContourWall protocol over serial communication
//! with an ESP32 device mounted on each tile of the ContourWall.
//!
//! The ContourWallCore struct represents the core functionality, allowing you to initialize a connection to a COM port, 
//! send commands to update LED colors, retrieve tile identifiers, and more.
//!
//! For more details on available commands and usage, refer to the individual function documentation.
//!
//! # Example Usage
//!
//! To utilize this library, ensure you have the necessary serial port permissions 
//! and ESP32 firmware flashed with the ContourWall protocol support.
//!
//! ```rust
//! use std::ffi::CString;
//! use contourwall_core::*;
//!
//! fn main() {
//!     let com_port = CString::new("/dev/ttyUSB3").expect("CString conversion failed").into_raw();
//!     let baud_rate = 921_600;
//!     let mut cw = new(com_port, baud_rate);
//!
//!     let status_code = command_1_solid_color(&mut cw, 255, 0, 255); // Sets all LEDs to purple
//!     assert_eq!(status_code, StatusCode::Ok.as_u8());
//!
//!     let status_code = command_0_show(&mut cw); // Shows the changes on the LED tiles
//!     assert_eq!(status_code, StatusCode::Ok.as_u8());
//! }
//! ```
//!
//! # Compatibility
//!
//! This library is compatible with both Windows and Linux systems, It has been tested on Windows devices and a 
//! Raspberry Pi 5. MacOS is untested, however it should work.
//!
//! # Errors
//!
//! Errors encountered during serial communication or protocol execution are indicated 
//! through StatusCode values returned by the library functions.
//!
//! # Safety
//!
//! This library uses unsafe Rust code to interface with C-style pointers and raw bytes for serial communication. 
//! Extra care should be taken to ensure proper usage to avoid memory unsafety and undefined behavior.
//!
//! # Protocol Documentation
//!
//! This library assumes adherence to the ContourWall protocol. 
//! Please refer to the protocol documentation for more information on commands and their expected behavior.
//!
//! # License
//!
//! This library is distributed under the terms of the MIT license. 
//! See the [LICENSE](https://github.com/StrijpT-Ellie/contour-wall/blob/main/LICENSE) file for details.

use std::ffi::{c_char, CStr};
use std::time::{Duration, SystemTime};
use serialport::SerialPort;

type StatusCodeAlias = u8;
type SerialPointerAlias = *mut Box<dyn SerialPort>;

/// Enum abstraction over the StatusCodes used signal the status of the ESP32.
pub mod status_code; 
use status_code::StatusCode;

/// ContourWallCore encapsulates the essential elements required for communication with LED tiles, including timing parameters and the serial port connection.
#[repr(C)]
#[derive(Debug)]
pub struct ContourWallCore {
    /// The minimum time between between frames pushed to a tile. Default values is 33ms (33fps)
    pub frame_time: u64,    
    /// Last time since frame as pushed to tile. Stored as amount of milliseconds since Linux EPOCH
    pub last_serial_write_time: u64, 
    /// The serial COM port connected to a ESP32 (tile)
    pub serial: SerialPointerAlias,
} 

/// Creates a new instance of the ContourWallCore struct.
/// 
/// ## Parameters
/// - com_port: Device name of the COM port
///     - Example Device name: `/dev/ttyUSB3` (Linux), `COM3` (Windows)
/// - baudrate: The speed of the UART connection
///     - Expected speed is 921.600 MHz
///     - If you use a different speed, you need to flash new firmware to the ESP32
/// 
/// ## Return
/// - Returns an initialized ContourWallCore struct
/// 
/// ## Example
/// ```
/// let com_string: *const c_char = CString::new("COM16").unwrap().into_raw();
/// let baud_rate: u32 = 921_600
/// 
/// let cw: ContourWallCore = new(com_string, baud_rate);
/// ```
#[no_mangle]
pub extern "C" fn new(com_port: *const c_char, baudrate: u32) -> ContourWallCore {
    let serial = serialport::new(str_ptr_to_string(com_port), baudrate)
        .timeout(Duration::from_secs(0))
        .stop_bits(serialport::StopBits::One)
        .parity(serialport::Parity::None)
        .open()
        .expect(format!("[CW CORE ERROR] Could not open COM port: {}", str_ptr_to_string(com_port)).as_str());

    ContourWallCore {
        serial: Box::into_raw(Box::new(serial)) as SerialPointerAlias,
        frame_time: 33,
        last_serial_write_time: millis_since_epoch(),
    }
}

/// Executes `command_0_show` of the protocol.
/// 
/// This command signals to the tile that the its current framebuffer needs to be displayed or shown.
/// It expects a `100` or StatusCode::Ok, which is being returned by the tile _before_ it update its LED's.
/// 
/// The time in between calls needs to be atleast `ContourWallCore::frame_time` (this), which by default is 33ms.
/// 
/// ## Parameters
/// - this: mutable pointer to the ContourWallCore struct
/// 
/// ## Return
/// - StatusCode as an `u8` (`uint8_t`)
/// 
/// ## Example
/// ```
/// let cw: ContourWallCore = new(com_port, baud_rate);
/// 
/// let status_code = command_0_show(&mut cw);
/// ```
#[no_mangle]
pub extern "C" fn command_0_show(this: &mut ContourWallCore) -> StatusCodeAlias {
    // Sleeping if the time between "show" commands to too little. The frametimes cannot be shorter than ContourWallCore::frame_time.
    // This calculates the left over time for the thread to sleep, if any at all.
    let timespan = millis_since_epoch() - this.last_serial_write_time;
    if timespan < this.frame_time.into() {
        std::thread::sleep(Duration::from_millis((this.frame_time as u64) - timespan));
    }

    if write_to_serial_async(this.serial, &[0]).is_err() {
        return StatusCode::ErrorInternal.as_u8()
    }

    this.last_serial_write_time = millis_since_epoch();

    // Read response of tile 
    let read_buf = &mut[0; 1];
    if serial_read(this.serial, read_buf).is_err() || StatusCode::new(read_buf[0]).is_none() {
        return StatusCode::ErrorInternal.as_u8()
    }

    read_buf[0]
}

/// Executes `command_1_solid_color` of the protocol, which sets *all* pixels on a tile to one specific color.
/// 
/// Although possible, the function is not meant for developers to call this function "bare"
/// The intent of this function is for background optimizations. If the vast majority of the framebuffer is one color, 
/// than you could execute two protocol commands, E.G. `command_1_solid_color()` and `command_3_update_specific_led`. 
/// A background optimization could lead to faster frame times.
/// 
/// ## Parameters
/// - this: mutable pointer to the ContourWallCore struct
/// - red: 8-bit value of color red
/// - green: 8-bit value of color red
/// - blue: 8-bit value of color red
/// 
/// ## Return
/// - StatusCode as an `u8` (`uint8_t`)
/// 
/// ## Examples
/// 
/// Sets all LEDs on tile to purple
/// ```
/// let cw: ContourWallCore = new(com_port, baud_rate);
/// 
/// let red: u8 = 255;
/// let green: u8 = 0;
/// let blue: u8 = 255;
/// 
/// let status_code = command_1_solid_color(&mut cw, red, green ,blue);
/// ```
/// 
/// Fades tiles from black to white
/// ```
/// let cw: ContourWallCore = new(com_port, baud_rate);
/// 
/// for i in 0..255 {
///     let status_code = command_1_solid_color(&mut cw, i, i ,i);
/// 
///     let status_code = command_0_show(&mut cw);
/// }
/// ```
#[no_mangle]
pub extern "C" fn command_1_solid_color(this: &mut ContourWallCore, red: u8, green: u8, blue: u8) -> StatusCodeAlias {
    let crc = red.wrapping_add(green).wrapping_add(blue);
    if write_to_serial_async(this.serial, &[1, red, green, blue, crc]).is_err() {
        return StatusCode::ErrorInternal.as_u8()
    }

    // Read response of tile 
    let read_buf = &mut[0; 1];
    if serial_read(this.serial, read_buf).is_err() || StatusCode::new(read_buf[0]).is_none() {
        return StatusCode::ErrorInternal.as_u8()
    }

    read_buf[0]
}

/// Executes `command_2_update_all` of the protocol, sets LED's to individually assigned colors based on index of the RGB values
/// 
/// The order of the RGB values is expected to be identical to how they are wired on a tile.
/// 
/// ## Warning
/// 
/// The size of the framebuffer array needs to be 1200. A red, green and blue value for 400 LEDs.
/// 
/// ## Parameters
/// - this: mutable pointer to the ContourWallCore struct
/// - frame_buffer_ptr: pointer to the start of the framebuffer array
/// 
/// ## Return
/// - StatusCode as an `u8` (`uint8_t`)
/// 
/// ## Example
/// 
/// Sets first LED to RED, the rest is set to black (off)
/// ```
/// let mut cw = new(com_string, baud_rate);
/// 
/// let mut framebuffer = &mut[0; 1200];
/// framebuffer[0] = 255;
///
/// let status_code = command_2_update_all(&mut cw, framebuffer.as_ptr());
/// ```
#[no_mangle]
pub extern "C" fn command_2_update_all(this: &mut ContourWallCore, frame_buffer_ptr: *const u8) -> StatusCodeAlias {
    // Indicate to tile that command 2 is about to be executed
    if write_to_serial_async(this.serial, &[2]).is_err() {
        return StatusCode::ErrorInternal.as_u8()
    }

    // Generate framebuffer from pointer and generating the CRC by taking the sum of all the RGB values of the framebuffer
    let frame_buffer: &[u8] = unsafe { std::slice::from_raw_parts(frame_buffer_ptr, 1200) };
    let mut crc: u8 = 0;
    for byte in frame_buffer {
        crc += *byte;
    }
    let binding = [frame_buffer, &[crc]].concat();
    let frame_buffer = binding.as_slice();

    // Write framebuffer over serial to tile
    if write_to_serial_async(this.serial, frame_buffer).is_err() {
        return StatusCode::ErrorInternal.as_u8()
    }

    // Read response of tile 
    let read_buf = &mut[0; 1];
    if serial_read(this.serial, read_buf).is_err() || StatusCode::new(read_buf[0]).is_none() {
        return StatusCode::ErrorInternal.as_u8()
    }

    read_buf[0]
}

/// Executes `command_3_update_all` of the protocol, sets some LED's to individually assigned colors based given index with RGB code.
/// 
/// For every specific LED being updated, five bytes are needed. Two bytes for the LED index, one byte for red, blue and green.
/// The index for the LED is stored in [big-endian](https://en.wikipedia.org/wiki/Endianness) format, most significant byte on the smaller address.
/// 
/// ## Performance
/// 
/// Although the `led_count` can go up to 255, it is recommeneded to not update more then 200 LED's or so with this protocol command.
/// At around 200 updated LED's, this command will be slower then `command_2_update_all`, 
/// as less efficient at transferring data and requires more processing time
/// 
/// ## Parameters
/// - this: Mutable pointer to the ContourWallCore struct
/// - frame_buffer_ptr: Pointer to the start of the framebuffer array
/// - led_count: Amount of LED indexes and RGB values it contains
/// 
/// ## Return
/// - StatusCode as an `u8` (`uint8_t`)
/// 
/// ## Example
/// 
/// Sets 4th LED to red, 256th LED to blue
/// ```
/// let mut cw = new(com_string, baud_rate);
/// let framebuffer = &mut[0, 3, 255, 0, 0, 1, 0, 0, 0, 255];
/// 
/// let status_code = command_3_update_specific_led(&mut cw, framebuffer.as_ptr(), 2);
/// ```
#[no_mangle]
pub extern "C" fn command_3_update_specific_led(this: &mut ContourWallCore, frame_buffer_ptr: *const u8,  led_count: u8) -> StatusCodeAlias {
    // Indicate to tile that command 2 is about to be executed
    if write_to_serial_async(this.serial, &[3]).is_err() {
        return StatusCode::ErrorInternal.as_u8()
    }

    if write_to_serial_async(this.serial, &[led_count, led_count]).is_err() {
        return StatusCode::ErrorInternal.as_u8()
    }
    
    // Reading the next
    let read_buf = &mut[0; 1];
    if serial_read(this.serial, read_buf).is_err() || StatusCode::new(read_buf[0]).is_none() {
        return StatusCode::ErrorInternal.as_u8()
    }

    let status_code = StatusCode::new(read_buf[0]).unwrap();
    if status_code != StatusCode::Next {
        return status_code.as_u8();
    }

    // Generate framebuffer from pointer and generating the CRC by taking the sum of all the RGB values of the framebuffer
    let frame_buffer: &[u8] = unsafe { std::slice::from_raw_parts(frame_buffer_ptr, (led_count * 5) as usize) };
    let mut crc: u8 = 0;
    for byte in frame_buffer {
        crc += *byte;
    }
    let binding = [frame_buffer, &[crc]].concat();
    let frame_buffer = binding.as_slice();

    // Write framebuffer over serial to tile
    if write_to_serial_async(this.serial, frame_buffer).is_err() {
        return StatusCode::ErrorInternal.as_u8()
    }

    let read_buf = &mut[0; 1];
    if serial_read(this.serial, read_buf).is_err() || StatusCode::new(read_buf[0]).is_none() {
        return StatusCode::ErrorInternal.as_u8()
    }

    read_buf[0]
}

/// Executes `command_4_get_tile_identifier` of the protocol. Returns the tile identifier which is set in the EEPROM of the ESP32
/// 
/// Returns an `u16` (`uint16_t`), which are two `u8`'s (`uint8_t`) concatinated. 
/// The eight right-most bites are the StatusCode, the eight left-most bits are the actual identifier.
/// 
/// ## Example
/// ```
/// let mut cw = new(com_string, baud_rate);
/// 
/// let response = command_4_get_tile_identifier(&mut cw);
/// 
/// let status_code = (response & 255) as u8;
/// let identifier = (response >> 8) as u8;
/// ```
#[no_mangle]
pub extern "C" fn command_4_get_tile_identifier(this: &mut ContourWallCore) -> u16 {
    if write_to_serial_async(this.serial, &[4]).is_err() {
        return StatusCode::ErrorInternal.as_u8() as u16;
    }
    
    let read_buf = &mut[0; 1];
    if serial_read(this.serial, read_buf).is_err() || StatusCode::new(read_buf[1]).is_none() {
        return StatusCode::ErrorInternal.as_u8() as u16;
    }

    ((read_buf[0] as u16) << 8) + read_buf[1] as u16
}

/// Executes `command_5_set_tile_identifier` of the protocol. Sets a new tile identifier in the EEPROM of the ESP32
/// 
/// *WARNING*: DO NOT USE 0 AS AN ADDRESS.
#[no_mangle]
pub extern "C" fn command_5_set_tile_identifier(this: &mut ContourWallCore,  identifier: u8) -> StatusCodeAlias {
    if identifier == 0 {
        eprintln!("[CW CORE ERROR] Cannot set a tile identifier to 0");
        return StatusCode::Error.as_u8();
    }

    if write_to_serial_async(this.serial, &[5, identifier, identifier]).is_err() {
        return StatusCode::ErrorInternal.as_u8()
    }

    let read_buf = &mut[0; 1];
    if serial_read(this.serial, read_buf).is_err() || StatusCode::new(read_buf[0]).is_none() {
        return StatusCode::ErrorInternal.as_u8()
    }

    read_buf[0]
}

/// Sets the frame_time field of the ContourWallCore struct in milliseconds. 
/// 
/// Default frame_time is 33ms and it is not recommended to go less than 33ms
#[no_mangle]
pub extern "C" fn set_frame_time(this: &mut ContourWallCore, frame_time: u64) {
    this.frame_time = frame_time;
}

/// Returns current set frame_time of the ContourWallCore struct in milliseconds.
#[no_mangle]
pub extern "C" fn get_frame_time(this: &mut ContourWallCore) -> u64 {
    this.frame_time
}

/// Transfers ownership of the ContourWallCore object back to Rust and frees the memory.
#[no_mangle]
pub extern "C" fn drop(this: *mut ContourWallCore) {
    if !this.is_null() {
        unsafe {
            let cw = Box::from_raw(this);
            std::mem::drop(cw);
        }
    }
}

fn serial_read(serial: SerialPointerAlias, buffer: &mut[u8]) -> Result<(), ()> {
    let serial = unsafe {  &mut *serial };
    
    let start = millis_since_epoch();
    let time_to_receive_ms = 30;
    while serial.bytes_to_read().expect("Cannot get bytes from serial read buffer") < buffer.len() as u32 {
        if (millis_since_epoch() - start) > time_to_receive_ms {
            eprintln!("[CW CORE ERROR] Only {}/{} bytes were received within the {}ms allocated time", serial.bytes_to_read().unwrap(), buffer.len(), time_to_receive_ms);
            let _res = (*serial).clear(serialport::ClearBuffer::Input);
            return Err(());
        }
    } 

    if let Err(e) = serial.read_exact(buffer) {
        eprintln!("[CW CORE ERROR] Error occured during reading of Serial buffer: {}", e);
        Err(())
    } else {
        Ok(())
    }
}

fn write_to_serial_async(serial: SerialPointerAlias, bytes: &[u8]) -> Result<usize, std::io::Error> {
    unsafe { (*serial).write(bytes) }
}

fn write_to_serial(serial: SerialPointerAlias, bytes: &[u8]) -> Result<(), std::io::Error> {
    unsafe { (*serial).write_all(bytes) }
}

fn millis_since_epoch() -> u64 {
    let now = SystemTime::now();
    let duration_since_epoch = now.duration_since(SystemTime::UNIX_EPOCH).unwrap();
    duration_since_epoch.as_nanos() as u64 / 1_000_000
}

fn str_ptr_to_string(ptr: *const c_char) -> String {
    let c_str = unsafe { CStr::from_ptr(ptr) };
    c_str.to_string_lossy().into_owned()
}

#[cfg(test)]
mod tests {
    use std::ffi::CString;

    use super::*;

    #[test]
    fn update_specific() {
        let framebuffer = &mut[0, 4, 0, 255, 0, 0, 10, 0, 100, 100, 1, 100, 255, 0, 255];
        let com_string: *const c_char = CString::new("COM16").expect("CString conversion failed").into_raw();

        let mut cw = new(com_string, 921_600);
        let code = command_3_update_specific_led(&mut cw, framebuffer.as_ptr(), (framebuffer.len()/5) as u8);
        assert_eq!(code, 100, "testing if 'command_2_update_specific_led' works");

        let code = command_0_show(&mut cw);
        assert_eq!(code, 100, "testing if 'command_0_show' works");
    }

    #[test]
    fn update_all() {
        let framebuffer = &mut[100; 1200];

        let com_string: *const c_char = CString::new("COM16").expect("CString conversion failed").into_raw();

        let mut cw = new(com_string, 921_600);

        let code = command_2_update_all(&mut cw, framebuffer.as_ptr());
        assert_eq!(code, 100, "testing if 'command_2_update_all' works");

        let code = command_0_show(&mut cw);
        assert_eq!(code, 100, "testing if 'command_0_show' works");
    }

    #[test]
    fn solid_color() {
        let com_string: *const c_char = CString::new("COM16").expect("CString conversion failed").into_raw();

        let mut cw = new(com_string, 921_600);

        let code = command_1_solid_color(&mut cw, 0, 0, 255);
        assert_eq!(code, 100);
        
        let code = command_0_show(&mut cw);
        assert_eq!(code, 100, "testing if 'command_0_show' works");
    }

    #[test]
    fn tile_identifier_test() {
        let com_string: *const c_char = CString::new("COM16").expect("CString conversion failed").into_raw();
        let mut cw = new(com_string, 921_600);

        let identifier: u8 = 4;

        let res = command_5_set_tile_identifier(&mut cw, identifier);
        assert_eq!(res, 100, "testing if 'command_4_get_tile_identifier' works");

        let res = command_4_get_tile_identifier(&mut cw);
        assert_eq!((res & 255) as u8, 100, "testing if 'command_4_get_tile_identifier' works");
        assert_eq!((res >> 8) as u8, identifier);
    }
}