# Pixel-based score display for ContourWall games
# Digit patterns for score display (5 rows x 3 columns)
DIGITS = {
    '0': [
        [1, 1, 1],
        [1, 0, 1],
        [1, 0, 1],
        [1, 0, 1],
        [1, 1, 1]
    ],
    '1': [
        [0, 1, 0],
        [1, 1, 0],
        [0, 1, 0],
        [0, 1, 0],
        [1, 1, 1]
    ],
    '2': [
        [1, 1, 1],
        [0, 0, 1],
        [1, 1, 1],
        [1, 0, 0],
        [1, 1, 1]
    ],
    '3': [
        [1, 1, 1],
        [0, 0, 1],
        [1, 1, 1],
        [0, 0, 1],
        [1, 1, 1]
    ],
    '4': [
        [1, 0, 1],
        [1, 0, 1],
        [1, 1, 1],
        [0, 0, 1],
        [0, 0, 1]
    ],
    '5': [
        [1, 1, 1],
        [1, 0, 0],
        [1, 1, 1],
        [0, 0, 1],
        [1, 1, 1]
    ],
    '6': [
        [1, 1, 1],
        [1, 0, 0],
        [1, 1, 1],
        [1, 0, 1],
        [1, 1, 1]
    ],
    '7': [
        [1, 1, 1],
        [0, 0, 1],
        [0, 1, 0],
        [1, 0, 0],
        [1, 0, 0]
    ],
    '8': [
        [1, 1, 1],
        [1, 0, 1],
        [1, 1, 1],
        [1, 0, 1],
        [1, 1, 1]
    ],
    '9': [
        [1, 1, 1],
        [1, 0, 1],
        [1, 1, 1],
        [0, 0, 1],
        [1, 1, 1]
    ]
}

def draw_digit(pixels, digit, row, col, color=(255, 255, 255)):
    """Draw a single digit at the specified position"""
    if digit not in DIGITS:
        return
    pattern = DIGITS[digit]
    for r in range(5):
        for c in range(3):
            if pattern[r][c]:
                pixels[row + r, col + c] = color

def draw_score(pixels, score, start_row=0, start_col=0, color=(255, 255, 255), position='left'):
    """Draw the score as digits at the specified position
    
    Args:
        pixels: The pixel array to draw on
        score: The score number to display
        start_row: Row position (0 for top)
        start_col: Column position (only used if position='custom')
        color: RGB color tuple for the digits
        position: 'left', 'center', 'right', or 'custom'
    """
    score_str = str(score)
    score_width = len(score_str) * 4 - 1  # 3 pixels per digit + 1 spacing, minus 1 for last digit
    
    rows, cols = pixels.shape[:2]
    
    if position == 'left':
        col = 0
    elif position == 'center':
        col = (cols - score_width) // 2
    elif position == 'right':
        col = cols - score_width
    elif position == 'custom':
        col = start_col
    else:
        col = 0  # default to left
    
    # Ensure we don't go out of bounds
    col = max(0, min(col, cols - score_width))
    
    for digit in score_str:
        draw_digit(pixels, digit, start_row, col, color)
        col += 4  # 3 pixels for digit + 1 pixel spacing