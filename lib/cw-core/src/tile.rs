use std::time::Duration;

use crate::{
    status_code::StatusCode,
    util::{generate_index_conversion_vector, extract_mutated_pixels, millis_since_epoch},
};
use serialport::SerialPort;

#[derive(Debug)]
pub enum InitError {
    NotAnEllieTile,
    FailedToOpenConnection,
}

#[derive(Debug)]
pub struct Tile {
    pub frame_time: u64,
    last_serial_write_time: u64,
    port: Box<dyn SerialPort>,

    index_converter_vector: [usize; 1200],
    previous_framebuffer: [u8; 1200],
}

impl Tile {
    pub fn init(port: String, baudrate: u32) -> Result<Tile, InitError> {
        let Ok(port) = serialport::new(&port, baudrate)
            .timeout(Duration::from_secs(0))
            .stop_bits(serialport::StopBits::One)
            .parity(serialport::Parity::None)
            .open()
        else {
            return Result::Err(InitError::FailedToOpenConnection);
        };

        let mut tile = Tile {
            port: port,
            frame_time: 33,
            last_serial_write_time: millis_since_epoch(),

            index_converter_vector: generate_index_conversion_vector(),
            previous_framebuffer: [0u8; 1200],
        };

        let magic_numbers = tile.command_6_magic_numbers()[0..5]
            .into_iter()
            .map(|&x| x as char)
            .collect::<String>();

        if magic_numbers != "Ellie" {
            tile.drop();
            Result::Err(InitError::NotAnEllieTile)
        } else {
            Result::Ok(tile)
        }
    }

    pub fn command_0_show(&mut self) -> StatusCode {
        // Sleeping if the time between "show" commands to too little. The frametimes cannot be shorter than ContourWallCore::frame_time.
        // This calculates the left over time for the thread to sleep, if any at all.
        let timespan = millis_since_epoch() - self.last_serial_write_time;
        if timespan < self.frame_time.into() {
            std::thread::sleep(Duration::from_millis((self.frame_time as u64) - timespan));
        }

        if self.write_over_serial(&[0]).is_err() {
            StatusCode::ErrorInternal
        } else {
            self.last_serial_write_time = millis_since_epoch();
            StatusCode::Ok
        }
    }

    pub fn command_1_solid_color(&mut self, red: u8, green: u8, blue: u8) -> StatusCode {
        let crc = red.wrapping_add(green).wrapping_add(blue);
        if self.write_over_serial(&[1, red, green, blue, crc]).is_err() {
            return StatusCode::ErrorInternal;
        }

        // Read response of tile
        let read_buf = &mut [0; 1];
        if self.read_from_serial(read_buf).is_err() || StatusCode::new(read_buf[0]).is_none() {
            StatusCode::ErrorInternal
        } else {
            StatusCode::new(read_buf[0]).unwrap()
        }
    }

    pub fn command_2_update_all(&mut self, frame_buffer_unordered: &[u8]) -> StatusCode {
        // Indicate to tile that command 2 is about to be executed
        if self.write_over_serial(&[2]).is_err() {
            return StatusCode::ErrorInternal;
        }

     
        // Generate framebuffer from pointer and generating the CRC by taking the sum of all the RGB values of the framebuffer
        let mut frame_buffer = [0; 1201];
        let mut crc: u8 = 0;

        for (i, byte) in frame_buffer_unordered.into_iter().enumerate() {
            crc += *byte;
            frame_buffer[self.index_converter_vector[i]] = *byte;
        }
       
        let mutated_frame_buffer = extract_mutated_pixels(&mut self.previous_framebuffer,frame_buffer[0..1200].try_into().unwrap());

        // comparing th
        if mutated_frame_buffer.len() / 5 < 100 {
            let sent_mutated_frame_buffer: &[u8] = &mutated_frame_buffer;
            return self.command_3_update_specific_led(sent_mutated_frame_buffer);
        }


        frame_buffer[1200] = crc;

        // Write framebuffer over serial to tile
        if self.write_over_serial(&frame_buffer).is_err() {
            return StatusCode::ErrorInternal;
        }

        // Read response of tile
        let read_buf = &mut [0; 1];
        if self.read_from_serial(read_buf).is_err() || StatusCode::new(read_buf[0]).is_none() {
            StatusCode::ErrorInternal
        } else {
            StatusCode::new(read_buf[0]).unwrap()
        }
    }

