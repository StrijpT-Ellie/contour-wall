use std::ffi::c_char;

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
    tiles: [Box<Tile>; 6],
}

#[no_mangle]
pub extern "C" fn new(baud_rate: u32) -> ContourWallCore {
    fn error_handler(e: Error) -> Vec<SerialPortInfo> {
        println!("[CW CORE ERROR] {}", e);
        Vec::new()
    }

    let ports = serialport::available_ports().unwrap_or_else(error_handler);

    let mut tiles: Vec<Box<Tile>> = Vec::with_capacity(6);

    for port in ports {
        let SerialPortType::UsbPort(_) = port.port_type else {
            todo!();
        };

        let tile = Tile::init(port.port_name, baud_rate);
        let Ok(mut tile) = tile else { todo!() };

        let (status_code, identifier) = tile.command_4_get_tile_identifier();
        if status_code == StatusCode::Ok {
            tiles[identifier as usize - 1] = Box::new(tile);
        }
    }

    let tiles = tiles.try_into().unwrap();

    ContourWallCore { tiles }
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

    let mut tiles: [Box<Tile>; 6] = Default::default();

    for (i, com_port) in com_ports.into_iter().enumerate() {
        let tile = Tile::init(com_port, baud_rate);
        let Ok(tile) = tile else { todo!() };
        tiles[i] = Box::new(tile);
    }

    ContourWallCore { tiles }
}

#[no_mangle]
pub extern "C" fn show(this: &mut ContourWallCore) {
    // This is the old code that is sequentially written
    // for tile in &mut this.tiles {
    //     let _status_code = tile.as_mut().command_0_show();
    // }
    
    (&mut this.tiles).par_iter_mut().for_each(|tile| {
        let _status_code = tile.as_mut().command_0_show();
    });
}

#[no_mangle]
pub extern "C" fn update_all(this: &mut ContourWallCore, frame_buffer_ptr: *const u8) {
    let frame_buffer: &[u8] = unsafe { std::slice::from_raw_parts(frame_buffer_ptr, 7200) };
    let frame_buffers = util::split_framebuffer(frame_buffer);

    this.tiles.par_iter_mut().enumerate().for_each(|(i, tile)| {
        let x = frame_buffers[i].clone().as_mut_ptr();
        let _status_code = tile.as_mut().command_2_update_all(x);
    });
}

#[no_mangle]
pub extern "C" fn solid_color(this: &mut ContourWallCore, red: u8, green: u8, blue: u8) {
    // This is the old code that is sequentially written
    // for tile in this.tiles {
    //     let _status_code = tile.as_ref().command_1_solid_color(red, green, blue);
    // }

    (&mut this.tiles).par_iter_mut().for_each(|tile| {
        let _status_code = tile.as_mut().command_1_solid_color(red, green, blue);
    });
}

#[no_mangle]
pub extern "C" fn drop(this: *mut ContourWallCore) {
    if !this.is_null() {
        unsafe {
            let cw = Box::from_raw(this);
            std::mem::drop(cw);
        }
    }
}
