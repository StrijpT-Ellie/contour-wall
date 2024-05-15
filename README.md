# Contour Wall

This project is a student initiative called "The Contour Wall," which is part of "ELLIE." The overarching goal of the ELLIE project is to enhance interactivity and engagement within the school buildings and the daily lives of the visitors, including Fontys students and employees to various technology companies who visit Fontys ICT for work and social activities.

The Contour Wall is intended to be an abstract, colorful, large-scale display measuring two meters in height and three meters in width. The project aims to serve as a visually striking and inspirational focal point, highlighting the diverse talents and capabilities of Fontys ICT students. By integrating elements from multiple ICT domains, the project provides a hands-on learning experience for the participating students, fostering collaboration, problem-solving, and skill development. And because of its simple and open interface, future students can integrate The Contour Wall into their project.

This repository contains: research, designs, source code and documention of the Contour Wall

![ellie_tq_render](/img/ellie_tq_denoise.png)

## Documentation readers guide

- [(TODO) You want to use the Contour Wall for your project]()
- [You need to know something about the construction](docs/construction/)
- [(TODO) You have bug, problem or suggestion]()
- [You need to know something about the software architecture](/docs/software_architecture/ELLIE_software_achitecture.pdf)
- [You need to know something about the hardware architecture documents (Excl. PCB's) ](/docs/hardware_architecture/README.md)
- [You need to know something about the PCB's designs, information or files](/PCB/)
- [(TODO) You want to write an additional wrapper](/lib/wrappers)
- [(TODO) You want to contribute to the core libary]()
- [(TODO) You want to contribute to the ESP32-S3 firmware]()

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
