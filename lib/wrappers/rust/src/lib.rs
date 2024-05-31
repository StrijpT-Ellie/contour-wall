use contourwall_core::{
    new, new_with_ports, show, single_new_with_port, update_all, ContourWallCore,
};


use serialport::{self, available_ports};
use std::{ffi::c_char, thread, time::Duration};

/// # Description
/// The ContourWall takse responsible for managing on how frame is pushed to the title via its members.
///
/// # Struct members
///  - cw_core: having the type of ContourWallCore. The cw_core play the role of title administration with 2 functionalities.
//   setting up the ContourWall with configurations and managing the sending buffer tasks following different type of commands.
///
///  - pixels: having the type of ndarray::Array3<u8> with the shape of 20x20x3. This is a 3D arrays that representS the pixels frame.
///  
///  - pushed_frame: an unsigned 32bit integer. this integer counts the number of frames that is pushed to the titles.
pub struct ContourWall {
    cw_core: ContourWallCore,
    pub pixels: ndarray::Array3<u8>,
    pub pushed_frames: u32,
}

impl ContourWall {
    ///Initialise the ContourWall, all the configuration and orchistration of the ContourWallCore happens automatically.
    ///
    /// # Parameters
    /// - Baudrate: an unsigned 32bit integer.
    ///
    /// # Returns
    /// - The initialised ContourWall is return.
    pub fn new(baud_rate: u32) -> ContourWall {
        //new with zero title
        ContourWall {
            cw_core: new(baud_rate),
            pixels: ndarray::Array3::<u8>::zeros((20, 20, 3)),
            pushed_frames: 0,
        }
    }

    ///Initialise the ContourWall, the fixed 6 ports are manually setup by the user to the ContourWallCore.
    ///
    ///# Parameters
    /// - ports: an fixed string arrays with the lengths of 6. this array stores the 6 configured ports.
    /// - Baudrate: an unsigned 32bit integer.
    ///
    /// #Returns
    /// - the intiialised Contourwall is return.
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

    ///Initialise the ContourWall with only one port.
    ///
    ///# Parameters
    ///  - port: the string name of the port.
    ///  - baudrate: an unsigned 32bit integer.
    ///  
    /// # Returns
    ///  - the initialised ContourWall is return.
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

    /// Update each single LED on the ContourWallCore with the pixel data in cw.pixels. It has the choice of
    /// using the optimisation algorithm, which allows the buffer is updated in more efficient way in term of speed.
    /// In order to use the show_w function to update with the newly pixel frames, the pixels 3D arrays of
    /// the CounterWall must be first update.
    ///
    /// #parameters
    ///  - sleep_ms: an unsigned 64bit integer.time before pushing another frame
    ///  - optimize: a boolean. Selection of turning on the optimisation.  
    ///
    /// #Examples
    ///   
    ///```
    ///  let cw = ContourWall::new(2_000_000);
    ///  cw.pixels.slice_mut(s![.., .., ..]).assign(&Array::from(vec![255, 255, 255]));
    ///  cw.show_w(10,true);
    pub fn show(&mut self, sleep_ms: u64, optimize: bool) {
        self.pushed_frames += 1;
        update_all(
            &mut self.cw_core,
            self.pixels
                .as_slice()
                .expect("could not get pixel slice")
                .as_ptr(),
            optimize,
        );
        show(&mut self.cw_core);

        thread::sleep(Duration::from_millis(sleep_ms))
    }

    /// Sending the command of filling the titles with one solid color.
    ///
    /// #paramters
    ///  - red: an unsigned 8bit integer.
    ///  - green: an unsigned 8bit integer.
    ///  - red: an unsigend 8bit integer.
    ///
    /// #Examples
    ///```
    ///  let cw = ContourWall::new(2_000_000);
    ///  cw.pixels.slice_mut(s![.., .., ..]).assign(&Array::from(vec![i, i, i]));
    ///  cw.show_w(10,true);
    /// ```
    pub fn solid_color(&mut self, red: u8, green: u8, blue: u8) {
        let mut slice = self.pixels.slice_mut(ndarray::s![.., .., ..]);
        let filled_vector = ndarray::Array::from(vec![red, green, blue]);
        slice.assign(&filled_vector);
    }
}

/// Converting color code from hsv to rgb.
///
/// #paramters
///  - h: an unsigned 8bit integer.
///  - s: an unsigned 8bit integer.
///  - v: an unsigend 8bit integer.
///
/// #return
///  a tuple of rgb code is return
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

fn string_to_str_ptr(s: &str) -> *const c_char {
    std::ffi::CString::new(s)
        .expect("CString conversion failed")
        .into_raw()
}

#[cfg(test)]
mod tests {
    use ndarray::{s, Array};
    use std::vec;

