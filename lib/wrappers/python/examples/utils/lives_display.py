#!/usr/bin/env python3
"""
Lives display module for ContourWall games.
Displays lives as heart shapes made of pixels.
"""

# Heart pattern: 3x3 grid
HEART_PATTERN = [
    [1, 0, 1],
    [1, 1, 1],
    [0, 1, 0]
]

HEART_WIDTH = 3
HEART_HEIGHT = 3

def draw_lives(cw, lives: int, start_row: int = 0, start_col: int = 0, spacing: int = 4, color: tuple = (255, 0, 0)):
    """
    Draw lives as hearts on the ContourWall display.

    Args:
        cw: ContourWall emulator instance
        lives: Number of lives to display
        start_row: Starting row position
        start_col: Starting column position
        spacing: Space between hearts (in columns)
        color: RGB color tuple for the hearts
    """
    for i in range(lives):
        col = start_col + i * spacing
        for r in range(HEART_HEIGHT):
            for c in range(HEART_WIDTH):
                if HEART_PATTERN[r][c]:
                    # Check bounds to avoid index errors
                    if (start_row + r < cw.pixels.shape[0] and
                        col + c < cw.pixels.shape[1]):
                        cw.pixels[start_row + r, col + c] = color