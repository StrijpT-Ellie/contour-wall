use contourwall_core::{new, new_with_ports, single_new_with_port, show, solid_color, update_all, ContourWallCore};
use serialport::{self, available_ports};
use std::{ffi::c_char, thread, time::Duration};
// type Result<T> = std::result::Result<T, InitialError>;

// struct InitialError;

// trait Commanding {
//     fn new(baud_rate: u32) -> Self;

//     fn new_with_ports(&self, ports: [&String; 6], baud_rate: u32) -> Self;

//     fn show(&mut self, sleep_ms: u64, optimize: bool);

//     fn solid_color(&mut self, red: u8, green: u8, blue: u8);
// }

pub struct ContourWall {
    cw_core: ContourWallCore,
    pub pixels: ndarray::Array3<u8>,
    pub pushed_frames: u32,
}

impl ContourWall {
    pub fn new(baud_rate: u32) -> ContourWall { //new with zero title
        ContourWall {
            cw_core: new(baud_rate),
            pixels: ndarray::Array3::<u8>::zeros((20, 20, 3)),
            pushed_frames: 0,
        }
    }

    //TODO handle the error properly - check array type of &string is safe
    pub fn new_with_ports(ports: [&String; 6], baud_rate: u32) -> Result<ContourWall, ()> {
        if check_comport_existence(ports.to_vec()) {
            Ok(ContourWall {
                cw_core: new_with_ports(
                    string_to_str_ptr(ports[0]),
                    string_to_str_ptr(ports[1]),
                    string_to_str_ptr(ports[2]),
                    string_to_str_ptr(ports[3]),
                    string_to_str_ptr(ports[4]),
                    string_to_str_ptr(ports[5]),
                    baud_rate,
                ),
                pixels: ndarray::Array3::<u8>::zeros((20, 20, 3)),
                pushed_frames: 0,
            })
        } else {
            Err(())
        }
    }

    pub fn single_new_from_port(port: String, baudrate: u32) -> Result<ContourWall, ()> {
        if check_comport_existence(vec![&port]) {
            Ok(ContourWall {
                cw_core: single_new_with_port(string_to_str_ptr(&port), baudrate),
                pixels: ndarray::Array3::<u8>::zeros((20, 20, 3)),
                pushed_frames: 0,
            })
        } else {
            Err(())
        }
        
    }

    //TODO - get the latest version of cw-core so update all has the optimize choce
    /// update each single LED on the ContourWallCore with the pixel data in cw.pixels
    pub fn show(&mut self, sleep_ms: u64, optimize: bool) {
        update_all(&mut self.cw_core, self.pixels.as_ptr(), optimize);
        show(&mut self.cw_core);
        self.pushed_frames += 1;
        thread::sleep(Duration::from_millis(sleep_ms))
    }

    /// Turns all the pixel colors to the given values
    pub fn solid_color(&mut self, red: u8, green: u8, blue: u8) {
        solid_color(&mut self.cw_core, red, green, blue)
    }
}

pub fn hsv_to_rgb(h: u64, s: u64, v: u64) -> (u64, u64, u64) {
    // let h:f64 = h / 255;
    // let s:f64 = s / 255;
    // let v:f64 = v / 255;

    // if s == 0.0
    // {
    //     return (h*225, s*225, v*255)
    // }

    // let  i = h * 6 ;
    // let f = (h * 6.) - i  
    // let p = v * (1. - s)
    // let q = v * (1. - s * f)
    // let  t = v * (1. - s * (1. - f))

    // if i == 0{
    //     return int(v * 255), int(t * 255), int(p * 255)}
    // elif i == 1:
    //     return int(q * 255), int(v * 255), int(p * 255)
    // elif i == 2:
    //     return int(p * 255), int(v * 255), int(t * 255)
    // elif i == 3:
    //     return int(p * 255), int(q * 255), int(v * 255)
    // elif i == 4:
    //     return int(t * 255), int(p * 255), int(v * 255)
    // else:
    //     return int(v * 255), int(p * 255), int(q * 255)
    return (0,0,0)
}

fn check_comport_existence(com_ports: Vec<&String>) -> bool {
    let ports = available_ports().unwrap().into_iter().map(|port| port.port_name).collect::<Vec<String>>();
    println!("{:?}", ports);
    for port in com_ports {
        if !ports.contains(&port) {
            return false;
        }
    }

    return true;
}

fn string_to_str_ptr(s: &str) -> *mut c_char {
    std::ffi::CString::new(s).expect("CString conversion failed").into_raw()
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_one_tile() {
       let Ok(mut cw) = ContourWall::single_new_from_port(String::from("COM3"), 2_000_000) else {
            panic!("Port does not exist");
       };

       cw.pixels[[0, 0, 0]] = 255;
       cw.pixels[[10, 0, 1]] = 255;
       cw.pixels[[0, 0, 2]] = 255;

       cw.show(0, false)
    }
}