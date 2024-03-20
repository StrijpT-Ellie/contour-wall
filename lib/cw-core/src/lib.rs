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

use serialport::SerialPort;
use std::ffi::{c_char, CStr};
use std::time::{Duration, SystemTime};

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
    ///
    index_converter_vector: [usize; 1200],
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
        .expect(
            format!(
                "[CW CORE ERROR] Could not open COM port: {}",
                str_ptr_to_string(com_port)
            )
            .as_str(),
        );

    let index_converter_vector = generate_index_conversion_matrix();

    ContourWallCore {
        serial: Box::into_raw(Box::new(serial)) as SerialPointerAlias,
        frame_time: 33,
        last_serial_write_time: millis_since_epoch(),
        index_converter_vector,
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
        return StatusCode::ErrorInternal.as_u8();
    }

    this.last_serial_write_time = millis_since_epoch();

    // Read response of tile
    // let read_buf = &mut[0; 1];
    // if serial_read(this.serial, read_buf).is_err() || StatusCode::new(read_buf[0]).is_none() {
    //     return StatusCode::ErrorInternal.as_u8()
    // }

    // read_buf[0]

    StatusCode::Ok.as_u8()
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
pub extern "C" fn command_1_solid_color(
    this: &mut ContourWallCore,
    red: u8,
    green: u8,
    blue: u8,
) -> StatusCodeAlias {
    let crc = red.wrapping_add(green).wrapping_add(blue);
    if write_to_serial_async(this.serial, &[1, red, green, blue, crc]).is_err() {
        return StatusCode::ErrorInternal.as_u8();
    }

    // Read response of tile
    let read_buf = &mut [0; 1];
    if serial_read(this.serial, read_buf).is_err() || StatusCode::new(read_buf[0]).is_none() {
        return StatusCode::ErrorInternal.as_u8();
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
pub extern "C" fn command_2_update_all(
    this: &mut ContourWallCore,
    frame_buffer_ptr: *const u8,
) -> StatusCodeAlias {
    // Indicate to tile that command 2 is about to be executed
    if write_to_serial_async(this.serial, &[2]).is_err() {
        return StatusCode::ErrorInternal.as_u8();
    }

    // Generate framebuffer from pointer and generating the CRC by taking the sum of all the RGB values of the framebuffer
    let frame_buffer_unordered: &[u8] = unsafe { std::slice::from_raw_parts(frame_buffer_ptr, 1200) };
    let mut frame_buffer = [0; 1201];
    let mut crc: u8 = 0;
    for (i, byte) in frame_buffer_unordered.iter().enumerate() {
        crc += *byte;
        frame_buffer[this.index_converter_vector[i]] = *byte;
    }
    frame_buffer[1200] = crc;

    // Write framebuffer over serial to tile
    if write_to_serial_async(this.serial, &frame_buffer).is_err() {
        return StatusCode::ErrorInternal.as_u8();
    }

    // Read response of tile
    let read_buf = &mut [0; 1];
    if serial_read(this.serial, read_buf).is_err() || StatusCode::new(read_buf[0]).is_none() {
        return StatusCode::ErrorInternal.as_u8();
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
pub extern "C" fn command_3_update_specific_led(
    this: &mut ContourWallCore,
    frame_buffer_ptr: *const u8,
    led_count: u8,
) -> StatusCodeAlias {
    // Indicate to tile that command 2 is about to be executed
    if write_to_serial_async(this.serial, &[3]).is_err() {
        return StatusCode::ErrorInternal.as_u8();
    }

    if write_to_serial_async(this.serial, &[led_count, led_count]).is_err() {
        return StatusCode::ErrorInternal.as_u8();
    }

    // Reading the next
    let read_buf = &mut [0; 1];
    if serial_read(this.serial, read_buf).is_err() || StatusCode::new(read_buf[0]).is_none() {
        return StatusCode::ErrorInternal.as_u8();
    }

    let status_code = StatusCode::new(read_buf[0]).unwrap();
    if status_code != StatusCode::Next {
        return status_code.as_u8();
    }

    // Generate framebuffer from pointer and generating the CRC by taking the sum of all the RGB values of the framebuffer
    let frame_buffer: &[u8] =
        unsafe { std::slice::from_raw_parts(frame_buffer_ptr, (led_count * 5) as usize) };
    let mut crc: u8 = 0;
    for byte in frame_buffer {
        crc += *byte;
    }
    let binding = [frame_buffer, &[crc]].concat();
    let frame_buffer = binding.as_slice();

    // Write framebuffer over serial to tile
    if write_to_serial_async(this.serial, frame_buffer).is_err() {
        return StatusCode::ErrorInternal.as_u8();
    }

    let read_buf = &mut [0; 1];
    if serial_read(this.serial, read_buf).is_err() || StatusCode::new(read_buf[0]).is_none() {
        return StatusCode::ErrorInternal.as_u8();
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

    let read_buf = &mut [0; 8];
    if serial_read(this.serial, read_buf).is_err() || StatusCode::new(read_buf[1]).is_none() {
        return StatusCode::ErrorInternal.as_u8() as u16;
    }

    let status_code = if StatusCode::new(read_buf[7]).is_none() {
        StatusCode::ErrorInternal.as_u8()
    } else {
        read_buf[7]
    };

    let magic_numbers = read_buf[0..5]
        .iter()
        .map(|&x| x as char)
        .collect::<String>();

    if magic_numbers != String::from("Ellie") {
        StatusCode::NotACWPort.as_u8() as u16 // This COM port is not part of the ContourWall, because the magic numbers are not ELLIE
    } else if read_buf[5] != read_buf[6] {
        StatusCode::NonMatchingCRC.as_u8() as u16
    } else {
        ((read_buf[6] as u16) << 8) + (status_code as u16)
    }
}

/// Executes `command_5_set_tile_identifier` of the protocol. Sets a new tile identifier in the EEPROM of the ESP32
///
/// *WARNING*: DO NOT USE 0 AS AN ADDRESS.
#[no_mangle]
pub extern "C" fn command_5_set_tile_identifier(
    this: &mut ContourWallCore,
    identifier: u8,
) -> StatusCodeAlias {
    if identifier == 0 {
        eprintln!("[CW CORE ERROR] Cannot set a tile identifier to 0");
        return StatusCode::Error.as_u8();
    }

    if write_to_serial_async(this.serial, &[5, identifier, identifier]).is_err() {
        return StatusCode::ErrorInternal.as_u8();
    }

    let read_buf = &mut [0; 1];
    if serial_read(this.serial, read_buf).is_err() || StatusCode::new(read_buf[0]).is_none() {
        return StatusCode::ErrorInternal.as_u8();
    }

    read_buf[0]
}

#[no_mangle]
pub extern "C" fn verify_if_tile(this: &mut ContourWallCore) -> bool {
    let res = command_4_get_tile_identifier(this);
    let res = StatusCode::new((res & 256) as u8).unwrap();
    match res {
        StatusCode::Error
        | StatusCode::TooSlow
        | StatusCode::NonMatchingCRC
        | StatusCode::ErrorInternal
        | StatusCode::NotACWPort => {
            StatusCode::new((command_4_get_tile_identifier(this) & 256) as u8).unwrap()
                == StatusCode::Ok
        }
        StatusCode::UnknownCommand => {
            unreachable!("[CW CORE ERROR] verify_if_tile executed a command which is unknown")
        }
        StatusCode::Next | StatusCode::Reset => unreachable!(
            "[CW CORE ERROR] verify_if_tile, should never receive a {}",
            res
        ),
        StatusCode::Ok => true,
    }
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

fn serial_read(serial: SerialPointerAlias, buffer: &mut [u8]) -> Result<(), ()> {
    let serial = unsafe { &mut *serial };

    let start = millis_since_epoch();
    let time_to_receive_ms = 30;
    while serial
        .bytes_to_read()
        .expect("Cannot get bytes from serial read buffer")
        < buffer.len() as u32
    {
        if (millis_since_epoch() - start) > time_to_receive_ms {
            eprintln!(
                "[CW CORE ERROR] Only {}/{} bytes were received within the {}ms allocated time",
                serial.bytes_to_read().unwrap(),
                buffer.len(),
                time_to_receive_ms
            );
            let _res = (*serial).clear(serialport::ClearBuffer::Input);
            return Err(());
        }
    }

    if let Err(e) = serial.read_exact(buffer) {
        eprintln!(
            "[CW CORE ERROR] Error occured during reading of Serial buffer: {}",
            e
        );
        Err(())
    } else {
        Ok(())
    }
}

fn write_to_serial_async(
    serial: SerialPointerAlias,
    bytes: &[u8],
) -> Result<usize, std::io::Error> {
    unsafe { (*serial).write(bytes) }
}

fn write_to_serial(serial: SerialPointerAlias, bytes: &[u8]) -> Result<(), std::io::Error> {
    unsafe { (*serial).write_all(bytes) }
}

fn generate_index_conversion_matrix() -> [usize; 1200] {
    let mut matrix: [[usize; 20]; 20] = [[0; 20]; 20];
    for x in 0..20 {
        let row_start_value = match x {
            0..=4 => x,
            5..=9 => 100 + x - 5,
            10..=14 => 200 + x  - 10,
            _ => 300 + x - 15,
        };

        let mut y = 0;
        for index in (row_start_value..row_start_value + 100).step_by(5) {
            matrix[y][x] = index * 3;
            y += 1;
        }
    }

    let mut result: [usize; 1200] = [0; 1200];
    let mut index = 0;
    for column in matrix.iter() {
        for &element in column.iter() {
            result[index] = element;
            result[index + 1] = element + 1;
            result[index + 2] = element + 2;
            index += 3;
        }
    }

    result
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
        let framebuffer = &mut [0, 4, 0, 255, 0, 0, 10, 0, 100, 100, 1, 100, 255, 0, 255];
        let com_string: *const c_char = CString::new("COM16")
            .expect("CString conversion failed")
            .into_raw();

        let mut cw = new(com_string, 921_600);
        let code = command_3_update_specific_led(
            &mut cw,
            framebuffer.as_ptr(),
            (framebuffer.len() / 5) as u8,
        );
        assert_eq!(
            code, 100,
            "testing if 'command_2_update_specific_led' works"
        );

        let code = command_0_show(&mut cw);
        assert_eq!(code, 100, "testing if 'command_0_show' works");
    }

    #[test]
    fn update_all() {
        let framebuffer = &mut [100; 1200];

        let com_string: *const c_char = CString::new("COM16")
            .expect("CString conversion failed")
            .into_raw();

        let mut cw = new(com_string, 921_600);

        let code = command_2_update_all(&mut cw, framebuffer.as_ptr());
        assert_eq!(code, 100, "testing if 'command_2_update_all' works");

        let code = command_0_show(&mut cw);
        assert_eq!(code, 100, "testing if 'command_0_show' works");
    }

    #[test]
    fn solid_color() {
        let com_string: *const c_char = CString::new("COM16")
            .expect("CString conversion failed")
            .into_raw();

        let mut cw = new(com_string, 921_600);

        let code = command_1_solid_color(&mut cw, 0, 0, 255);
        assert_eq!(code, 100);

        let code = command_0_show(&mut cw);
        assert_eq!(code, 100, "testing if 'command_0_show' works");
    }

    #[test]
    fn tile_identifier_test() {
        let com_string: *const c_char = CString::new("COM16")
            .expect("CString conversion failed")
            .into_raw();
        let mut cw = new(com_string, 921_600);

        let identifier: u8 = 4;

        let res = command_5_set_tile_identifier(&mut cw, identifier);
        assert_eq!(res, 100, "testing if 'command_4_get_tile_identifier' works");

        let res = command_4_get_tile_identifier(&mut cw);
        assert_eq!(
            (res & 255) as u8,
            100,
            "testing if 'command_4_get_tile_identifier' works"
        );
        assert_eq!((res >> 8) as u8, identifier);
    }

    #[rustfmt::skip]
    #[test]
    fn test_index_conversion_generators() {
        let output = generate_index_conversion_matrix();
        let correct_output = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 300, 301, 302, 303, 304, 305, 306, 307, 308, 309, 310, 311, 312, 313, 314, 600, 601, 602, 603, 604, 605, 606, 607, 608, 609, 610, 611, 612, 613, 614, 900, 901, 902, 903, 904, 905, 906, 907, 908, 909, 910, 911, 912, 913, 914, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 315, 316, 317, 318, 319, 320, 321, 322, 323, 324, 325, 326, 327, 328, 329, 615, 616, 617, 618, 619, 620, 621, 622, 623, 624, 625, 626, 627, 628, 629, 915, 916, 917, 918, 919, 920, 921, 922, 923, 924, 925, 926, 927, 928, 929, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 330, 331, 332, 333, 334, 335, 336, 337, 338, 339, 340, 341, 342, 343, 344, 630, 631, 632, 633, 634, 635, 636, 637, 638, 639, 640, 641, 642, 643, 644, 930, 931, 932, 933, 934, 935, 936, 937, 938, 939, 940, 941, 942, 943, 944, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 58, 59, 345, 346, 347, 348, 349, 350, 351, 352, 353, 354, 355, 356, 357, 358, 359, 645, 646, 647, 648, 649, 650, 651, 652, 653, 654, 655, 656, 657, 658, 659, 945, 946, 947, 948, 949, 950, 951, 952, 953, 954, 955, 956, 957, 958, 959, 60, 61, 62, 63, 64, 65, 66, 67, 68, 69, 70, 71, 72, 73, 74, 360, 361, 362, 363, 364, 365, 366, 367, 368, 369, 370, 371, 372, 373, 374, 660, 661, 662, 663, 664, 665, 666, 667, 668, 669, 670, 671, 672, 673, 674, 960, 961, 962, 963, 964, 965, 966, 967, 968, 969, 970, 971, 972, 973, 974, 75, 76, 77, 78, 79, 80, 81, 82, 83, 84, 85, 86, 87, 88, 89, 375, 376, 377, 378, 379, 380, 381, 382, 383, 384, 385, 386, 387, 388, 389, 675, 676, 677, 678, 679, 680, 681, 682, 683, 684, 685, 686, 687, 688, 689, 975, 976, 977, 978, 979, 980, 981, 982, 983, 984, 985, 986, 987, 988, 989, 90, 91, 92, 93, 94, 95, 96, 97, 98, 99, 100, 101, 102, 103, 104, 390, 391, 392, 393, 394, 395, 396, 397, 398, 399, 400, 401, 402, 403, 404, 690, 691, 692, 693, 694, 695, 696, 697, 698, 699, 700, 701, 702, 703, 704, 990, 991, 992, 993, 994, 995, 996, 997, 998, 999, 1000, 1001, 1002, 1003, 1004, 105, 106, 107, 108, 109, 110, 111, 112, 113, 114, 115, 116, 117, 118, 119, 405, 406, 407, 408, 409, 410, 411, 412, 413, 414, 415, 416, 417, 418, 419, 705, 706, 707, 708, 709, 710, 711, 712, 713, 714, 715, 716, 717, 718, 719, 1005, 1006, 1007, 1008, 1009, 1010, 1011, 1012, 1013, 1014, 1015, 1016, 1017, 1018, 1019, 120, 121, 122, 123, 124, 125, 126, 127, 128, 129, 130, 131, 132, 133, 134, 420, 421, 422, 423, 424, 425, 426, 427, 428, 429, 430, 431, 432, 433, 434, 720, 721, 722, 723, 724, 725, 726, 727, 728, 729, 730, 731, 732, 733, 734, 1020, 1021, 1022, 1023, 1024, 1025, 1026, 1027, 1028, 1029, 1030, 1031, 1032, 1033, 1034, 135, 136, 137, 138, 139, 140, 141, 142, 143, 144, 145, 146, 147, 148, 149, 435, 436, 437, 438, 439, 440, 441, 442, 443, 444, 445, 446, 447, 448, 449, 735, 736, 737, 738, 739, 740, 741, 742, 743, 744, 745, 746, 747, 748, 749, 1035, 1036, 1037, 1038, 1039, 1040, 1041, 1042, 1043, 1044, 1045, 1046, 1047, 1048, 1049, 150, 151, 152, 153, 154, 155, 156, 157, 158, 159, 160, 161, 162, 163, 164, 450, 451, 452, 453, 454, 455, 456, 457, 458, 459, 460, 461, 462, 463, 464, 750, 751, 752, 753, 754, 755, 756, 757, 758, 759, 760, 761, 762, 763, 764, 1050, 1051, 1052, 1053, 1054, 1055, 1056, 1057, 1058, 1059, 1060, 1061, 1062, 1063, 1064, 165, 166, 167, 168, 169, 170, 171, 172, 173, 174, 175, 176, 177, 178, 179, 465, 466, 467, 468, 469, 470, 471, 472, 473, 474, 475, 476, 477, 478, 479, 765, 766, 767, 768, 769, 770, 771, 772, 773, 774, 775, 776, 777, 778, 779, 1065, 1066, 1067, 1068, 1069, 1070, 1071, 1072, 1073, 1074, 1075, 1076, 1077, 1078, 1079, 180, 181, 182, 183, 184, 185, 186, 187, 188, 189, 190, 191, 192, 193, 194, 480, 481, 482, 483, 484, 485, 486, 487, 488, 489, 490, 491, 492, 493, 494, 780, 781, 782, 783, 784, 785, 786, 787, 788, 789, 790, 791, 792, 793, 794, 1080, 1081, 1082, 1083, 1084, 1085, 1086, 1087, 1088, 1089, 1090, 1091, 1092, 1093, 1094, 195, 196, 197, 198, 199, 200, 201, 202, 203, 204, 205, 206, 207, 208, 209, 495, 496, 497, 498, 499, 500, 501, 502, 503, 504, 505, 506, 507, 508, 509, 795, 796, 797, 798, 799, 800, 801, 802, 803, 804, 805, 806, 807, 808, 809, 1095, 1096, 1097, 1098, 1099, 1100, 1101, 1102, 1103, 1104, 1105, 1106, 1107, 1108, 1109, 210, 211, 212, 213, 214, 215, 216, 217, 218, 219, 220, 221, 222, 223, 224, 510, 511, 512, 513, 514, 515, 516, 517, 518, 519, 520, 521, 522, 523, 524, 810, 811, 812, 813, 814, 815, 816, 817, 818, 819, 820, 821, 822, 823, 824, 1110, 1111, 1112, 1113, 1114, 1115, 1116, 1117, 1118, 1119, 1120, 1121, 1122, 1123, 1124, 225, 226, 227, 228, 229, 230, 231, 232, 233, 234, 235, 236, 237, 238, 239, 525, 526, 527, 528, 529, 530, 531, 532, 533, 534, 535, 536, 537, 538, 539, 825, 826, 827, 828, 829, 830, 831, 832, 833, 834, 835, 836, 837, 838, 839, 1125, 1126, 1127, 1128, 1129, 1130, 1131, 1132, 1133, 1134, 1135, 1136, 1137, 1138, 1139, 240, 241, 242, 243, 244, 245, 246, 247, 248, 249, 250, 251, 252, 253, 254, 540, 541, 542, 543, 544, 545, 546, 547, 548, 549, 550, 551, 552, 553, 554, 840, 841, 842, 843, 844, 845, 846, 847, 848, 849, 850, 851, 852, 853, 854, 1140, 1141, 1142, 1143, 1144, 1145, 1146, 1147, 1148, 1149, 1150, 1151, 1152, 1153, 1154, 255, 256, 257, 258, 259, 260, 261, 262, 263, 264, 265, 266, 267, 268, 269, 555, 556, 557, 558, 559, 560, 561, 562, 563, 564, 565, 566, 567, 568, 569, 855, 856, 857, 858, 859, 860, 861, 862, 863, 864, 865, 866, 867, 868, 869, 1155, 1156, 1157, 1158, 1159, 1160, 1161, 1162, 1163, 1164, 1165, 1166, 1167, 1168, 1169, 270, 271, 272, 273, 274, 275, 276, 277, 278, 279, 280, 281, 282, 283, 284, 570, 571, 572, 573, 574, 575, 576, 577, 578, 579, 580, 581, 582, 583, 584, 870, 871, 872, 873, 874, 875, 876, 877, 878, 879, 880, 881, 882, 883, 884, 1170, 1171, 1172, 1173, 1174, 1175, 1176, 1177, 1178, 1179, 1180, 1181, 1182, 1183, 1184, 285, 286, 287, 288, 289, 290, 291, 292, 293, 294, 295, 296, 297, 298, 299, 585, 586, 587, 588, 589, 590, 591, 592, 593, 594, 595, 596, 597, 598, 599, 885, 886, 887, 888, 889, 890, 891, 892, 893, 894, 895, 896, 897, 898, 899, 1185, 1186, 1187, 1188, 1189, 1190, 1191, 1192, 1193, 1194, 1195, 1196, 1197, 1198, 1199];

        assert_eq!(output, correct_output);
    }
}
