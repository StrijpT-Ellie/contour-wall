# Pixel-based game over display for ContourWall games
# Letter patterns for text display (5 rows x 5 columns)
LETTERS = {
    'G': [
        [1, 1, 1, 1, 0],
        [1, 0, 0, 0, 0],
        [1, 0, 1, 1, 1],
        [1, 0, 0, 0, 1],
        [1, 1, 1, 1, 0]
    ],
    'A': [
        [0, 1, 1, 1, 0],
        [1, 0, 0, 0, 1],
        [1, 1, 1, 1, 1],
        [1, 0, 0, 0, 1],
        [1, 0, 0, 0, 1]
    ],
    'M': [
        [1, 0, 0, 0, 1],
        [1, 1, 0, 1, 1],
        [1, 0, 1, 0, 1],
        [1, 0, 0, 0, 1],
        [1, 0, 0, 0, 1]
    ],
    'E': [
        [1, 1, 1, 1, 1],
        [1, 0, 0, 0, 0],
        [1, 1, 1, 1, 0],
        [1, 0, 0, 0, 0],
        [1, 1, 1, 1, 1]
    ],
    'O': [
        [0, 1, 1, 1, 0],
        [1, 0, 0, 0, 1],
        [1, 0, 0, 0, 1],
        [1, 0, 0, 0, 1],
        [0, 1, 1, 1, 0]
    ],
    'V': [
        [1, 0, 0, 0, 1],
        [1, 0, 0, 0, 1],
        [1, 0, 0, 0, 1],
        [0, 1, 0, 1, 0],
        [0, 0, 1, 0, 0]
    ],
    'R': [
        [1, 1, 1, 1, 0],
        [1, 0, 0, 0, 1],
        [1, 1, 1, 1, 0],
        [1, 0, 0, 1, 0],
        [1, 0, 0, 0, 1]
    ],
    ' ': [
        [0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0]
    ]
}

def draw_letter(pixels, letter, row, col, color=(0, 0, 255)):
    """Draw a single letter at the specified position"""
    if letter not in LETTERS:
        return
    pattern = LETTERS[letter]
    for r in range(5):
        for c in range(5):
            if pattern[r][c]:
                pixels[row + r, col + c] = color

def draw_text(pixels, text, start_row=0, start_col=0, color=(0, 0, 255), position='left'):
    """Draw text at the specified position

    Args:
        pixels: The pixel array to draw on
        text: The text string to display
        start_row: Row position (0 for top)
        start_col: Column position (only used if position='custom')
        color: RGB color tuple for the text
        position: 'left', 'center', 'right', or 'custom'
    """
    text = text.upper()  # Convert to uppercase since we only have uppercase letters
    text_width = len(text) * 6 - 1  # 5 pixels per letter + 1 spacing, minus 1 for last letter

    rows, cols = pixels.shape[:2]

    if position == 'left':
        col = 0
    elif position == 'center':
        col = (cols - text_width) // 2
    elif position == 'right':
        col = cols - text_width
    elif position == 'custom':
        col = start_col
    else:
        col = 0  # default to left

    # Ensure we don't go out of bounds
    col = max(0, min(col, cols - text_width))

    for letter in text:
        draw_letter(pixels, letter, start_row, col, color)
        col += 6  # 5 pixels for letter + 1 pixel spacing

def draw_game_over(pixels, score=None, color=(0, 0, 255)):
    """Draw a game over screen with optional score

    Args:
        pixels: The pixel array to draw on
        score: Optional score to display below "GAME OVER"
        color: BGR color tuple for the text (default: red)
    """
    rows, cols = pixels.shape[:2]

    # Clear the screen
    pixels[:] = 0, 0, 0

    # Draw "GAME OVER" centered
    game_over_text = "GAME OVER"
    draw_text(pixels, game_over_text, start_row=rows//2 - 3, color=color, position='center')

    # Draw score below if provided
    if score is not None:
        from score_display import draw_score
        draw_score(pixels, score, start_row=rows//2 + 3, color=color, position='center')