use std::ffi::c_char;

use log::{info, warn, error, debug, trace};
use util::configure_logging;
use serialport::{Error, SerialPortInfo, SerialPortType};
use rayon::prelude::*;

use tile::Tile;

use crate::status_code::StatusCode;

pub mod status_code;
pub mod tile;
pub mod util;

#[repr(C)]
#[derive(Debug)]
pub struct ContourWallCore {
    tiles_ptr: *mut Tile,
    tiles_len: usize,
}

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
        let SerialPortType::UsbPort(USB_port) = port.port_type else {
            trace!("Port: '{}' is a USB port", port.port_name);
            continue;
        };

        let tile = Tile::init(port.port_name.clone(), baud_rate);
        let mut tile = match tile {
            Ok(tile) => tile,
            Err(error) => { 
                info!("'{}', is not an ELLIE tile, because: {:?}", port.port_name, error);
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
    assert_eq!(tiles.len(), 6, "[CW CORE ERROR] Only {}/6 tiles were found", tiles.len());

    let tiles_ptr = tiles.as_mut_ptr();
    let tiles_len = tiles.len();
    configure_logging();
    if !configure_threadpool(tiles_len as u8) {
        warn!("Failed to configure the threadpool with {} thread", tiles_len)
    }

    std::mem::forget(tiles);

    ContourWallCore { tiles_ptr, tiles_len }
}

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
        warn!("Failed to configure the threadpool with {} thread", tiles_len)
    }

    std::mem::forget(tiles);

    ContourWallCore { tiles_ptr, tiles_len }
}

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
        error!("Failed to configure the threadpool with {} thread", tiles_len)
    }

    std::mem::forget(tiles);

    ContourWallCore {
        tiles_ptr, tiles_len
    }
}

#[no_mangle]
pub extern "C" fn configure_threadpool(threads: u8) -> bool {
    let res = rayon::ThreadPoolBuilder::new().num_threads(threads as usize).build_global();
    if res.is_err() {
        error!("Failed to set the threadpool threadcount to: {}", threads);
    }

    res.is_ok()
}

/// Executes the `command_0_show` on each tile to show their current framebuffer
#[no_mangle]
pub extern "C" fn show(this: &mut ContourWallCore) {
    let tiles: &mut [Tile] = unsafe { std::slice::from_raw_parts_mut(this.tiles_ptr, this.tiles_len) };

    tiles.par_iter_mut().for_each(|tile| {
        let _status_code = tile.command_0_show();
    });
}

#[no_mangle]
pub extern "C" fn update_all(this: &mut ContourWallCore, frame_buffer_ptr: *const u8) {
    let buffer_size = 1200 * this.tiles_len;

    let frame_buffer: &[u8] = unsafe { std::slice::from_raw_parts(frame_buffer_ptr, buffer_size) };
    let tiles: &mut [Tile] = unsafe { std::slice::from_raw_parts_mut(this.tiles_ptr, this.tiles_len) };

    if this.tiles_len == 1 {
        let tile = tiles.first_mut().expect("There should at least be one tile");
        let _status_code = tile.command_2_update_all(frame_buffer);
    } else if this.tiles_len == 6 {
        let frame_buffers = util::split_framebuffer(frame_buffer);
    
        tiles.par_iter_mut().enumerate().for_each(|(i, tile)| {
            let _status_code = tile.command_2_update_all(frame_buffers[i].as_slice());
        });
    } else {
        error!("--> UNREACHABLE <-- Amount of tiles HAS to be either 1 or 6, not '{}'\n EXITING", this.tiles_len);
        unreachable!();
    }
}

#[no_mangle]
pub extern "C" fn solid_color(this: &mut ContourWallCore, red: u8, green: u8, blue: u8) {
    // This is the old code that is sequentially written
    // for tile in this.tiles {
    //     let _status_code = tile.as_ref().command_1_solid_color(red, green, blue);
    // }

    let tiles: &mut [Tile] = unsafe { std::slice::from_raw_parts_mut(this.tiles_ptr, this.tiles_len) };
        
    tiles.par_iter_mut().for_each(|tile| {
        let status_code = tile.command_1_solid_color(red, green, blue);
    });
}

#[no_mangle]
pub extern "C" fn drop(this: *mut ContourWallCore) {
    if !this.is_null() {
        unsafe {
            let cw = Box::from_raw(this);
            std::mem::drop(cw);

            let tiles: Vec<Tile> = Vec::from_raw_parts((*this).tiles_ptr, (*this).tiles_len, (*this).tiles_len);
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
        let com_string: *const c_char = CString::new("COM5")
            .expect("CString conversion failed").into_raw();

        let mut cw = single_new_with_port(com_string, 2_000_000);

        solid_color(&mut cw, 255, 255, 255);
        show(&mut cw);

        assert!(false);
    }

    #[test]
    fn test_update_all() {
        let com_string: *const c_char = CString::new("COM5")
            .expect("CString conversion failed").into_raw();

        let mut cw = single_new_with_port(com_string, 2_000_000);

        let mut buffer = vec![0; 1200];
        buffer[1150] = 255;
        buffer[0] = 255;
        buffer[59] = 255;

        update_all(&mut cw, buffer.as_ptr());
        show(&mut cw);
        
        assert!(false);
    }
}