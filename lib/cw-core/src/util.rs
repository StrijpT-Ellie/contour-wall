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