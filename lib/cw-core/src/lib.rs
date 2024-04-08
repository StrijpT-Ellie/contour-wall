use serialport::{Error, SerialPortInfo, SerialPortType};

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
pub extern "C" fn show(this: &mut ContourWallCore) {
    for tile in &mut this.tiles {
        let _status_code = tile.as_mut().command_0_show();
    }
}

#[no_mangle]
pub extern "C" fn update_all(this: &mut ContourWallCore, frame_buffer_ptr: *const u8) {
    let frame_buffer: &[u8] = unsafe { std::slice::from_raw_parts(frame_buffer_ptr, 7200) };
    let mut frame_buffers = util::split_framebuffer(frame_buffer);

    // TODO: Make this for-loop concurrent so the tile.command_2_update_all function,
    // for all six tiles is called at the same time insteaf of sequentually.
    // This will result in a 4x performance increase
    for (i, frame_buffer) in frame_buffers.iter_mut().enumerate() {
        let _status_code = this.tiles[i].as_mut().command_2_update_all(frame_buffer.as_mut_ptr());
    }
}

#[no_mangle]
pub extern "C" fn solid_color(this: &mut ContourWallCore, red: u8, green: u8, blue: u8) {
    for tile in &mut this.tiles {
        let _status_code = tile.as_mut().command_1_solid_color(red, green, blue);
    }
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
