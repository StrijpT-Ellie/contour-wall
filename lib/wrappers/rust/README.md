# Rust wrapper

High-level Rust interface to control the Contour Wall

The Rust wrapper library wrapping the [cw-core](https://crates.io/crates/contourwall_core) library, which provides a low-level interface to control the Contour wall. The examples of using rust wrapper is put at the end of the lib.rs file.

```rust
let Ok(mut cw) = ContourWall::single_new_from_port(String::from("COM3"), 2_000_000)
else {
    panic!("Port does not exist");
};

//slowly faded to white
for i in 0..255 {
    cw.pixels
        .slice_mut(s![.., .., ..])
        .assign(&Array::from(vec![i, i, i]));
    cw.show(10, true);
}
```

## How to run

1. Run the demo test of rust wrapper with: cargo test
2. test can be run individually with the syntax: cargo test <test_function_name>
