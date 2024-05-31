//! Utiliy functions for the ContourWall Core libary.

use std::{
    ffi::{c_char, CStr},
    time::SystemTime,
};

pub fn millis_since_epoch() -> u64 {
    let now = SystemTime::now();
    let duration_since_epoch = now.duration_since(SystemTime::UNIX_EPOCH).unwrap();
    duration_since_epoch.as_nanos() as u64 / 1_000_000
}

pub fn str_ptr_to_string(ptr: *const c_char) -> String {
    let c_str = unsafe { CStr::from_ptr(ptr) };
    c_str.to_string_lossy().into_owned()
}

pub fn generate_index_conversion_vector() -> [usize; 1200] {
    let mut matrix: [[usize; 20]; 20] = [[0; 20]; 20];
    for x in 0..20 {
        let row_start_value = match x {
            0..=4 => x,
            5..=9 => 100 + x - 5,
            10..=14 => 200 + x - 10,
            _ => 300 + x - 15,
        };

        let mut y = 0;
        for index in (row_start_value..row_start_value + 100).step_by(5) {
            matrix[x][y] = index * 3;
            y += 1;
        }
    }

    let mut result: [usize; 1200] = [0; 1200];
    let mut index = 0;
    for column in matrix.iter() {
        for &element in column.iter() {
            result[index] = element;
            result[index + 1] = element + 1;
            result[index + 2] = element + 2;
            index += 3;
        }
    }

    result
}

pub fn split_framebuffer(framebuffer: &[u8]) -> Vec<Vec<u8>> {
    let mut framebuffers: Vec<Vec<u8>> = vec![Vec::with_capacity(1200); 6];

    for (i, v) in framebuffer.iter().enumerate() {
        let column: usize = i / 2400;
        let row: usize = ((i % 120) > 59) as usize * 3;

        framebuffers[column + row].push(*v);
    }

    framebuffers
}

pub fn extract_mutated_pixels(
    previous_framebuffer: &mut [u8; 1200],
    framebuffer: &[u8; 1200],
) -> Vec<u8> {
    let mut different_framebuffer_vector: Vec<u8> = vec![];

    let frame_length = previous_framebuffer.len();
    for i in (0..frame_length - 2).step_by(3) {
        let start_i: usize = i;
        let end_i: usize = i + 3;

        //get the previous and the current rgb code
        let prev_rgb: &[u8] = &previous_framebuffer[start_i..end_i];
        let cur_rgb: &[u8] = &framebuffer[start_i..end_i];

        if prev_rgb != cur_rgb {
            //add index and updated rgb code to the different buffer
            different_framebuffer_vector.extend(get_pixel_index(i));
            different_framebuffer_vector.extend(cur_rgb);

            //update the previous buffer to the latest rgb code
            previous_framebuffer[start_i..end_i].copy_from_slice(cur_rgb);
        }
    }

    return different_framebuffer_vector;
}

pub fn get_pixel_index(index: usize) -> [u8; 2] {
    assert_eq!(index % 3, 0, "index must be divisible by 3");
   
    let index = index / 3;

    //limited to the toatal number of the total pixels on the tile - 400 pixels
    if index > 399 {
        return [0u8; 2];
    }

    let pixel_index: [u8; 2] = (index as u16).to_be_bytes();

    return pixel_index;
}

#[cfg(debug_assertions)]
pub fn configure_logging() {
    env_logger::Builder::new()
        .format_timestamp_millis()
        .filter_level(log::LevelFilter::Trace)
        .init();
}

#[cfg(not(debug_assertions))]
pub fn configure_logging() {
    env_logger::Builder::new()
        .format_timestamp_millis()
        .filter_level(log::LevelFilter::Info)
        .init();
}

#[cfg(test)]
mod tests {
    use std::ffi::CString;

    use super::*;

    #[test]
    fn test_extract_mutated_framebuffer_no_led_is_updated_case() {
        //arrange
        let previous_framebuffer = &mut [0u8; 1200];
        let current_framebuffer = &mut [0u8; 1200];

        let expected_mutated_framebuffer: Vec<u8> = vec![];

        //action
        let mutated_framebuffer = extract_mutated_pixels(previous_framebuffer, current_framebuffer);

        //assert
        assert_eq!(
            mutated_framebuffer, expected_mutated_framebuffer,
            "the result_different_frambuffer is wrong: {:?}",
            mutated_framebuffer
        );
    }

    #[test]
    fn test_diff_framebuffer_the_first_pixel_is_updated_case() {
        //arrange
        let previous_framebuffer = &mut [0u8; 1200];
        let current_framebuffer = &mut [0u8; 1200];
        current_framebuffer[0..3].copy_from_slice(&[1u8; 3]);

        let expected_mutated_framebuffer: Vec<u8> = vec![0, 0, 1, 1, 1];

        //action
        let mutated_framebuffer = extract_mutated_pixels(previous_framebuffer, current_framebuffer);

        //assert
        assert_eq!(
            mutated_framebuffer, expected_mutated_framebuffer,
            "the result_different_frambuffer is wrong: {:?}",
            mutated_framebuffer
        );
    }

