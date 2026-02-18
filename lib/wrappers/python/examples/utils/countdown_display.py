# Pixel-based countdown display for ContourWall games
import time

def draw_countdown_number(pixels, number, color=(255, 255, 255)):
	"""Draw a large countdown number using pixels"""
	rows, cols = pixels.shape[:2]
	
	# Define pixel patterns for countdown numbers (5, 4, 3, 2, 1) and GO
	patterns = {
		5: [
			" XXXXX ",
			" X     ",
			" XXXX  ",
			"     X ",
			" XXXXX "
		],
		4: [
			" X  X ",
			" X  X ",
			" XXXX ",
			"    X ",
			"    X "
		],
		3: [
			" XXXX  ",
			"     X ",
			"  XXX  ",
			"     X ",
			" XXXX  "
		],
		2: [
			" XXXX  ",
			"     X ",
			"  XXX  ",
			" X     ",
			" XXXXX "
		],
		1: [
			"  X   ",
			" XX   ",
			"  X   ",
			"  X   ",
			" XXX  "
		],
		'GO': [
			" XXXX ",
			" X  X ",
			" X XX ",
			" X  X ",
			" XXXX "
		]
	}
	
	pattern = patterns.get(number, patterns[3])  # Default to 3 if invalid
	
	# Calculate position to center the pattern
	pattern_height = len(pattern)
	pattern_width = len(pattern[0])
	start_row = (rows - pattern_height) // 2
	start_col = (cols - pattern_width) // 2
	
	# Draw the pattern
	for r, line in enumerate(pattern):
		for c, char in enumerate(line):
			if char == 'X':
				actual_row = start_row + r
				actual_col = start_col + c
				if 0 <= actual_row < rows and 0 <= actual_col < cols:
					pixels[actual_row, actual_col] = color


def show_countdown(cw, countdown_items=None, delay=1.0):
	"""Show a countdown sequence on the ContourWall display
	
	Args:
		cw: ContourWall emulator instance
		countdown_items: List of items to show (numbers or 'GO')
		delay: Seconds to show each item
	"""
	if countdown_items is None:
		countdown_items = [5, 4, 3, 2, 1, 'GO']
	
	for item in countdown_items:
		# Clear screen
		cw.pixels[:] = 0, 0, 0
		
		# Draw countdown number/pattern
		if item == 'GO':
			# For GO, use a brighter color
			draw_countdown_number(cw.pixels, item, color=(0, 255, 0))
		else:
			# For numbers, use white
			draw_countdown_number(cw.pixels, item, color=(255, 255, 255))
		
		cw.show()
		time.sleep(delay)