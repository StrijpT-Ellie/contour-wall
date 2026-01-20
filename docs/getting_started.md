# Getting Started

This guide gives a overview on how the Contour Wall works.

---

## How the Contour Wall works (conceptual overview)

The Contour Wall is controlled by a **core library written in Rust**.  
This core is responsible for:

- Communicating with the ESP32-S3 tiles
- Sending data at high speed over serial
- Synchronizing updates across tiles
- Handling low-level performance-critical logic

On top of this core, **wrappers** (Python, Rust, etc.) provide a friendly API for students to build demos and interactive experiences.

Your code never talks directly to the hardware — instead:
```
Your Demo → Wrapper → Core library (Rust) → ESP32-S3 (LED tiles)
```

This design keeps demos simple, safe, and language-agnostic. At its core, the Contour Wall works by sending **arrays of data** that represent what should be shown on the wall.

Each demo generates a **frame**:
- A 3D array
- Each element corresponds to a pixel (or tile segment)
- Each value represents color or intensity

## Choose your programming language
If you want to use the Contour Wall for your project you are going to have to decide on the language that you want to use. Currently, the two languages in which the library to control the wall is implemented are: Python and Rust. If you want to use a different language you are going to have to [implement it yourself](../CONTRIBUTING.md#contributing-to-new-wrappers).

The documentation for the for the library that you are going to use can be found in their respective directory, which are all located in the [`wrappers/`](../lib/wrappers/) directory. All wrappers (should) have examples are guides on how to setup your development enviroment.

If you want to incorperate the Contour Wall into your project you are going to have to decide on the language that you want to use. Currently, the two languages in which the library to control the wall is implemented are: Python and Rust. If you want to use a different language you are going to have to [implement it yourself](https://github.com/StrijpT-Ellie/contour-wall/blob/main/CONTRIBUTING.md#contributing-to-new-wrappers).

The documentation for the for the library that you are going to use can be found in their respective directory, which are all located in the [`wrappers/`](https://github.com/StrijpT-Ellie/contour-wall/blob/main/lib/wrappers) directory. All wrappers should have examples are guides on how to setup your development enviroment.
The Contour Wall core is written in **Rust**, and currently has official wrappers for:

- **Python**
- **Rust**

If you want to use a different language, you can create your own wrapper:
 [Contributing to new wrappers](../CONTRIBUTING.md#contributing-to-new-wrappers)

---

## Set up a wrapper

Each wrapper has its own documentation, examples, and setup instructions.

You can find all wrappers in `lib/wrappers/`:
- [Python duide](../lib/wrappers/python/README.md)
- [Rust guide](../lib/wrappers/rust/README.md)


Choose your wrapper and follow its README to:
- Build the core library
- Set up dependencies
- Run example demos
- Connect to the wall or emulator

---


---

### If you get stuck:
- [Check the wrapper documentation](../lib/README.md)
- [Read the software architecture docs](../docs/software_architecture)
- [Check the common errors section](../docs/common_errors.md)
- Ask previous project members
