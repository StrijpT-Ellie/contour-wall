use std::array::from_mut;
use std::ffi::{c_char, CStr};
use std::time::{Duration, SystemTime};
use serialport::SerialPort;

type StatusCodeAlias = u8;
type SerialPointer = *mut Box<dyn SerialPort>;

pub mod status_code;
pub use status_code::StatusCode;

#[repr(C)]
#[derive(Debug)]
pub struct ContourWallCore {
    pub frame_time: u64,
    serial: SerialPointer,
    last_serial_write_time: u64,
}

#[no_mangle]
pub extern "C" fn new(com_port: *const c_char, baudrate: u32) -> ContourWallCore {
    let mut serial = serialport::new(str_ptr_to_string(com_port), baudrate)
        .timeout(Duration::from_secs(0))
        .open()
        .unwrap();

    let _ = serial.set_stop_bits(serialport::StopBits::One);
    let _ = serial.set_parity(serialport::Parity::None);

    ContourWallCore {
        serial: Box::into_raw(Box::new(serial)) as SerialPointer,
        frame_time: 33,
        last_serial_write_time: millis_since_epoch(),
    }
}

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

    // Read response of tile 
    let read_buf = &mut[0; 1];
    if serial_read_slice(this.serial, read_buf).is_err() || StatusCode::new(read_buf[0]).is_none() {
        return StatusCode::ErrorInternal.as_u8()
    }

    read_buf[0]
}

#[no_mangle]
pub extern "C" fn command_1_solid_color(this: &mut ContourWallCore, red: u8, green: u8, blue: u8) -> StatusCodeAlias {
    let crc = red.wrapping_add(green).wrapping_add(blue);
    if write_to_serial_async(this.serial, &[1, red, green, blue, crc]).is_err() {
        return StatusCode::ErrorInternal.as_u8()
    }

    // Read response of tile 
    let read_buf = &mut[0; 1];
    if serial_read_slice(this.serial, read_buf).is_err() || StatusCode::new(read_buf[0]).is_none() {
        return StatusCode::ErrorInternal.as_u8()
    }

    read_buf[0]
}

#[no_mangle]
pub extern "C" fn command_2_update_all(this: &mut ContourWallCore, frame_buffer_ptr: *const u8, frame_buffer_size: u32) -> StatusCodeAlias {
    // Indicate to tile that command 2 is about to be executed
    if write_to_serial_async(this.serial, &[2]).is_err() {
        return StatusCode::ErrorInternal.as_u8()
    }

    // Generate framebuffer from pointer and generating the CRC by taking the sum of all the RGB values of the framebuffer
    let frame_buffer: &[u8] = unsafe { std::slice::from_raw_parts(frame_buffer_ptr, frame_buffer_size as usize) };
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
    if serial_read_slice(this.serial, read_buf).is_err() || StatusCode::new(read_buf[0]).is_none() {
        return StatusCode::ErrorInternal.as_u8()
    }

    read_buf[0]
}

#[no_mangle]
pub extern "C" fn command_3_update_specific_led(this: &mut ContourWallCore, frame_buffer_ptr: *const u8, frame_buffer_size: u32) -> StatusCodeAlias {
    // Indicate to tile that command 2 is about to be executed
    if write_to_serial_async(this.serial, &[3]).is_err() {
        return StatusCode::ErrorInternal.as_u8()
    }

    let pixel_count: u8 = (frame_buffer_size / 5).try_into().unwrap();
    if write_to_serial_async(this.serial, &[pixel_count, pixel_count]).is_err() {
        return StatusCode::ErrorInternal.as_u8()
    }
    
    // Reading the next
    let read_buf = &mut[0; 1];
    if serial_read_slice(this.serial, read_buf).is_err() || StatusCode::new(read_buf[0]).is_none() {
        return StatusCode::ErrorInternal.as_u8()
    }

    let status_code = StatusCode::new(read_buf[0]).unwrap();
    if status_code != StatusCode::Next {
        return status_code.as_u8();
    }

    // Generate framebuffer from pointer and generating the CRC by taking the sum of all the RGB values of the framebuffer
    let frame_buffer: &[u8] = unsafe { std::slice::from_raw_parts(frame_buffer_ptr, frame_buffer_size as usize) };
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
    if serial_read_slice(this.serial, read_buf).is_err() || StatusCode::new(read_buf[0]).is_none() {
        return StatusCode::ErrorInternal.as_u8()
    }

    read_buf[0]
}

