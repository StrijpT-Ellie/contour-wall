#[derive(PartialEq, Debug)]
pub enum StatusCode {
    Error,
    TooSlow,
    NonMatchingCRC,
    UnknownCommand,
    ErrorInternal,
    Ok,
    Next,
    Reset,
}

impl StatusCode {
    pub fn new(code: u8) -> Option<StatusCode> {
        match code {
            0 => Some(StatusCode::Error),
            1 => Some(StatusCode::TooSlow),
            2 => Some(StatusCode::NonMatchingCRC),
            3 => Some(StatusCode::UnknownCommand),
            50 => Some(StatusCode::ErrorInternal),
            100 => Some(StatusCode::Ok),
            101 => Some(StatusCode::Next),
            255 => Some(StatusCode::Reset),
            _ => None
        }
    }

    pub fn as_u8(&self) -> u8 {
        match self {
            StatusCode::Error => 0,
            StatusCode::TooSlow => 1,
            StatusCode::NonMatchingCRC => 2,
            StatusCode::UnknownCommand => 3,
            StatusCode::ErrorInternal => 50,
            StatusCode::Ok => 100,
            StatusCode::Next => 101,
            StatusCode::Reset => 255,
        }
    }
}