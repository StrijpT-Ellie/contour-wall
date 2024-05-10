use contourwall_core::{
    new, new_with_ports, show, single_new_with_port, solid_color, update_all, ContourWallCore,
};
use serialport::{self, available_ports};
use std::{ffi::c_char, thread, time::Duration};
pub struct ContourWall {
    cw_core: ContourWallCore,
    pub pixels: ndarray::Array3<u8>,
    pub pushed_frames: u32,
}

impl ContourWall {
    pub fn new(baud_rate: u32) -> ContourWall {
        //new with zero title
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

pub fn hsv_to_rgb(h: u8, s: u8, v: u8) -> (u8, u8, u8) {
    let h: f32 = h as f32 / 255.;
    let s: f32 = s as f32 / 255.;
    let v: f32 = v as f32 / 255.;

    if s == 0.0 {
        return (h as u8 * 225, s as u8 * 225, v as u8 * 255);
    }

    let i = h * 6.;
    let f = (h * 6.) - i;
    let p = v * (1. - s);
    let q = v * (1. - s * f);
    let t = v * (1. - s * (1. - f));

    if i == 0. {
        return (v as u8 * 225, t as u8 * 225, p as u8 * 255);
    } else if i == 1. {
        return (q as u8 * 225, v as u8 * 225, p as u8 * 255);
    } else if i == 2. {
        return (p as u8 * 225, v as u8 * 225, t as u8 * 255);
    } else if i == 3. {
        return (p as u8 * 225, q as u8 * 225, v as u8 * 255);
    } else if i == 4. {
        return (t as u8 * 225, p as u8 * 225, v as u8 * 255);
    } else {
        return (v as u8 * 225, p as u8 * 225, q as u8 * 255);
    }
}

fn check_comport_existence(com_ports: Vec<&String>) -> bool {
    let ports = available_ports()
        .unwrap()
        .into_iter()
        .map(|port| port.port_name)
        .collect::<Vec<String>>();
    println!("{:?}", ports);
    for port in com_ports {
        if !ports.contains(&port) {
            return false;
        }
    }

    return true;
}

fn string_to_str_ptr(s: &str) -> *mut c_char {
    std::ffi::CString::new(s)
        .expect("CString conversion failed")
        .into_raw()
}

#[cfg(test)]
mod tests {
    use std::vec;
    use ndarray::{s, Array};

    use super::*;

    #[test]
    fn test_flash_all_colors() {
        let Ok(mut cw) = ContourWall::single_new_from_port(String::from("COM3"), 2_000_000) else {
            panic!("Port does not exist");
        };

        //set all pixels to RED
        cw.solid_color(0, 0, 255);
        cw.show(500, false);

        //set all pixels to RED
        cw.solid_color(0, 255, 255);
        cw.show(500, false);

        //set all pixels to GREEN
        cw.solid_color(0, 255, 0);
        cw.show(500, false);

        //set all pixels to GREEN
        cw.solid_color(255, 255, 0);
        cw.show(500, false);

        //set all pixels to BLUE
        cw.solid_color(255, 0, 0);
        cw.show(500, false);

        //set all pixels to WHITE
        cw.solid_color(255, 0, 255);
        cw.show(500, false);

        //set all pixels to BLACK
        cw.solid_color(0, 0, 0);
        cw.show(500, false);
    }

    #[test]
    fn test_fade_to_white() {
        let Ok(mut cw) = ContourWall::single_new_from_port(String::from("COM3"), 2_000_000) else {
            panic!("Port does not exist");
        };

        //slowly faded to white
        for i in 0..255 {
            cw.pixels
                .slice_mut(s![.., .., ..])
                .assign(&Array::from(vec![i, i, i]));
        }

        cw.solid_color(0, 0, 0);
        cw.show(10, false);
    }

    #[test]
    fn test_fade_colors() {
        let Ok(mut cw) = ContourWall::single_new_from_port(String::from("COM3"), 2_000_000) else {
            panic!("Port does not exist");
        };

        //slowly fade oever all HSV colors
        for i in 0..=255 {
            cw.pixels
                .slice_mut(s![.., .., ..])
                .assign(&Array::from(vec![i, 255, 255]));
        }

        cw.solid_color(0, 0, 0);
        cw.show(10, false);
    }

    #[test]
    fn test_moving_lines() {
        let Ok(mut cw) = ContourWall::single_new_from_port(String::from("COM3"), 2_000_000) else {
            panic!("Port does not exist");
        };

        let white = Array::from(vec![255, 255, 255]);
        let black = Array::from(vec![0, 0, 0]);

        //Move white line over the horizontal axis, from left to right
        for i in 0..=20 {
            cw.pixels.slice_mut(s![.., i, ..]).assign(&white);
            cw.show(10, false);
            cw.pixels.slice_mut(s![.., i, ..]).assign(&black);
        }

        //Move white line over the horizontal axis, from left to right
        for i in (0..=20).rev() {
            cw.pixels.slice_mut(s![.., i, ..]).assign(&white);
            cw.show(10, false);
            cw.pixels.slice_mut(s![.., i, ..]).assign(&black);
        }

        //Move white line over the vertical axis, from top to bottom
        for i in 0..=20 {
            cw.pixels.slice_mut(s![i, .., ..]).assign(&white);
            cw.show(10, false);
            cw.pixels.slice_mut(s![i, .., ..]).assign(&black);
        }

        //Move white line over the vertical axis, from bottom to top
        for i in (0..=20).rev() {
            cw.pixels.slice_mut(s![i, .., ..]).assign(&white);
            cw.show(10, false);
            cw.pixels.slice_mut(s![i, .., ..]).assign(&black);
        }

        cw.solid_color(0, 0, 0);
        cw.show(10, false);
    }

    #[test]
    fn test_turning_pixels_on_zigzag() {
        let Ok(mut cw) = ContourWall::single_new_from_port(String::from("COM3"), 2_000_000) else {
            panic!("Port does not exist");
        };

        let mut color = Array::from(vec![255, 255, 255]);

        for _ in 0..=2 {
            let mut left_to_right = true;

            for x in (0..=20).step_by(2) {

                //get iter range from left to right or vice versa based on choice
                let range_iter =  if left_to_right { 
                         (0..=20).step_by(2).collect::<Vec<_>>().into_iter()
                 } else { 
                    (0..=20).rev().step_by(2).collect::<Vec<_>>().into_iter()
                };

                //update the pixels in size of 2x2 every times
                for y in range_iter {
                    cw.pixels.slice_mut(s![y..(y + 2), x..(x + 2), ..]).assign(&color);
                    cw.show(10, false);
                }
                left_to_right = false;
            }

            color = Array::from(vec![0, 0, 0]);
        }
    }
}

// ----- fill all member with the same vector in ndarray  ---//
//let mut slice = 3d_array.slice_mut(s![..,1,..]);
//slice.assign(&filled_vector);

// ----- fill all member with the same value in ndarray  ---//
//let mut slice = 3d_array.slice_mut(s![..,1,..]);
//slice.fill(&filled_value);

// cw.pixels.map_axis_mut(ndarray::Axis(1),|mut row| {row.assign(&rgb_code).to_owned()});
