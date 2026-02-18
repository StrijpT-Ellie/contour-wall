import argparse
import time
import random
import math
import sys
from pathlib import Path

_THIS_DIR = Path(__file__).resolve().parent
EXAMPLES_DIR = _THIS_DIR.parent
UTILS_DIR = EXAMPLES_DIR / "utils"
WRAPPER_DIR = EXAMPLES_DIR.parent

for _p in (str(WRAPPER_DIR), str(UTILS_DIR)):
	if _p not in sys.path:
		sys.path.insert(0, _p)

from contourwall_emulator import ContourWallEmulator

try:
	import cv2 as cv
except ImportError:  # Allow running without cv2 input support.
	cv = None
try:
	import mediapipe as mp
except ImportError:
	mp = None

from game_input import PhysicalMotionController, normalize_key
from score_display import draw_score
from game_over_display import draw_game_over
from lives_display import draw_lives
from highscore_board import HighscoreBoard, highscore_path
from countdown_display import show_countdown


class PoseController:
	def __init__(self, camera_index=0, show_window=False):
		self.show_window = show_window
		if cv is None or mp is None or not hasattr(mp, "solutions"):
			raise RuntimeError("MediaPipe Pose is unavailable.")
		if sys.platform.startswith("win"):
			self.cap = cv.VideoCapture(camera_index, cv.CAP_DSHOW)
		else:
			self.cap = cv.VideoCapture(camera_index)
		if not self.cap.isOpened():
			raise RuntimeError("Camera failed to open.")
		self.cap.set(cv.CAP_PROP_FRAME_WIDTH, 640)
		self.cap.set(cv.CAP_PROP_FRAME_HEIGHT, 480)
		self.pose = mp.solutions.pose.Pose(
			static_image_mode=False,
			model_complexity=1,
			min_detection_confidence=0.3,
			min_tracking_confidence=0.3,
		)

	def read_key(self):
		if not self.show_window or cv is None:
			return -1
		return normalize_key(cv.waitKey(1))

	def read_target_col(self, cols):
		ret, frame = self.cap.read()
		if not ret:
			return None
		frame = cv.flip(frame, 1)
		rgb = cv.cvtColor(frame, cv.COLOR_BGR2RGB)
		results = self.pose.process(rgb)
		if self.show_window:
			cv.imshow("Camera", frame)
		if not results.pose_landmarks:
			return None

		lm = results.pose_landmarks.landmark
		xs = [
			lm[mp.solutions.pose.PoseLandmark.LEFT_SHOULDER].x,
			lm[mp.solutions.pose.PoseLandmark.RIGHT_SHOULDER].x,
			lm[mp.solutions.pose.PoseLandmark.LEFT_HIP].x,
			lm[mp.solutions.pose.PoseLandmark.RIGHT_HIP].x,
		]
		avg_x = sum(xs) / len(xs)
		return int(max(0, min(cols - 1, round(avg_x * (cols - 1)))))

	def close(self):
		if self.cap is not None:
			self.cap.release()
		if self.pose is not None:
			self.pose.close()
		if self.show_window and cv is not None:
			cv.destroyAllWindows()


def read_key():
	if cv is None:
		return -1
	return cv.waitKey(1) & 0xFF


def draw_background(pixels, offset, pattern):
	"""Draw subtle animated background patterns"""
	rows, cols = pixels.shape[:2]

	if pattern == "stars":
		# Very subtle twinkling stars background
		for r in range(0, rows, 3):  # Every 3rd row
			for c in range(0, cols, 4):  # Every 4th column
				# Create a simple star field effect
				star_value = (r * 7 + c * 13 + offset) % 255
				if star_value < 5:  # Very sparse stars
					brightness = min(50, star_value * 10)  # Much dimmer
					pixels[r, c] = (brightness, brightness, brightness)


def draw_gradient_line(pixels, row, hole_start, hole_width, colors, score):
	"""Draw a line with solid colors and hole"""
	cols = pixels.shape[1]
	line_color = colors[score % len(colors)]

	# Draw the solid line parts (no gradient, just solid color)
	for c in range(cols):
		if not (hole_start <= c < hole_start + hole_width):
			pixels[row, c] = line_color


