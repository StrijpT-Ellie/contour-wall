# Rust wrapper 

The rust wrapper library wrapping the cw-core library, which is used to control the contour wall. The examples of using rust wrapper is put at the end of the lib.rs file.

```rust
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
```

# How to run
1. Run the demo test of rust wrapper with: 
```cargo test``` 

3. test can be run individually with the syntax:
```cargo test <test_function_name>```

