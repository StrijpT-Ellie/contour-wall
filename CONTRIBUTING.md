# Contibuting to ContourWall

This page is for people who are interested in contributing to the Contour Wall project by work such as code or documentation. If you have anything outside that or you have a problem
, read [Contributing in different ways](#Contributing-in-different-ways).

## Contributing to CDI

When you are missing a feature in CDI (**C**ontourwall **D**isplay **I**nterface) or can something be improved, it is best to create a Github issue first. This way is can be discussed first before time is invested.

Updating CDI can be quite the undertaking, the firmware, core library, documentation and more needs to be updated. Maybe even all the wrappers if it is a really significant change. We also like to keep it as minimal as possible. Therefore we like to discuss before we implement.

However, if you are ready to implement your change, make sure you have a good understanding of [UART](https://en.wikipedia.org/wiki/Universal_asynchronous_receiver-transmitter), our [firmware](firmware/firmware.ino) and the [core libary](lib/cw-core/). CDI is explained and defined in the [software architecture document](docs/software_architecture/ELLIE_software_achitecture.pdf) could also help.

## Contributing to the core libary

Have you found a bug, optimization or do you want to implement a feature for the core libary.

TODO

## Contributing to (new) wrappers

Do you want to use a language in which there is not a wrapper available? Make sure that you understand the core libaries API very well, also refer to the [architecture document](docs/software_architecture/ELLIE_software_achitecture.pdf) for better understanding of the whole system.

Refer to the [ContourWallCore documentation](/lib/cw-core/README.md#how-to-use) to see how to compile the libary to a `*.dll` or `*.so`. When implementing your own wrapper in a new language, try to mimic the implementation of the [Python](lib/wrappers/python/) or [Rust](lib/wrappers/rust/) wrapper.

If you think that others would like to use your wrapper, you can create a pull request. Your code will be reviewed and if good enough it will be merged into the main branch. Before you make a pull request there are a couple of things you need to check to smooth out the reviewing process. We want to make sure that all wrappers are up to standard, therefore we have number of "rules" and conventions:

1. **Contain as little logic as possible.** If all the wrappers have the same logic, it should be considered to move this logic into the core library in Rust.
2. **Follow existing conventions of packages often used in combination with the wrapper.** This reduces the complexity of incorporating the Contour Wall into existing projects. E.G. OpenCV will be used to display content on the ContourWall, make sure that the wrapper uses OpenCV conventions. This makes sure that little conversions between data structures is needed to improve performance and reduce complexity.
3. **Keep the API of the wrappers similar.** When the API of all wrappers is identical is it easy to switch between them, streamlines wrapper development and reduces the learning curve.
4. **API documentation**. There is in-code documentation of the API of your wrapper.
5. **Getting started**. To instruct other on how to use your libary. We would like to see a getting started, this includes instructions on how to set everything up and a small code sample.

Are you unsure if your wrapper checks all the boxes? Just create a pull-request, we can always help!

## Contributing to the firmware

TODO

## Contributing to documentation

If you find a place where documentation is lacking create a issue, or create a pull request with the new or improved documentation.

## Contributing in different ways

Create an issue on Github or contact <p.pennings@student.fontys.nl>
