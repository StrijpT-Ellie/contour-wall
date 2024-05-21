# Rust wrapper 

The rust wrapper library wrapping the cw-core library, which is used to control the contour wall. The examples of using rust wrapper is put at the end of the lib.rs file.

# How to run

1. Install Cargo Rust version >=  1.75
2. Install Rust wrapper dependencies:
3. cargo add ndarray
```
cargo add serialport@=4.3.0
```
4. Set the library type of cw-core to ‘dylib’ with the following configuration in cargo.toml
```
[lib]
crate-type = ["dylib"]
```
5. Link the the rust wrapper to the cw-core with the following configuration in cargo.toml
```
[dependencies]
contourwall_core = {path = "../../cw-core" , version = "0.1.0" }
```
6. Run the demo test of rust wrapper with: 
```cargo test``` 