def draw_player_with_trail(pixels, player_row, player_col, trail, player_color):
	"""Draw player with a glowing trail effect"""
	# Draw trail (fading older positions)
	for i, (trail_row, trail_col) in enumerate(trail[-5:]):  # Last 5 positions
		if 0 <= trail_row < pixels.shape[0] and 0 <= trail_col < pixels.shape[1]:
			fade = (len(trail) - len(trail) + i + 1) / 6.0  # Fade factor
			r = int(player_color[0] * fade * 0.5)
			g = int(player_color[1] * fade * 0.5)
			b = int(player_color[2] * fade * 0.5)
			pixels[trail_row, trail_col] = (r, g, b)

	# Draw main player with glow effect
	if 0 <= player_row < pixels.shape[0] and 0 <= player_col < pixels.shape[1]:
		# Main player dot
		pixels[player_row, player_col] = player_color

		# Add glow around player
		for dr in [-1, 0, 1]:
			for dc in [-1, 0, 1]:
				if dr == 0 and dc == 0:
					continue
				r2, c2 = player_row + dr, player_col + dc
				if 0 <= r2 < pixels.shape[0] and 0 <= c2 < pixels.shape[1]:
					glow_intensity = 0.3 / (abs(dr) + abs(dc))  # Dimmer with distance
					r = int(player_color[0] * glow_intensity)
					g = int(player_color[1] * glow_intensity)
					b = int(player_color[2] * glow_intensity)
					# Only set if pixel is darker (don't overwrite brighter pixels)
					if all(pixels[r2, c2] < (r, g, b)):
						pixels[r2, c2] = (r, g, b)


def add_score_particles(particles, player_row, player_col, score):
	"""Add particle effects when scoring"""
	colors = [(255, 255, 0), (255, 165, 0), (255, 0, 255), (0, 255, 255)]
	for _ in range(3):  # Add 3 particles
		particles.append({
			'row': player_row - 1,
			'col': player_col + random.randint(-2, 2),
			'color': random.choice(colors),
			'lifetime': 15,
			'velocity_row': random.uniform(-0.5, -0.1),
			'velocity_col': random.uniform(-0.3, 0.3)
		})


def update_particles(particles):
	"""Update and draw particles"""
	to_remove = []
	for particle in particles:
		particle['lifetime'] -= 1
		if particle['lifetime'] <= 0:
			to_remove.append(particle)
			continue

		particle['row'] += particle['velocity_row']
		particle['col'] += particle['velocity_col']

		# Draw particle if in bounds
		row, col = int(particle['row']), int(particle['col'])
		if 0 <= row < cw.pixels.shape[0] and 0 <= col < cw.pixels.shape[1]:
			intensity = particle['lifetime'] / 15.0
			r = int(particle['color'][0] * intensity)
			g = int(particle['color'][1] * intensity)
			b = int(particle['color'][2] * intensity)
			cw.pixels[row, col] = (r, g, b)

	# Remove dead particles
	for particle in to_remove:
		particles.remove(particle)


