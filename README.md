# Contour Wall

This project is a student initiative called "The Contour Wall," which is part of "ELLIE." The overarching goal of the ELLIE project is to enhance interactivity and engagement within the school buildings and the daily lives of the visitors, including Fontys students and employees to various technology companies who visit Fontys ICT for work and social activities.

The Contour Wall is intended to be an abstract, colorful, large-scale display measuring two meters in height and three meters in width. The project aims to serve as a visually striking and inspirational focal point, highlighting the diverse talents and capabilities of Fontys ICT students. By integrating elements from multiple ICT domains, the project provides a hands-on learning experience for the participating students, fostering collaboration, problem-solving, and skill development. And because of its simple and open interface, future students can integrate The Contour Wall into their project.

## What’s in this repository

This repository contains **all research, designs, source code, and documentation** related to the Contour Wall:

- Software (core library + wrappers)
- Firmware for the tiles
- Hardware and PCB designs
- Research experiments
- Example demos
- Architecture documentation

![ellie_tq_render](/img/ellie_tq_denoise.png)

---
## Creating a demo

The Contour Wall can display a wide variety of interactive demos, such as:
- Visual animations
- Interactive mirrors using contour detection
- Games (e.g. Flappy Bird, coin collecting)
- Sensor-based installations

Several example demos are available in the [`/demos`](./demos) directory.

Demos are to be displayed during school hours. They are meant to be educational for students. To learn new technologies and frameworks and learn how to build and integrate interactive systems.

To create a demo in Python3, download and unzip a setup example for your architecture and OS. Copy the command in the terminal:

- **Windows x86_65:** `curl.exe -L -o setup.zip https://github.com/StrijpT-Ellie/contour-wall/releases/download/tag/v1.0.0/cw_setup_win_x86_64.zip; Expand-Archive -Path setup.zip -DestinationPath .; Remove-Item setup.zip`
- **Linux x86_64:** `curl -L -o setup.zip https://github.com/StrijpT-Ellie/contour-wall/releases/download/tag/v1.0.0/cw_setup_linux_x86_64.zip && unzip setup.zip && rm setup.zip`
- **MacOS ARM:** `curl -L -o setup.zip https://github.com/StrijpT-Ellie/contour-wall/releases/download/tag/v1.0.0/cw_setup_macos_arm.zip && unzip setup.zip && rm setup.zip`
- Sadly if we do not have a pre-compiled setup for you, [you have to compile it yourself](#compiling-your-own-setup).

Documentation of the wrappers are included in the actual source code above each function. Refer to demos for more context.

### Compiling your own setup
Before creating your own demo, you must:
1. **Compile the core library** (written in Rust): [lib/cw-core](lib/cw-core/)
2. **Choose and set up a wrapper language** (Python or Rust): [lib/wrappers](lib/wrappers/)
3. **Connect to the Contour Wall or use the emulator**
   - Emulator: : [lib/wrappers/python/contourwall_emulator.py](lib/wrappers/contourwall_emulator.py)

Once your environment is ready, you can:
- Run existing demos from `/demos`
- Modify a demo
- Create your own interactive experience

**Start here**:
- [Getting started: Compile the core library](lib/README.md )
- [Getting started: Learning how the Contour wall works](docs/getting_started.md)

---
## Documentation readers guide

- [You want to use the Contour Wall for your project](docs/getting_started.md)
- [You need to know something about the construction](docs/construction/)
- [(TODO) You have bug, problem or suggestion]()
- [You need to know something about the software architecture](/docs/software_architecture/ELLIE_software_achitecture.pdf)
- [You need to know something about the hardware architecture documents (Excl. PCB's) ](/docs/hardware_architecture/README.md)
- [You need to know something about the PCB's designs, information or files](/PCB/)
- [You want to write an additional wrapper](CONTRIBUTING.md#contributing-to-new-wrappers)
- [You want to contribute to the core libary](CONTRIBUTING.md#contributing-to-the-core-libary)
- [(TODO) You want to contribute to the ESP32-S3 firmware](CONTRIBUTING.md#contributing-to-the-firmware)
- [You want to contribute to CDI](CONTRIBUTING.md#contributing-to-cdi)

## Directory Structure

- `docs/`: Additional documentation that does not belong to specific parts (E.G. architecture or how-to)
- `firmware/`: The firmware for the tiles, running on ESP32's. Implements protocol and controls PCB's.
- `font/`: A custom low-res font for the Contour Wall, including util functions
- `img/`: images for E.G. README's 
- `lib/`: The library to control the Contour Wall
- `pcb/`: Information and design of the PCB's, such as: dimensions, electrical properties. All the design files of the PCB are also in there.
- `research/`: All the research scripts, mostly regarding contour extraction from video feed.
- `scripts/`: Additional scripts for E.G. a pipeline or development.
  
## Contributors

**This is an education project supported and guided by [Fontys University of Applied Sciences](https://www.fontys.nl/en/Home.htm)**

<a href="https://github.com/StrijpT-Ellie/contour-wall/graphs/contributors">
  <img src="https://contrib.rocks/image?repo=StrijpT-Ellie/contour-wall"/>
</a>