#[no_mangle]
pub extern "C" fn command_4_get_tile_identifier(this: &mut ContourWallCore) -> u16 {
    if write_to_serial_async(this.serial, &[4]).is_err() {
        return StatusCode::ErrorInternal.as_u8() as u16;
    }
    
    let read_buf = &mut[0; 1];
    if serial_read_slice(this.serial, read_buf).is_err() || StatusCode::new(read_buf[1]).is_none() {
        return StatusCode::ErrorInternal.as_u8() as u16;
    }

    ((read_buf[0] as u16) << 8) + read_buf[1] as u16
}

#[no_mangle]
pub extern "C" fn command_5_set_tile_identifier(this: &mut ContourWallCore,  identifier: u8) -> StatusCodeAlias {
    if write_to_serial_async(this.serial, &[5, identifier, identifier]).is_err() {
        return StatusCode::ErrorInternal.as_u8()
    }

    let read_buf = &mut[0; 1];
    if serial_read_slice(this.serial, read_buf).is_err() || StatusCode::new(read_buf[0]).is_none() {
        return StatusCode::ErrorInternal.as_u8()
    }

    read_buf[0]
}

#[no_mangle]
pub extern "C" fn set_frame_time(this: &mut ContourWallCore, frame_time: u64) {
    this.frame_time = frame_time;
}

#[no_mangle]
pub extern "C" fn get_frame_time(this: &mut ContourWallCore) -> u64 {
    this.frame_time
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

// pub fn expect(this: &mut ContourWallCore, mut status_code: &mut StatusCode) -> bool {
//     let mut read_buf: Vec<u8> = vec![0; 1];
//     if serial_read_slice(this.serial, &mut read_buf).is_err() || StatusCode::new(read_buf[0]).is_none() {
//         status_code = &mut StatusCode::ErrorInternal;
//         return false;
//     }

//     // Processing the respose from the tile
//     let mut code = &mut StatusCode::new(read_buf[0]).unwrap();
//     status_code = code;
//     if code != status_code {
//          false
//     } else {
//         true
//     }
// }

fn serial_read_slice(serial: SerialPointer, buffer: &mut[u8]) -> Result<(), ()> {
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

fn write_to_serial_async(serial: SerialPointer, bytes: &[u8]) -> Result<usize, std::io::Error> {
    unsafe { (*serial).write(bytes) }
}

fn write_to_serial(serial: SerialPointer, bytes: &[u8]) -> Result<(), std::io::Error> {
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
        let framebuffer: Vec<u8> = vec![0, 4, 0, 255, 0, 0, 10, 0, 100, 100, 1, 100, 255, 0, 255];
        let com_string: *const c_char = CString::new("COM16").expect("CString conversion failed").into_raw();

        let mut cw = new(com_string, 921_600);
        let code = command_3_update_specific_led(&mut cw, framebuffer.as_ptr(), framebuffer.len() as u32);
        assert_eq!(code, 100, "testing if 'command_2_update_specific_led' works");

        let code = command_0_show(&mut cw);
        assert_eq!(code, 100, "testing if 'command_0_show' works");
    }

    #[test]
    fn update_all() {
        let mut framebuffer: Vec<u8> = vec![100; 1200];

        let com_string: *const c_char = CString::new("COM16").expect("CString conversion failed").into_raw();

        let mut cw = new(com_string, 921_600);

        let code = command_2_update_all(&mut cw, framebuffer.as_ptr(), framebuffer.len() as u32);
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