def hole_runner(motion_controller=None):
	rows, cols = cw.pixels.shape[:2]
	player_row = rows - 2
	player_col = cols // 2
	player_col_float = float(player_col)
	player_color = (0, 255, 255)

	hole_width = max(2, cols // 6)
	line_row = 0
	hole_start = random.randint(0, cols - hole_width)

	line_interval = 0.08
	last_line = time.time()
	last_tick = time.time()
	last_move_time = 0.0
	last_move_key = None
	move_repeat_delay = 0.12
	move_repeat_interval = 0.05

	score = 0
	lives = 3
	invuln_timer = 0
	line_count = 0  # Counter for total lines drawn

	# Enhanced color schemes with gradients
	color_schemes = [
		[(255, 100, 100), (255, 150, 150), (255, 200, 200)],  # Red gradient
		[(100, 255, 100), (150, 255, 150), (200, 255, 200)],  # Green gradient
		[(100, 100, 255), (150, 150, 255), (200, 200, 255)],  # Blue gradient
		[(255, 255, 100), (255, 255, 150), (255, 255, 200)],  # Yellow gradient
		[(255, 100, 255), (255, 150, 255), (255, 200, 255)],  # Magenta gradient
		[(100, 255, 255), (150, 255, 255), (200, 255, 255)],  # Cyan gradient
		[(255, 150, 100), (255, 200, 150), (255, 255, 200)],  # Orange gradient
	]

	# Particle system for effects
	particles = []  # List of (row, col, color, lifetime)

	# Background animation variables
	background_offset = 0
	background_pattern = "stars"  # "stars", "waves", "grid"

	# Player trail effect
	player_trail = []  # List of recent player positions

	# Highscore variables
	EXAMPLES_DIR = Path(__file__).resolve().parent
	highscore_path_var = highscore_path(EXAMPLES_DIR, "hole_runner")
	highscores = []
	last_initials = "Anm"
	highscore_board = HighscoreBoard(rows, cols, cw.pixels)
	highscores = highscore_board.load(highscore_path_var)

	if motion_controller is None:
		print("Hole runner controls: A/D or Left/Right arrows. Press Q to quit.")
	else:
		print("Hole runner camera mode: move left/right. Press Q to quit.")

	# Countdown before game starts
	show_countdown(cw)

	while True:
		now = time.time()
		if now - last_tick < 0.02:
			time.sleep(0.002)
			continue
		last_tick = now

		if invuln_timer > 0:
			invuln_timer -= 1

		key = read_key() if motion_controller is None else normalize_key(motion_controller.read_key())
		if key in (ord('q'), 27):
			return False

		if motion_controller is None:
			move_key = None
			if key in (ord('a'), 81):
				move_key = 'left'
			elif key in (ord('d'), 83):
				move_key = 'right'

			if move_key is not None:
				if move_key != last_move_key:
					last_move_key = move_key
					last_move_time = now
					if move_key == 'left':
						player_col = max(0, player_col - 1)
					else:
						player_col = min(cols - 1, player_col + 1)
				else:
					elapsed = now - last_move_time
					if elapsed >= move_repeat_delay or elapsed >= move_repeat_interval:
						if move_key == 'left':
							player_col = max(0, player_col - 1)
							last_move_time = now
						else:
							player_col = min(cols - 1, player_col + 1)
							last_move_time = now
			else:
				last_move_key = None
		else:
			physical_col = motion_controller.read_target_col(cols)
			if physical_col is not None:
				target = float(max(0, min(cols - 1, physical_col)))
				player_col_float = (0.8 * player_col_float) + (0.2 * target)
				player_col = int(max(0, min(cols - 1, round(player_col_float))))

		if now - last_line >= line_interval:
			last_line = now
			line_row += 1
			line_count += 1  # Increment total line counter

			if line_row >= player_row:
				if hole_start <= player_col < hole_start + hole_width:
					score += 1
					line_interval = max(0.02, line_interval - 0.005)  # Speed up slightly
					line_row = 0
					hole_start = random.randint(0, cols - hole_width)
					# Add score particles
					add_score_particles(particles, player_row, player_col, score)
				else:
					lives -= 1
					invuln_timer = 30  # 1 second of invulnerability
					if lives <= 0:
						break
					# Reset line position to give player another chance
					line_row = 0
					hole_start = random.randint(0, cols - hole_width)

		# Update background animation
		background_offset += 1

		# Update player trail
		player_trail.append((player_row, player_col))
		if len(player_trail) > 8:  # Keep only recent positions
			player_trail.pop(0)

		# Clear screen and draw background
		cw.pixels[:] = 0, 0, 0
		draw_background(cw.pixels, background_offset, background_pattern)

		# Update and draw particles
		update_particles(particles)

		# Draw score at top left
		draw_score(cw.pixels, score, start_row=0, position='center')

		# Draw lives
		draw_lives(cw, lives, start_row=1, start_col=0, spacing=4, color=(0, 0, 255))

		if 0 <= line_row < rows:
			current_scheme = color_schemes[score % len(color_schemes)]
			draw_gradient_line(cw.pixels, line_row, hole_start, hole_width, current_scheme, score)

		# Modify player color for damage flash
		display_color = player_color
		if invuln_timer > 0 and (invuln_timer // 5) % 2 == 1:  # Flash every 5 frames
			display_color = (255, 0, 255)  # Purple flash

		# Draw player with trail and glow
		draw_player_with_trail(cw.pixels, player_row, player_col, player_trail, display_color)

		cw.show()

	# Game over screen with animation
	game_over_start = time.time()
	animation_frames = 60  # 2 seconds at 30fps

	for frame in range(animation_frames):
		# Create explosion effect
		cw.pixels[:] = 0, 0, 0

		# Draw expanding explosion circles
		center_row, center_col = player_row, player_col
		radius = frame * 0.5

		if radius > 0:  # Avoid division by zero
			for r in range(rows):
				for c in range(cols):
					distance = math.sqrt((r - center_row)**2 + (c - center_col)**2)
					if distance <= radius and distance > radius - 1:
						# Explosion ring colors
						intensity = 1.0 - (distance / radius)
						if frame < 20:
							color = (int(255 * intensity), 0, int(255 * intensity))  # Purple
						elif frame < 40:
							color = (int(255 * intensity), int(100 * intensity), int(255 * intensity))  # Purple-pink
						else:
							color = (int(128 * intensity), 0, int(128 * intensity))  # Dark purple

						cw.pixels[r, c] = color

		# Draw final score with pulsing effect
		pulse = math.sin(frame * 0.3) * 0.3 + 0.7
		score_color = (int(255 * pulse), int(255 * pulse), int(100 * pulse))
		draw_score(cw.pixels, score, start_row=rows//2 - 3, position='center', color=score_color)

		cw.show()
		time.sleep(0.033)  # ~30fps

	# Final static game over screen
	cw.pixels[:] = 0, 0, 0
	draw_game_over(cw.pixels, score=score)
	cw.show()
	time.sleep(2)  # Show final screen for 2 seconds

	# Record highscore
	last_initials, highscores = highscore_board.record(
		highscores,
		score,
		last_initials,
		path=highscore_path_var,
	)

	print(f"Game over. Score: {score}")

	# Show highscores and wait for restart or quit
	print("Press R to restart or Q to quit.")
	if highscores:
		print("Top scores:")
		for idx, (name, score_val) in enumerate(highscores[:10], start=1):
			print(f" {idx:>2}. {name} - {score_val}")

	flash = False
	while True:
		flash = not flash
		if flash:
			cw.pixels[:] = 6, 6, 20
		else:
			cw.pixels[:] = 0, 0, 0
		highscore_board.draw(highscores, last_initials, score, flash)
		key = cw.show(sleep_ms=220)
		if key in (27, ord("q"), ord("Q")):
			return False
		if key in (ord("r"), ord("R")):
			return True

		if motion_controller is not None:
			motion_controller.read_target_col(cols)
			camera_key = normalize_key(motion_controller.read_key())
			if camera_key in (27, ord("q"), ord("Q")):
				return False
			if camera_key in (ord("r"), ord("R")):
				return True


if __name__ == "__main__":
	parser = argparse.ArgumentParser(description="Hole runner for ContourWallEmulator.")
	parser.add_argument(
		"--physical",
		action="store_true",
		help="Use webcam motion as player input.",
	)
	parser.add_argument(
		"--camera-index",
		type=int,
		default=0,
		help="OpenCV camera index for --physical mode (default: 0).",
	)
	parser.add_argument(
		"--show-camera",
		action="store_true",
		help="Show webcam debug windows in --physical mode.",
	)
	args = parser.parse_args()

	cw = ContourWallEmulator()
	cw.new()

	motion_controller = None
	if args.physical:
		try:
			motion_controller = PoseController(
				camera_index=args.camera_index,
				show_window=args.show_camera,
			)
		except RuntimeError as exc:
			print(f"[INPUT WARN] {exc}")
			print("[INPUT WARN] Falling back to motion input.")
			try:
				motion_controller = PhysicalMotionController(
					camera_index=args.camera_index,
					show_window=args.show_camera,
				)
			except RuntimeError as inner_exc:
				print(f"[INPUT WARN] {inner_exc}")
				print("[INPUT WARN] Falling back to keyboard input.")

	try:
		while hole_runner(motion_controller=motion_controller):
			pass
	finally:
		if motion_controller is not None:
			motion_controller.close()
		time.sleep(1)
		cw.pixels[:] = 0, 0, 0
		cw.show()
