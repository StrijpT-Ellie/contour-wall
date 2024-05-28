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
//! ## Full Contour Wall mode (6 tiles)
//!
//! ```rust
//! use std::ffi::CString;
//! use contourwall_core::*;
//!
//! fn main() {
//!     let baud_rate = 2_000_000;
//!     let mut cw = new(baud_rate);
//!
//!     solid_color(&mut cw, 255, 0, 255); // Sets all LEDs to purple
//!     show(&mut cw); // Shows the changes on the LED tiles
//! }
//! ```
//!
//! ## Single tile mode
//!
//! ```rust
//! use std::ffi::CString;
//! use contourwall_core::*;
//!
//! fn main() {
//!     let com_port = CString::new("/dev/ttyUSB3").expect("CString conversion failed").into_raw();
//!     let baud_rate = 2_000_000;
//!     let mut cw = single_new_with_port(com_port, baud_rate);
//!
//!     solid_color(&mut cw, 255, 0, 255); // Sets all LEDs to purple
//!     show(&mut cw); // Shows the changes on the LED tiles
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

use std::ffi::c_char;

use log::{error, info, trace, warn};
use rayon::prelude::*;
use serialport::{Error, SerialPortInfo, SerialPortType};
use util::configure_logging;

use tile::Tile;

use crate::status_code::StatusCode;

pub mod status_code;
pub mod tile;
pub mod util;

/// ContourWallCore class encapsulates the list of connected tiles.
#[repr(C)]
#[derive(Debug)]
pub struct ContourWallCore {
    pub tiles_ptr: *mut Tile,
    pub tiles_len: usize,
}

/// Initializes the full ContourWall, all the configuration and orchistration happens automatically.
///
/// This sets up the ContourWall automatically. It checks each COM port to see if it is part of
/// the ContourWall. If the magic numbers are correct, the COM port is a tile. Then it asks each
/// tile for its identifier, which is the location on the wall. Based on that identifier,
/// the library knows which COM port is which tile. This lets the library know where to send
/// each part of a framebuffer to the right COM port.
///
/// ## Parameters
/// - baudrate: an unsigned 32bit integer, default value of 2.000.000
///
/// ## Returns
/// The initialized ContourWall is returned.
#[no_mangle]
pub extern "C" fn new(baud_rate: u32) -> ContourWallCore {
    fn error_handler(e: Error) -> Vec<SerialPortInfo> {
        error!("{}", e);
        Vec::new()
    }

    let ports = serialport::available_ports().unwrap_or_else(error_handler);

    // This could be written more optimally like this:
    // let tiles: Vec<Option<Tile>> = vec![None; 6];
    // but, that does not work due to .clone() not being implemented for Tile
    // .clone() cannot be implemented for Tile, due to the Tile::Port field.
    let mut tiles: Vec<Option<Tile>> = Vec::with_capacity(6);
    for _ in 0..6 {
        tiles.push(None);
    }

    for port in ports {
        let SerialPortType::UsbPort(_) = port.port_type else {
            trace!("Port: '{}' is a USB port", port.port_name);
            continue;
        };

        let tile = Tile::init(port.port_name.clone(), baud_rate);
        let mut tile = match tile {
            Ok(tile) => tile,
            Err(error) => {
                info!(
                    "'{}', is not an ELLIE tile, because: {:?}",
                    port.port_name, error
                );
                continue;
            }
        };

        let (status_code, identifier) = tile.command_4_get_tile_identifier();
        if status_code == StatusCode::Ok {
            tiles[identifier as usize - 1] = Some(tile);
        }
    }

    let mut tiles: Vec<Tile> = tiles.into_iter().flat_map(|tile| tile).collect();

    // TODO: Implement actual error that does not crash the program
    assert_eq!(
        tiles.len(),
        6,
        "[CW CORE ERROR] Only {}/6 tiles were found",
        tiles.len()
    );

    let tiles_ptr = tiles.as_mut_ptr();
    let tiles_len = tiles.len();
    configure_logging();
    if !configure_threadpool(tiles_len as u8) {
        warn!(
            "Failed to configure the threadpool with {} thread",
            tiles_len
        )
    }

    std::mem::forget(tiles);

    ContourWallCore {
        tiles_ptr,
        tiles_len,
    }
}