    #[test]
    fn test_diff_framebuffer_the_last_pixel_is_updated() {
        //arrange
        let previous_framebuffer = &mut [0u8; 1200];
        let current_framebuffer = &mut [0u8; 1200];
        current_framebuffer[1197..1200].copy_from_slice(&[1u8; 3]);

        let expected_mutated_framebuffer: Vec<u8> = vec![0x1, 0x8F, 1, 1, 1];

        //action
        let mutated_framebuffer = extract_mutated_pixels(previous_framebuffer, current_framebuffer);

        //assert
        assert_eq!(
            mutated_framebuffer, expected_mutated_framebuffer,
            "the result_different_frambuffer is wrong: {:?}",
            mutated_framebuffer
        );
    }

    #[test]
    fn test_diff_framebuffer_the_first_and_last_pixel_are_updated_case() {
        //arrange
        let previous_framebuffer = &mut [0u8; 1200];
        let current_framebuffer = &mut [0u8; 1200];
        current_framebuffer[0..3].copy_from_slice(&[1u8; 3]);
        current_framebuffer[1197..1200].copy_from_slice(&[1u8; 3]);

        let expected_mutated_framebuffer: Vec<u8> = vec![0, 0, 1, 1, 1, 0x1, 0x8F, 1, 1, 1];

        //action
        let mutated_framebuffer = extract_mutated_pixels(previous_framebuffer, current_framebuffer);

        //assert
        assert_eq!(
            mutated_framebuffer, expected_mutated_framebuffer,
            "the result_different_frambuffer is wrong: {:?}",
            mutated_framebuffer
        );
    }

    #[test]
    fn test_get_pixel_index_smaller_than_255() {
        //arrange
        let index: usize = 12 * 3;
        let expected_pixel_index: [u8; 2] = [0, 12];

        //action
        let index_pixel = get_pixel_index(index);

        //assert
        assert_eq!(
            index_pixel, expected_pixel_index,
            "the result of the index pixel is wrong{:?}",
            index_pixel
        );
    }

    #[test]
    fn test_get_pixel_index_255() {
        //arrange
        let index: usize = 255 * 3;
        let expected_pixel_index: [u8; 2] = [0, 255];

        //action
        let index_pixel = get_pixel_index(index);

        //assert
        assert_eq!(
            index_pixel, expected_pixel_index,
            "the result of the index pixel is wrong{:?}",
            index_pixel
        );
    }

    #[test]
    fn test_get_pixel_index_256() {
        //arrange
        let index: usize = 256 * 3;
        let expected_pixel_index: [u8; 2] = [1, 0];

        //action
        let index_pixel = get_pixel_index(index);

        //assert
        assert_eq!(
            index_pixel, expected_pixel_index,
            "the result of the index pixel is wrong{:?}",
            index_pixel
        );
    }

    #[test]
    fn test_get_pixel_index_smaller_than_399() {
        //arrange
        let index: usize = 300 * 3;
        let expected_pixel_index: [u8; 2] = [0x01, 0x2C];

        //action
        let index_pixel = get_pixel_index(index);

        //assert
        assert_eq!(
            index_pixel, expected_pixel_index,
            "the result of the index pixel is wrong{:?}",
            index_pixel
        );
    }

    #[test]
    fn test_get_pixel_index_maximum() {
        //arrange
        let index: usize = 399 * 3;
        let expected_pixel_index: [u8; 2] = [0x1, 0x8F];

        //action
        let index_pixel = get_pixel_index(index);

        //assert
        assert_eq!(
            index_pixel, expected_pixel_index,
            "the result of the index pixel is wrong{:?}",
            index_pixel
        );
    }

    #[test]
    fn test_str_ptr_to_string() {
        let win_com: *const c_char = CString::new("COM5")
            .expect("CString conversion failed")
            .into_raw();

        let linux_com: *const c_char = CString::new("/dev/ttyUSB5")
            .expect("CString conversion failed")
            .into_raw();

        assert_eq!(str_ptr_to_string(win_com), "COM5");
        assert_eq!(str_ptr_to_string(linux_com), "/dev/ttyUSB5");
    }

    #[test]
    fn test_split_framebuffer_all_0() {
        let framebuffer: &[u8] = &[0; 7200];

        let framebuffers = split_framebuffer(framebuffer);

        for (i, framebuffer) in framebuffers.iter().enumerate() {
            assert_eq!(
                framebuffer.len(),
                1200,
                "Framebuffer at index: {}, has a length of {} not 1200",
                i,
                framebuffer.len()
            )
        }
    }

    #[test]
    fn test_split_framebuffer() {
        let framebuffer: &mut [u8] = &mut [0; 7200];

        framebuffer[0] = 1;
        framebuffer[60] = 2;
        framebuffer[2400] = 3;
        framebuffer[2460] = 4;
        framebuffer[4800] = 5;
        framebuffer[4860] = 6;

        let framebuffers = split_framebuffer(framebuffer);

        assert_eq!(framebuffers[0][0], 1, "Top left framebuffer");
        assert_eq!(framebuffers[1][0], 3, "Top center framebuffer");
        assert_eq!(framebuffers[2][0], 5, "top right framebuffer");
        assert_eq!(framebuffers[3][0], 2, "Bottom left framebuffer");
        assert_eq!(framebuffers[4][0], 4, "Bottom center framebuffer");
        assert_eq!(framebuffers[5][0], 6, "Bottom right framebuffer");
    }

    #[test]
    fn test_index_conversion_vector() {
        let conversion_vector = generate_index_conversion_vector();

        assert_eq!(conversion_vector[1199], 1199);
        assert_eq!(conversion_vector[60], 3);
        assert_eq!(conversion_vector[300], 300);
        assert_eq!(conversion_vector[659], 887);
    }
}
