# ContourWall Examples

This directory contains example games and demos for the ContourWall. These examples demonstrate how to use the ContourWall Python wrapper to create interactive games that can be controlled via keyboard or physical motion using a webcam.
Every game is equipped with an emulated version for running it locally.

## Games

### Line
A simple lane-switching game where you must stay within the safe lanes.

### Subway Surfers
An endless runner game inspired by Subway Surfers, where you switch lanes to avoid obstacles.

### Brick Breaker
A classic brick breaker game where you control a paddle to bounce a ball and break bricks.

### Hole Runner
A game where you navigate through moving lines with holes, avoiding collision.

## Controls

All games share similar controls:

- **Keyboard Mode**: Use Left/Right arrow keys or A/D to move, Q or ESC to quit, R to restart after game over (if applicable).
- **Physical Mode**: Move left/right in front of a webcam to control movement.

## Demos

- `demo.py`: Basic color flashing test for the ContourWall.
- `demo2.py`: Test script for specific hardware ports.

## Installation

Before running the examples, install the required dependencies:

```bash
python3 pip install -r requirements.txt
```

## Running the Games

To run a game in keyboard mode:

```bash
python3 examples/<game_directory>/<game_name>.py
```

For example:

```bash
python3 examples/line/line.py
```

To run a game in physical mode using webcam input:

```bash
python3 examples/<game_directory>/<game_name>.py --physical --camera-index 0
```

Replace `<game_directory>` and `<game_name>` with the appropriate name (e.g., `line`, `subway_surfers`, `brick_breaker`, `hole`).

Note: Physical mode requires a webcam and the MediaPipe library (included in requirements) for pose detection.

### Running emulated versions of the Games

If you don't have access to the wall, you can run the games using an Emulator. To do that, simply add _emulator to the end of the <game_name> in the terminal commands.

Example:

```bash
python3 examples/line/line_emulator.
```