/// Initializes the full ContourWall, based on manualy input of COM ports.
///
/// ## Parameters
/// - com_port0: Device name of the COM port, 'com_port0' is the top-left tile
/// - com_port1: Device name of the COM port, 'com_port1' is the top-center tile
/// - com_port2: Device name of the COM port, 'com_port2' is the top-right tile
/// - com_port3: Device name of the COM port, 'com_port3' is the bottom-left tile
/// - com_port4: Device name of the COM port, 'com_port4' is the bottom-center tile
/// - com_port5: Device name of the COM port, 'com_port5' is the bottom right tile
/// - baudrate: an unsigned 32bit integer, default value of 2.000.000
///
/// ## Returns
/// The initialized ContourWall is returned.
#[no_mangle]
pub extern "C" fn new_with_ports(
    com_port0: *const c_char,
    com_port1: *const c_char,
    com_port2: *const c_char,
    com_port3: *const c_char,
    com_port4: *const c_char,
    com_port5: *const c_char,
    baud_rate: u32,
) -> ContourWallCore {
    let com_ports = vec![
        util::str_ptr_to_string(com_port0),
        util::str_ptr_to_string(com_port1),
        util::str_ptr_to_string(com_port2),
        util::str_ptr_to_string(com_port3),
        util::str_ptr_to_string(com_port4),
        util::str_ptr_to_string(com_port5),
    ];

    // Ensure we have exactly 6 ports
    assert_eq!(com_ports.len(), 6);

    let mut tiles: Vec<Tile> = Vec::with_capacity(6);

    for (i, com_port) in com_ports.into_iter().enumerate() {
        let tile = Tile::init(com_port.clone(), baud_rate);
        let tile = match tile {
            Ok(tile) => tile,
            Err(error) => {
                info!("'{}', is not an ELLIE tile, because: {:?}", com_port, error);
                continue;
            }
        };
        tiles[i] = tile;
    }

    let tiles_ptr = tiles.as_mut_ptr();
    let tiles_len = tiles.len();
    configure_logging();
    if !configure_threadpool(tiles_len as u8) {
        warn!(
            "Failed to configure the threadpool with {} thread",
            tiles_len
        )
    }

    std::mem::forget(tiles);

    ContourWallCore {
        tiles_ptr,
        tiles_len,
    }
}

/// Initializes the ContourWall as a single tile
///
/// ## Parameters
/// - com_port: the device name of the COM port
/// - baudrate: an unsigned 32bit integer, default value of 2.000.000
///
/// ## Returns
/// The initialized ContourWall is returned.
#[no_mangle]
pub extern "C" fn single_new_with_port(com_port: *const c_char, baud_rate: u32) -> ContourWallCore {
    let com_port = util::str_ptr_to_string(com_port);
    
    let tile = Tile::init(com_port.clone(), baud_rate);
    let tile = match tile {
        Ok(tile) => tile,
        Err(error) => {
            error!("'{}', is not an ELLIE tile, because: {:?}", com_port, error);
            todo!();
        }
    };

    let mut tiles = vec![tile];
    let tiles_ptr = tiles.as_mut_ptr();
    let tiles_len = tiles.len();
    configure_logging();
    if !configure_threadpool(tiles_len as u8) {
        error!(
            "Failed to configure the threadpool with {} thread",
            tiles_len
        )
    }

    std::mem::forget(tiles);

    ContourWallCore {
        tiles_ptr,
        tiles_len,
    }
}

/// Configures the amount of threads for the Rayon threadpool.
///
/// The default threadcount is the amount of tiles connected to the Contour Wall. If the full wall is
/// initialised then there are 6 threads. If the wall is in single tile mode, then there is only one thread.
#[no_mangle]
pub extern "C" fn configure_threadpool(threads: u8) -> bool {
    if threads > 6 {
        warn!(
            "A higher thread count than {}, is unnecessary as there is a maximum of 6 tiles",
            threads
        );
    }

    let res = rayon::ThreadPoolBuilder::new()
        .num_threads(threads as usize)
        .build_global();
    if res.is_err() {
        error!("Failed to set the threadpool threadcount to: {}", threads);
    }

    res.is_ok()
}

/// Executes the `command_0_show` on each tile to show their current framebuffer
///
/// The execution of the command on each tile is done concurrently.
///
/// ## Parameter
/// - this: a mutable pointer to the ContourWallCore object
#[no_mangle]
pub extern "C" fn show(this: &mut ContourWallCore) {
    let tiles: &mut [Tile] =
        unsafe { std::slice::from_raw_parts_mut(this.tiles_ptr, this.tiles_len) };

    tiles.par_iter_mut().for_each(|tile| {
        let _status_code = tile.command_0_show();
    });
}

