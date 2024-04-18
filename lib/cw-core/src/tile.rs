use std::{thread, time};
use std::time::{Duration, Instant};

use crate::{
    status_code::StatusCode,
    util::{generate_index_conversion_vector, millis_since_epoch},
};
use log::error;
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
}

impl Tile {
    /// Initializes the tile,
    ///
    /// It connects to the tile over serial, and asks for the magic numbers. If are not correct the connection is terminated.
    /// Otherwise the initialized tile is returned.
    /// 
    /// ## Parameters
    /// - port: string which is port location
    /// - baudrate: an unsigned 32bit integer, default value of 2.000.000
    /// 
    /// ## Returns
    /// 
    /// A Result is returned, the `Result::Ok` value contains the tile. If it is an `Result::Err`, it returns an `InitError`
    /// 
    /// ```
    /// let port = String::from("COM5"); // If on Linux, the port is going to look something like this /dev/ttyUSB5
    /// let baudrate: u32 = 2_000_000; // Default speed of 2MHz
    /// 
    /// let tile: Tile = Tile::init(port, baudrate).expect("Tile initialization is unsuccessful.");
    /// ```
    pub fn init(port: String, baudrate: u32) -> Result<Tile, InitError> {
        let Ok(port) = serialport::new(&port, baudrate)
            .timeout(Duration::from_millis(25))
            .stop_bits(serialport::StopBits::One)
            .parity(serialport::Parity::None)
            .open()
        else {
            return Result::Err(InitError::FailedToOpenConnection);
        };

        let mut tile = Tile {
            port: port,
            frame_time: 15,
            last_serial_write_time: 0,
            index_converter_vector: generate_index_conversion_vector(),
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
        
        // Ok(tile)
    }

    /// Executes `command_0_show` of the protocol.
    ///
    /// This command signals to the tile that the its current framebuffer needs to be displayed or shown.
    /// It expects a `100` or StatusCode::Ok, which is being returned by the tile _before_ it update its LED's.
    ///
    /// The time in between calls needs to be atleast `ContourWallCore::frame_time` (this), which by default is 33ms.
    ///
    /// ## Return
    /// - StatusCode 
    ///
    /// ## Example
    /// ```
    /// let mut tile: Tile = Tile::init(com_port, baud_rate).expect("Init is unsuccesfull");
    ///
    /// let status_code = cw.command_0_show();
    /// ```
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

    /// Executes `command_1_solid_color` of the protocol, which sets *all* pixels on a tile to one specific color.
    ///
    /// Although possible, the function is not meant for developers to call this function "bare"
    /// The intent of this function is for background optimizations. If the vast majority of the framebuffer is one color,
    /// than you could execute two protocol commands, E.G. `command_1_solid_color()` and `command_3_update_specific_led`.
    /// A background optimization could lead to faster frame times.
    ///
    /// ## Parameters
    /// - red: 8-bit value of color red
    /// - green: 8-bit value of color red
    /// - blue: 8-bit value of color red
    ///
    /// ## Return
    /// - StatusCode
    ///
    /// ## Examples
    ///
    /// Sets all LEDs on tile to purple
    /// ```
    /// let mut tile: Tile = Tile::init(com_port, baud_rate).expect("Init is unsuccesfull");
    ///
    /// let red: u8 = 255;
    /// let green: u8 = 0;
    /// let blue: u8 = 255;
    ///
    /// let status_code = tile.command_1_solid_color(red, green ,blue);
    /// let status_code = tile.command_0_show();
    /// ```
    ///
    /// Fades tiles from black to white
    /// ```
    /// let mut tile: Tile = Tile::init(com_port, baud_rate).expect("Init is unsuccesfull");
    ///
    /// for i in 0..255 {
    ///     let status_code = tile.command_1_solid_color(i, i ,i);
    ///
    ///     let status_code = tile.command_0_show();
    /// }
    /// ```
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
    /// - frame_buffer: the framebuffer array
    ///
    /// ## Return
    /// - StatusCode
    ///
    /// ## Example
    ///
    /// Sets first LED to RED, the rest is set to black (off)
    /// ```
    /// let mut tile: Tile = Tile::init(com_port, baud_rate).expect("Init is unsuccesfull");
    ///
    /// let mut framebuffer = &mut[0; 1200];
    /// framebuffer[0] = 255;
    ///
    /// let status_code = tile.command_2_update_all(framebuffer);
    /// ```
    pub fn command_2_update_all(&mut self, frame_buffer_unordered: &[u8]) -> StatusCode {
        let timespan = millis_since_epoch() - self.last_serial_write_time;
        if timespan < self.frame_time.into() {
            std::thread::sleep(Duration::from_millis((self.frame_time as u64) - timespan));
        }

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
    /// - frame_buffer: the framebuffer array
    ///
    /// ## Return
    /// - StatusCode 
    ///
    /// ## Example
    ///
    /// Sets 4th LED to red, 256th LED to blue
    /// ```
    /// let mut tile: Tile = Tile::init(com_port, baud_rate).expect("Init is unsuccesfull");
    /// let framebuffer = &[0, 3, 255, 0, 0, 1, 0, 0, 0, 255];
    ///
    /// let status_code = tile.command_3_update_specific_led(framebuffer);
    /// ```
    pub fn command_3_update_specific_led(
        &mut self,
        frame_buffer: &[u8],
    ) -> StatusCode {
        // Indicate to tile that command 3 is about to be executed
        if self.write_over_serial(&[3]).is_err() {
            return StatusCode::ErrorInternal;
        }
        
        assert_eq!(frame_buffer.len(), 255 * 5, "When using command_3_update_specific_led you cannot transfer more then 255 LED");

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

    
    /// Executes `command_4_get_tile_identifier` of the protocol. Returns the tile identifier which is set in the EEPROM of the ESP32
    ///
    /// Returns an tuple of which the first element is the StatusCode and the second element is the actual identifier.
    ///
    /// ## Example
    /// ```
    /// let mut tile: Tile = Tile::init(com_port, baud_rate).expect("Init is unsuccesfull");
    ///
    /// let (status_code, identifier) = tile.command_4_get_tile_identifier();
    /// ```
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

    /// Executes `command_5_set_tile_identifier` of the protocol. Sets a new tile identifier in the EEPROM of the ESP32
    ///
    /// *WARNING*: DO NOT USE 0 AS AN ADDRESS.
    /// ## Example
    /// ```
    /// let mut tile: Tile = Tile::init(com_port, baud_rate).expect("Init is unsuccesfull");
    ///
    /// let status_code = tile.command_4_set_tile_identifier(4);
    /// ```
    pub fn command_5_set_tile_identifier(&mut self, identifier: u8) -> StatusCode {
        if identifier == 0 {
            error!("Cannot set a tile identifier to 0");
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

    /// Executes `command_6_magic_numbers` of the protocol. Returns the 5 magic_numbers of the tile
    /// 
    /// The magic numbers are the ASCII values of the word: "Ellie".
    ///
    /// ## Example
    /// ```
    /// let mut tile: Tile = Tile::init(com_port, baud_rate).expect("Init is unsuccesfull");
    ///
    /// let magic_numbers = tile.command_6_magic_numbers()[0..5]
    ///     .into_iter()
    ///     .map(|&x| x as char)
    ///     .collect::<String>();
    ///     
    /// if magic_numbers != "Ellie" {
    ///     pritnln!("Tile is not part of ELLIE");
    /// } else {
    ///     pritnln!("Tile is part of ELLIE");
    /// }
    /// ```
    pub fn command_6_magic_numbers(&mut self) -> [u8; 5] {
        if self
            .write_over_serial(&[6])
            .is_err()
        {
            return [0, 0, 0, 0, 0];
        }

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

        let size = match port.read(buffer) {
            Ok(size) => size,
            Err(e) => {
                error!("Error occurred during reading of Serial buffer: {}", e);
                let _ = port.clear(serialport::ClearBuffer::All);
                return Err(());
            }
        };

        if size == buffer.len() {
            Ok(())
        } else {
            error!(
                "Only {}/{} bytes were received within the {}ms allocated time",
                port.bytes_to_read().unwrap_or(666),
                buffer.len(),
                port.timeout().as_millis()
            );
            let _ = port.clear(serialport::ClearBuffer::All);
            Err(())
        }
    }

    fn write_over_serial(&mut self, bytes: &[u8]) -> Result<usize, std::io::Error> {
        let port = self.port.as_mut();
        port.write(bytes)
    }
}
