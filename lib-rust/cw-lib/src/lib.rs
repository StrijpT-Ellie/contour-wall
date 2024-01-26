use std::ffi::{c_char, CString};

use serialport::SerialPort;

#[repr(C)]
pub struct ContourWall {
    pub frame_time: u64,
    pub tx_buffer_size: u64,
    pub serial: Box<dyn SerialPort>,
    pub index_converter: [[u16; 20]; 20],
    pub last_serial_write_time: Instant,
}

#[no_mangle]
pub extern "C" fn init_contour_wall(com_port: *const c_char, baudrate: u64, frame_time: u64) -> ContourWall {
    // Safety: The input is assumed to be a valid C string (null-terminated)
    let c_str = unsafe { CString::from_raw(com_port as *mut c_char) };
    let com_port = c_str.to_str().unwrap();
    
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn it_works() {
        let result = add(2, 2);
        assert_eq!(result, 4);
    }
}