/// Executes the `command_2_update_all` on each tile.
///
/// If the Contour Wall is in 6 tile mode, the framebuffer first gets split into 6 framebuffers,
/// one framebuffer for each tile.
///
/// The execution of the command on each tile is done concurrently.
///
/// ## Parameter
/// - this: a mutable pointer to the ContourWallCore object
/// - frame_buffer_ptr: pointer to framebuffer. If Contour Wall is in 6 tile mode the framebuffer is expected to be 7200 bytes big. In one tile mode, it is expected to be 1200 bytes big.

#[no_mangle]
pub extern "C" fn update_all(
    this: &mut ContourWallCore,
    frame_buffer_ptr: *const u8,
    optimize: bool,
) {
    let buffer_size = 1200 * this.tiles_len;

    let frame_buffer: &[u8] = unsafe { std::slice::from_raw_parts(frame_buffer_ptr, buffer_size) };
    let tiles: &mut [Tile] =
        unsafe { std::slice::from_raw_parts_mut(this.tiles_ptr, this.tiles_len) };

    if this.tiles_len == 1 {
        let tile = tiles
            .first_mut()
            .expect("There should at least be one tile");
        let _status_code = tile.command_2_update_all(frame_buffer, optimize);
    } else if this.tiles_len == 6 {
        let frame_buffers = util::split_framebuffer(frame_buffer);

        tiles.par_iter_mut().enumerate().for_each(|(i, tile)| {
            let _status_code = tile.command_2_update_all(frame_buffers[i].as_slice(), optimize);
        });
    } else {
        error!(
            "--> UNREACHABLE <-- Amount of tilesxis i  HAS to be either 1 or 6, not '{}'\n EXITING",
            this.tiles_len
        );
        unreachable!();
    }
}

/// Executes the `command_1_solid_color` on each tile.
///
/// The execution of the command on each tile is done concurrently.
///
/// ## Parameters
/// - this: a mutable pointer to the ContourWallCore object
/// - red: 8-bit value of color red
/// - green: 8-bit value of color red
/// - blue: 8-bit value of color red
#[no_mangle]
pub extern "C" fn solid_color(this: &mut ContourWallCore, red: u8, green: u8, blue: u8) {
    // This is the old code that is sequentially written
    // for tile in this.tiles {
    //     let _status_code = tile.as_ref().command_1_solid_color(red, green, blue);
    // }

    let tiles: &mut [Tile] =
        unsafe { std::slice::from_raw_parts_mut(this.tiles_ptr, this.tiles_len) };

    tiles.par_iter_mut().for_each(|tile| {
        let _status_code = tile.command_1_solid_color(red, green, blue);
    });
}

/// Transfers ownership of the ContourWallCore object back to Rust and frees the memory.
/// Also closes the serial connections
#[no_mangle]
pub extern "C" fn drop(this: *mut ContourWallCore) {
    if !this.is_null() {
        unsafe {
            let cw = Box::from_raw(this);
            std::mem::drop(cw);

            let tiles: Vec<Tile> =
                Vec::from_raw_parts((*this).tiles_ptr, (*this).tiles_len, (*this).tiles_len);
            std::mem::drop(tiles);
        }
    }
}

#[cfg(test)]
mod tests {
    use std::ffi::CString;

    use super::*;

    #[test]
    fn test_solid_color() {
        let com_string: *const c_char = CString::new("COM3")
            .expect("CString conversion failed")
            .into_raw();

        let mut cw = single_new_with_port(com_string, 2_000_000);

        solid_color(&mut cw, 255, 255, 255);
        show(&mut cw);

        
        assert!(false);
    }

    #[test]
    fn test_update_all() {
        let com_string: *const c_char = CString::new("COM3")
            .expect("CString conversion failed")
            .into_raw();

        let mut cw = single_new_with_port(com_string, 2_000_000);

        let mut buffer = vec![0; 1200];
        buffer[1150] = 255;
        buffer[0] = 255;
        buffer[59] = 255;

        update_all(&mut cw, buffer.as_ptr(), false);
        show(&mut cw);

        assert!(false);
    }
}