    pub fn command_3_update_specific_led(&mut self, frame_buffer: &[u8]) -> StatusCode {
        // Indicate to tile that command 3 is about to be executed
        if self.write_over_serial(&[3]).is_err() {
            return StatusCode::ErrorInternal;
        }

        assert_eq!(
            frame_buffer.len(),
            255 * 5,
            "When using command_3_update_specific_led you cannot transfer more then 255 LED"
        );

        let led_count = (frame_buffer.len() / 5) as u8;
        if self.write_over_serial(&[led_count, led_count]).is_err() {
            return StatusCode::ErrorInternal;
        }

        // Reading the next
        let read_buf = &mut [0; 1];
        if self.read_from_serial(read_buf).is_err() || StatusCode::new(read_buf[0]).is_none() {
            return StatusCode::ErrorInternal;
        }

        let status_code = StatusCode::new(read_buf[0]).unwrap();
        if status_code != StatusCode::Next {
            return status_code;
        }

        // Generate framebuffer from pointer and generating the CRC by taking the sum of all the RGB values of the framebuffer
        let mut crc: u8 = 0;
        for byte in frame_buffer {
            crc += *byte;
        }
        let binding = [frame_buffer, &[crc]].concat();
        let frame_buffer = binding.as_slice();

        // Write framebuffer over serial to tile
        if self.write_over_serial(frame_buffer).is_err() {
            return StatusCode::ErrorInternal;
        }

        let read_buf = &mut [0; 1];
        if self.read_from_serial(read_buf).is_err() || StatusCode::new(read_buf[0]).is_none() {
            StatusCode::ErrorInternal
        } else {
            StatusCode::new(read_buf[0]).unwrap()
        }
    }

    pub fn command_4_get_tile_identifier(&mut self) -> (StatusCode, u8) {
        if self.write_over_serial(&[4]).is_err() {
            return (StatusCode::ErrorInternal, 0);
        }

        let read_buf = &mut [0; 3];
        if self.read_from_serial(read_buf).is_err() {
            return (StatusCode::ErrorInternal, 0);
        }

        if StatusCode::new(read_buf[2]).is_none() {
            (StatusCode::ErrorInternal, 0)
        } else {
            if read_buf[0] != read_buf[1] {
                (StatusCode::NonMatchingCRC, 0)
            } else {
                (StatusCode::new(read_buf[2]).unwrap(), read_buf[0])
            }
        }
    }

    pub fn command_5_set_tile_identifier(&mut self, identifier: u8) -> StatusCode {
        if identifier == 0 {
            eprintln!("[CW CORE ERROR] Cannot set a tile identifier to 0");
            return StatusCode::Error;
        }

        if self
            .write_over_serial(&[5, identifier, identifier])
            .is_err()
        {
            return StatusCode::ErrorInternal;
        }

        let read_buf = &mut [0; 1];
        if self.read_from_serial(read_buf).is_err() || StatusCode::new(read_buf[0]).is_none() {
            StatusCode::ErrorInternal
        } else {
            StatusCode::new(read_buf[0]).unwrap()
        }
    }

    pub fn command_6_magic_numbers(&mut self) -> [u8; 5] {
        let read_buf = &mut [0; 5];

        if self.read_from_serial(read_buf).is_err() {
            [0, 0, 0, 0, 0]
        } else {
            *read_buf
        }
    }

    /// Transfers ownership of the ContourWallCore object back to Rust and frees the memory.
    /// Also closes the serial connections
    pub fn drop(self) {
        std::mem::drop(self);
    }

    fn read_from_serial(&mut self, buffer: &mut [u8]) -> Result<(), ()> {
        let port = self.port.as_mut();
        let start = millis_since_epoch();
        let time_to_receive_ms = 30;
        while port
            .bytes_to_read()
            .expect("Cannot get bytes from serial read buffer")
            < buffer.len() as u32
        {
            if (millis_since_epoch() - start) > time_to_receive_ms {
                eprintln!(
                    "[CW CORE ERROR] Only {}/{} bytes were received within the {}ms allocated time",
                    port.bytes_to_read().unwrap(),
                    buffer.len(),
                    time_to_receive_ms
                );
                let _res = port.clear(serialport::ClearBuffer::Input);
                return Err(());
            }
        }

        if let Err(e) = port.read_exact(buffer) {
            eprintln!(
                "[CW CORE ERROR] Error occured during reading of Serial buffer: {}",
                e
            );
            Err(())
        } else {
            Ok(())
        }
    }

    fn write_over_serial(&mut self, bytes: &[u8]) -> Result<usize, std::io::Error> {
        let port = self.port.as_mut();
        port.write(bytes)
    }
}