    use super::*;

    #[test]
    fn test_flash_all_colors() {
        let port = String::from("COM3");
        let Ok(mut cw) = ContourWall::single_new_from_port_w(port, 2_000_000) else {
            panic!("Port does not exist");
        };

        //set all pixels to RED
        cw.solid_color_w(255, 255, 255);
        cw.show_w(500, true);

        //set all pixels to RED
        cw.solid_color_w(0, 255, 255);
        cw.show_w(500, true);

        //set all pixels to GREEN
        cw.solid_color_w(0, 255, 0);
        cw.show_w(500, true);

        //set all pixels to GREEN
        cw.solid_color_w(255, 255, 0);
        cw.show_w(500, true);

        //set all pixels to BLUE
        cw.solid_color_w(255, 0, 0);
        cw.show_w(500, true);

        //set all pixels to WHITE
        cw.solid_color_w(255, 0, 255);
        cw.show_w(500, true);

        //set all pixels to BLACK
        cw.solid_color_w(0, 0, 0);
        cw.show_w(500, true);
    }

    #[test]
    fn test_fade_to_white() {
        let Ok(mut cw) = ContourWall::single_new_from_port_w(String::from("COM3"), 2_000_000)
        else {
            panic!("Port does not exist");
        };

        //slowly faded to white
        for i in 0..255 {
            cw.pixels
                .slice_mut(s![.., .., ..])
                .assign(&Array::from(vec![i, i, i]));
            cw.show_w(10, true);
        }

        cw.solid_color_w(0, 0, 0);
        cw.show_w(10, true);
    }

    #[test]
    fn test_fade_colors() {
        let Ok(mut cw) = ContourWall::single_new_from_port_w(String::from("COM3"), 2_000_000)
        else {
            panic!("Port does not exist");
        };

        //slowly fade oever all HSV colors
        for i in 0..=255 {
            cw.pixels
                .slice_mut(s![.., .., ..])
                .assign(&Array::from(vec![i, 255, 255]));
            cw.show_w(10, true);
        }

        cw.solid_color_w(0, 0, 0);
        cw.show_w(10, true);
    }

    #[test]
    fn test_moving_lines() {
        let Ok(mut cw) = ContourWall::single_new_from_port_w(String::from("COM3"), 2_000_000)
        else {
            panic!("Port does not exist");
        };

        let white = Array::from(vec![255, 255, 255]);
        let black = Array::from(vec![0, 0, 0]);

        //Move white line over the horizontal axis, from left to right
        for i in 0..20 {
            cw.pixels.slice_mut(s![.., i, ..]).assign(&white);
            cw.show_w(10, true);
            cw.pixels.slice_mut(s![.., i, ..]).assign(&black);
        }

        //Move white line over the horizontal axis, from left to right
        for i in (0..20).rev() {
            cw.pixels.slice_mut(s![.., i, ..]).assign(&white);
            cw.show_w(10, true);
            cw.pixels.slice_mut(s![.., i, ..]).assign(&black);
        }

        //Move white line over the vertical axis, from top to bottom
        for i in 0..20 {
            cw.pixels.slice_mut(s![i, .., ..]).assign(&white);
            cw.show_w(10, true);
            cw.pixels.slice_mut(s![i, .., ..]).assign(&black);
        }

        //Move white line over the vertical axis, from bottom to top
        for i in (0..20).rev() {
            cw.pixels.slice_mut(s![i, .., ..]).assign(&white);
            cw.show_w(10, true);
            cw.pixels.slice_mut(s![i, .., ..]).assign(&black);
        }

        cw.solid_color_w(0, 0, 0);
        cw.show_w(10, true);
    }

    #[test]
    fn test_turning_pixels_on_zigzag() {
        let Ok(mut cw) = ContourWall::single_new_from_port_w(String::from("COM3"), 2_000_000)
        else {
            panic!("Port does not exist");
        };

        let mut color = Array::from(vec![255, 255, 255]);

        for _ in 0..2 {
            let mut left_to_right = true;

            for x in (0..19).step_by(2) {
                //get iter range from left to right or vice versa based on choice
                let range_iter = if left_to_right {
                    (0..19).step_by(2).collect::<Vec<_>>().into_iter()
                } else {
                    (0..19).rev().step_by(2).collect::<Vec<_>>().into_iter()
                };

                //update the pixels in size of 2x2 every times
                for y in range_iter {
                    cw.pixels
                        .slice_mut(s![y..(y + 2), x..(x + 2), ..])
                        .assign(&color);
                    cw.show_w(10, true);
                }
                left_to_right = !left_to_right;
            }

            color = Array::from(vec![0, 0, 0]);
        }
    }
}
