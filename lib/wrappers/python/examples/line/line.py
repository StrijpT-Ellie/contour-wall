#!/usr/bin/env python3
"""
Stay-in-lane game for the ContourWall emulator.

Controls:
- Move lanes: Arrow keys or A/D
- Quit: Q or ESC

Physical mode:
- Start with --physical
- Move your hand/body left-right in front of a webcam
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
import random
import sys
import time

import cv2 as cv
import numpy as np

_THIS_DIR = Path(__file__).resolve().parent
EXAMPLES_DIR = _THIS_DIR.parent
UTILS_DIR = EXAMPLES_DIR / "utils"
WRAPPER_DIR = EXAMPLES_DIR.parent

for _p in (str(WRAPPER_DIR), str(UTILS_DIR)):
	if _p not in sys.path:
		sys.path.insert(0, _p)

from contourwall import ContourWall
from game_input import (
	LEFT_KEYS,
	RIGHT_KEYS,
	PhysicalMotionController,
	normalize_key,
)
from lives_display import draw_lives
from score_display import draw_score
from highscore_board import HighscoreBoard, highscore_path


@dataclass
class Particle:
	"""Represents a single particle in the effect system"""
	x: float
	y: float
	vx: float
	vy: float
	life: float
	max_life: float
	color: tuple[int, int, int]

	def update(self) -> bool:
		"""Update particle position and life. Returns True if still alive."""
		self.x += self.vx
		self.y += self.vy
		self.vy += 0.05
		self.life -= 1
		return self.life > 0

	def render(self, pixels: np.ndarray) -> None:
		"""Draw particle to pixels array"""
		x, y = int(self.x), int(self.y)
		rows, cols = pixels.shape[:2]
		if 0 <= x < cols and 0 <= y < rows:
			alpha = self.life / self.max_life
			color = tuple(int(c * alpha) for c in self.color)
			pixels[y, x] = color


@dataclass
class LaneState:
	current: int
	target: int
	target_time: float = 0.0


class LaneStayGame:
	FASTER_FONT = {
		'F': [
			[1,1,1], [1,0,0], [1,1,0], [1,0,0], [1,0,0]
		],
		'A': [
			[0,1,0], [1,0,1], [1,1,1], [1,0,1], [1,0,1]
		],
		'S': [
			[1,1,1], [1,0,0], [1,1,1], [0,0,1], [1,1,1]
		],
		'T': [
			[1,1,1], [0,1,0], [0,1,0], [0,1,0], [0,1,0]
		],
		'E': [
			[1,1,1], [1,0,0], [1,1,0], [1,0,0], [1,1,1]
		],
		'R': [
			[1,1,0], [1,0,1], [1,1,0], [1,0,1], [1,0,1]
		]
	}

	def __init__(
		self,
		wall: ContourWall,
		motion_controller: PhysicalMotionController | None = None,
		player_name: str | None = None,
	):
		self.cw = wall
		self.motion_controller = motion_controller
		self.use_physical_input = motion_controller is not None
		self.rows, self.cols = wall.pixels.shape[:2]
		self.player_row = max(2, self.rows - 3)
		self.lane_state = LaneState(current=1, target=1, target_time=time.time())
		self.score = 0
		self.successful_scores = 0  # Track consecutive successes for speed-up
		self.lives = 3
		self.base_tick_interval = 1.8
		self.tick_interval = self.base_tick_interval
		self.last_tick = time.time()
		self.physical_col_float = float(self.cols // 2)
		self.frame_count = 0
		self.score_flash = 0
		self.particles: list[Particle] = []
		self.faster_flash_frames = 0
		self.faster_flash_max = 36  # ~1.8s at 20ms per frame
		self.faster_flash_colors = [(255, 255, 0), (0, 255, 255)]
		self.faster_flash_color_idx = 0
		self.faster_flash_score = 0
		self.highscore_path = highscore_path(EXAMPLES_DIR, "line")
		self.highscores: list[tuple[str, int]] = []
		self.last_initials = (
			HighscoreBoard.normalize_initials(player_name)
			if player_name
			else "YOU"
		)
		self.allow_prompt = not bool(player_name)
		self.highscore_board = HighscoreBoard(self.rows, self.cols, self.cw.pixels)
		self.highscores = self.highscore_board.load(self.highscore_path)

	def _record_highscore(self) -> None:
		self.last_initials, self.highscores = self.highscore_board.record_and_save(
			self.highscores,
			self.score,
			self.last_initials,
			self.highscore_path,
			allow_prompt=self.allow_prompt,
		)

	def _show_highscores(self) -> None:
		start = time.perf_counter()
		flash = False
		while time.perf_counter() - start < 5.0:
			flash = not flash
			self.cw.fill_solid(0, 0, 0)
			self.highscore_board.draw(self.highscores, self.last_initials, self.score, flash)
			self.cw.show(sleep_ms=220)

	def reset(self) -> None:
		self.rows, self.cols = self.cw.pixels.shape[:2]
		self.player_row = max(2, self.rows - 3)
		self.lane_state = LaneState(current=1, target=random.randint(0, 2), target_time=time.time())
		self.score = 0
		self.successful_scores = 0
		self.lives = 3
		self.last_tick = time.time()
		self.physical_col_float = float(self.cols // 2)
		self.frame_count = 0
		self.score_flash = 0
		self.particles = []

	def _lane_cols(self) -> list[int]:
		return [max(1, self.cols // 6), self.cols // 2, min(self.cols - 2, (self.cols * 5) // 6)]

	def _target_lane_from_col(self, col: int) -> int:
		lane_width = self.cols / 3.0
		return int(np.clip(col // lane_width, 0, 2))

	def _update_player_lane(self, key: int, physical_col: int | None = None) -> bool:
		key = normalize_key(key)
		if key in (27, ord("q"), ord("Q")):
			return False

		if self.use_physical_input and physical_col is not None:
			self.physical_col_float = (0.6 * self.physical_col_float) + (0.4 * float(physical_col))
			lane_width = self.cols / 3.0
			margin = lane_width * 0.08
			boundary_left = lane_width - margin
			boundary_right = (2 * lane_width) + margin
			if self.lane_state.current == 0 and self.physical_col_float > boundary_left:
				self.lane_state.current = 1
			elif self.lane_state.current == 2 and self.physical_col_float < boundary_right:
				self.lane_state.current = 1
			elif self.lane_state.current == 1:
				if self.physical_col_float < boundary_left:
					self.lane_state.current = 0
				elif self.physical_col_float > boundary_right:
					self.lane_state.current = 2
			return True

		if key in LEFT_KEYS or key in (ord("a"), ord("A")):
			self.lane_state.current = max(0, self.lane_state.current - 1)
		elif key in RIGHT_KEYS or key in (ord("d"), ord("D")):
			self.lane_state.current = min(2, self.lane_state.current + 1)
		return True

	def _tick_scoring(self) -> None:
		if self.faster_flash_frames > 0:
			return  # Pause scoring during FASTER flash
		if time.time() - self.last_tick < self.tick_interval:
			return
		self.last_tick = time.time()

		if self.lane_state.current == self.lane_state.target:
			self.score += 1
			self.successful_scores += 1
			self.score_flash = 10
			self._emit_score_particles()
			# Speed up every 3 successful scores
			if self.successful_scores % 3 == 0:
				self.faster_flash_frames = self.faster_flash_max
				self.faster_flash_score = self.score
				# Update tick_interval before flashing (0.90 = 10% faster each time)
				self.tick_interval = max(0.5, self.base_tick_interval * (0.90 ** (self.successful_scores // 3)))
		else:
			self.lives -= 1
			self._emit_damage_particles()

		self.lane_state.target = random.randint(0, 2)
		self.lane_state.target_time = time.time()

	def _emit_score_particles(self) -> None:
		"""Emit gold particles when scoring"""
		lane_cols = self._lane_cols()
		player_col = lane_cols[self.lane_state.current]
		for _ in range(12):
			angle = random.uniform(0, 2 * np.pi)
			speed = random.uniform(0.5, 2.0)
			vx = speed * np.cos(angle)
			vy = speed * np.sin(angle)
			particle = Particle(
				x=float(player_col),
				y=float(self.player_row),
				vx=vx,
				vy=vy,
				life=30,
				max_life=30,
				color=(0, 255, 0)
			)
			self.particles.append(particle)

	def _emit_damage_particles(self) -> None:
		"""Emit red particles when losing a life"""
		lane_cols = self._lane_cols()
		player_col = lane_cols[self.lane_state.current]
		for _ in range(16):
			angle = random.uniform(0, 2 * np.pi)
			speed = random.uniform(0.8, 2.5)
			vx = speed * np.cos(angle)
			vy = speed * np.sin(angle)
			particle = Particle(
				x=float(player_col),
				y=float(self.player_row),
				vx=vx,
				vy=vy,
				life=35,
				max_life=35,
				color=(0, 0, 255)
			)
			self.particles.append(particle)

	def draw_text_block(self, pixels, text, row, col, color):
		for idx, char in enumerate(text):
			if char not in self.FASTER_FONT:
				continue
			pattern = self.FASTER_FONT[char]
			for r in range(5):
				for c in range(3):
					if pattern[r][c]:
						pixels[row + r, col + idx * 4 + c] = color

	def _draw(self) -> None:
		self.cw.pixels[:] = (8, 10, 25)

		lane_cols = self._lane_cols()
		time_elapsed = time.time() - self.lane_state.target_time
		fill_ratio = max(0, 1.0 - (time_elapsed / self.tick_interval))

		# FASTER flash: all lanes fully lit, no timer, target lane not highlighted
		if self.faster_flash_frames > 0:
			for i, col in enumerate(lane_cols):
				color = (40, 50, 90)
				self.cw.pixels[:, col] = color
				self.cw.pixels[:, col + 1] = tuple(c // 2 for c in color)
		else:
			for i, col in enumerate(lane_cols):
				color = (40, 50, 90)
				if i == self.lane_state.target:
					pulse = int(30 * (0.5 + 0.5 * np.sin(self.frame_count * 0.1)))
					color = (50 + pulse, 220 + pulse, 100 + pulse)
					fill_height = int(self.rows * fill_ratio)
					if fill_height > 0:
						self.cw.pixels[self.rows - fill_height:, col] = color
						self.cw.pixels[self.rows - fill_height:, col + 1] = tuple(c // 2 for c in color)
					if fill_height < self.rows:
						self.cw.pixels[:self.rows - fill_height, col] = (20, 20, 30)
						self.cw.pixels[:self.rows - fill_height, col + 1] = (10, 10, 15)
				else:
					self.cw.pixels[:, col] = color
					self.cw.pixels[:, col + 1] = tuple(c // 2 for c in color)

		player_col = lane_cols[self.lane_state.current]
		player_color = (255, 220, 80)
		if self.score_flash > 0:
			flash_intensity = int(100 * (self.score_flash / 10.0))
			player_color = (255, 255, min(255, 80 + flash_intensity // 2))
		self.cw.pixels[self.player_row:self.player_row + 2, player_col:player_col + 2] = player_color

		# Update and render particles
		self.particles = [p for p in self.particles if p.update()]
		for particle in self.particles:
			particle.render(self.cw.pixels)

		draw_lives(self.cw, self.lives)

		score_color = (90, 160, 255)
		if self.score_flash > 0:
			score_color = (150, 200, 255)
		draw_score(self.cw.pixels, self.score, start_row=0, color=score_color, position='right')

		# FASTER flash text
		if self.faster_flash_frames > 0:
			color = self.faster_flash_colors[(self.faster_flash_frames // 6) % 2]
			text = 'FASTER'
			row = self.rows // 2 - 2
			col = (self.cols - 6 * 4 + 1) // 2
			self.draw_text_block(self.cw.pixels, text, row, col, color)
			self.faster_flash_frames -= 1
			# Reset timers when flash ends to prevent immediate scoring and show active lane properly
			if self.faster_flash_frames == 0:
				self.last_tick = time.time()
				self.lane_state.target_time = time.time()

		self.frame_count += 1
		if self.score_flash > 0:
			self.score_flash -= 1

	def _draw_digit(self, digit: int) -> None:
		patterns = {
			0: ["111", "101", "101", "101", "111"],
			1: ["010", "110", "010", "010", "111"],
			2: ["111", "001", "111", "100", "111"],
			3: ["111", "001", "111", "001", "111"],
			4: ["101", "101", "111", "001", "001"],
			5: ["111", "100", "111", "001", "111"],
			6: ["111", "100", "111", "101", "111"],
			7: ["111", "001", "001", "001", "001"],
			8: ["111", "101", "111", "101", "111"],
			9: ["111", "101", "111", "001", "111"],
		}
		pattern = patterns.get(digit)
		if pattern is None:
			return
		start_row = max(0, (self.rows // 2) - 2)
		start_col = max(0, (self.cols // 2) - 1)
		self.cw.fill_solid(0, 0, 0)
		for r, row in enumerate(pattern):
			for c, ch in enumerate(row):
				if ch == "1":
					self.cw.pixels[start_row + r, start_col + c] = (30, 200, 90)

	# Block font for FASTER (5x3 per letter)
	FASTER_FONT = {
		'F': [
			[1,1,1], [1,0,0], [1,1,0], [1,0,0], [1,0,0]
		],
		'A': [
			[0,1,0], [1,0,1], [1,1,1], [1,0,1], [1,0,1]
		],
		'S': [
			[1,1,1], [1,0,0], [1,1,1], [0,0,1], [1,1,1]
		],
		'T': [
			[1,1,1], [0,1,0], [0,1,0], [0,1,0], [0,1,0]
		],
		'E': [
			[1,1,1], [1,0,0], [1,1,0], [1,0,0], [1,1,1]
		],
		'R': [
			[1,1,0], [1,0,1], [1,1,0], [1,0,1], [1,0,1]
		]
	}

	def run(self) -> None:
		print("Lane Stay Game")
		if self.use_physical_input:
			print("Physical mode enabled: move left-right in front of your webcam.")
		else:
			print("Move with Arrow keys or A/D.")
		print("Match the green lane to score. Misses cost a life.")
		print("Starting in 5...")
		for count in range(5, 0, -1):
			self._draw_digit(count)
			self.cw.show(sleep_ms=1000)

		self.reset()
		key = -1
		while self.lives > 0:
			frame_start = time.perf_counter()

			physical_col = None
			if self.motion_controller is not None:
				physical_col = self.motion_controller.read_target_col(self.cols)
				camera_key = normalize_key(self.motion_controller.read_key())
				if camera_key in (27, ord("q"), ord("Q")):
					return

			if not self._update_player_lane(key, physical_col=physical_col):
				return

			self._tick_scoring()
			self._draw()
			key = normalize_key(cv.waitKey(1))
			self.cw.show()

			frame_time = time.perf_counter() - frame_start
			target_dt = 0.05
			if frame_time < target_dt:
				time.sleep(target_dt - frame_time)

		print(f"Game over. Score: {self.score}")
		self._record_highscore()
		self._show_highscores()


def main() -> None:
	parser = argparse.ArgumentParser(
		description="Stay-in-lane game for ContourWallEmulator."
	)
	parser.add_argument(
		"--physical",
		action="store_true",
		help="Use webcam motion as physical player input (left-right).",
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
	parser.add_argument(
		"--player-name",
		type=str,
		default="",
		help="Player name to use for highscores.",
	)
	args = parser.parse_args()

	random.seed()
	cw = ContourWall()
	cw.new_with_ports("COM10", "COM12", "COM9", "COM14", "COM13", "COM11")

	motion_controller: PhysicalMotionController | None = None
	if args.physical:
		try:
			motion_controller = PhysicalMotionController(
				camera_index=args.camera_index,
				show_window=args.show_camera,
			)
		except RuntimeError as exc:
			print(f"[INPUT WARN] {exc}")
			print("[INPUT WARN] Falling back to keyboard input.")

	player_name = args.player_name.strip()
	game = LaneStayGame(
		cw,
		motion_controller=motion_controller,
		player_name=player_name or None,
	)

	try:
		game.run()
	finally:
		if motion_controller is not None:
			motion_controller.close()
		cw.fill_solid(0, 0, 0)
		cw.show()
		cv.destroyAllWindows()


if __name__ == "__main__":
	main()