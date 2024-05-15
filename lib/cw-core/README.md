## Contour Wall Core

This is the "core" library of the Contour Wall. It provides a low-level interface to control the Contour Wall. It is not meant for developers to use directly, other languages should have wrappers implemented around this library. Those wrappers should be used by developers to control the Contour Wall.

To see where this library sits in the Contour Wall system, refer to the [software architecture](../../docs/software_architecture/ELLIE_software_achitecture.pdf). If you want API level documentation run: `cargo doc --open` or go to <https://docs.rs/contourwall_core/latest/contourwall_core/>.

## How to use

If you are planning on using this library in another Rust project, run this command in your project: `cargo add contourwall_core`.

If you are planning on using it in another language you need to compile it to a `*.so` (for Unix) or `*.dll` (for Windows). Execute: `cargo build --release`. Then, in the directory `target/release` you will find a file which is called `contourwall_core.dll` or `contourwall_core.so`.
