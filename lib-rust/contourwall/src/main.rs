use std::time::{Duration, Instant};
use std::thread;
use std::vec::Vec;
use serialport::SerialPort;

struct ContourWall {
    pixels: [[[u16; 3]; 20]; 20],
    frame_time: u64,
    tx_buffer_size: usize,
    serial: Box<dyn SerialPort>,
    index_converter: [[u16; 20]; 20],
    last_serial_write_time: Instant,
}

impl ContourWall {
    fn new(com_port: &str, baudrate: u32, frame_time: u64) -> Self {
        let pixels = [[[0; 3]; 20]; 20];
        let tx_buffer_size = pixels.len() * pixels[0].len() * 3;
        let serial = serialport::new(com_port, baudrate)
            .timeout(Duration::from_secs(0))
            .open()
            .unwrap();

        let mut index_converter = [[0; 20]; 20];
        Self::generate_index_conversion_matrix(&mut index_converter);

        Self {
            pixels,
            frame_time,
            tx_buffer_size,
            serial,
            index_converter,
            last_serial_write_time: Instant::now(),
        }
    }

    fn show()

    fn show(&mut self, force_frame_time: bool) -> Result<u128, ()> {
        let mut buffer = vec![0; self.tx_buffer_size];
        let mut crc: u8 = 0;

        for (x, row) in self.pixels.iter().enumerate() {
            for (y, pixel) in row.iter().enumerate() {
                let index = self.index_converter[x][y] as usize;
                buffer[index * 3] = pixel[0] as u8;
                buffer[index * 3 + 1] = pixel[1] as u8;
                buffer[index * 3 + 2] = pixel[2] as u8;
                crc = crc.wrapping_add(pixel[0] as u8).wrapping_add(pixel[1] as u8).wrapping_add(pixel[2] as u8);
            }
        }

        buffer.push(crc);

        if force_frame_time {
            thread::sleep(Duration::from_millis(self.frame_time));
        } else if self.last_serial_write_time.elapsed().as_millis() < self.frame_time as u128 {
            let time_passed = self.last_serial_write_time.elapsed().as_millis() as u64;
            thread::sleep(Duration::from_millis(self.frame_time - time_passed));
        }

        self.serial.write_all(&buffer).expect("Failed to write to serial port");

        let frame_time = self.last_serial_write_time.elapsed().as_micros();
        self.last_serial_write_time = Instant::now();

        frame_time
    }

    fn set_frame_time(&mut self, frame_time: u64) {
        self.frame_time = frame_time;
    }

    fn get_frame_time(&self) -> u64 {
        self.frame_time
    }

    fn generate_index_conversion_matrix(index_converter: &mut [[u16; 20]; 20]) {
        for x in 0..20 {
            let mut row_start_value = x as u16;
            if x >= 15 {
                row_start_value = 300 + x as u16 - 15;
            } else if x >= 10 {
                row_start_value = 200 + x as u16 - 10;
            } else if x >= 5 {
                row_start_value = 100 + x as u16 - 5;
            }

            let mut y = 0;
            for index in (row_start_value..row_start_value + 100).step_by(5) {
                index_converter[x][y] = index;
                y += 1;
            }
        }
    }
}

fn main() {
    let com_port = "COM16"; // Replace with your COM port
    let baudrate = 921_600;
    let frame_time = 33;

    let mut contour_wall = ContourWall::new(com_port, baudrate, frame_time);

    // Example: Set a pixel color at (0, 0) to red
    contour_wall.pixels[0][0] = [255, 255, 0];

    let actual_frame_time = contour_wall.show(false);
    println!("Actual Frame Time: {} microseconds", actual_frame_time);
}
