#!/usr/bin/env python3
"""
Subway Surfers style endless runner for the ContourWall emulator.

Controls:
- Move lanes: Left/Right arrows or A/D
- Quit: Q or ESC
- Restart after game over: R

Physical mode:
- Start with --physical
- Move left/right in front of a webcam to switch lanes.
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
from game_input import LEFT_KEYS, RIGHT_KEYS, PhysicalMotionController, normalize_key
from lives_display import draw_lives
from score_display import draw_score
from highscore_board import HighscoreBoard, highscore_path


@dataclass
class Obstacle:
    lane: int
    y: float


@dataclass
class Coin:
    lane: int
    y: float


class SubwaySurfersGame:
    def __init__(
        self,
        wall: ContourWall,
        motion_controller: PhysicalMotionController | None = None,
        player_name: str | None = None,
    ):
        self.cw = wall
        self.motion_controller = motion_controller
        self.use_physical_input = motion_controller is not None

        self.rows, self.cols = self.cw.pixels.shape[:2]
        self.base_row = max(5, self.rows - 4)
        self.lane_centers = self._compute_lane_centers()

        self.player_lane = 1
        self.player_x = float(self.lane_centers[self.player_lane])
        self.physical_col_float = float(self.cols // 2)
        self.lane_hysteresis = (self.cols / 3.0) * 0.07

        self.invuln_timer = 0
        self.crash_flash = 0

        self.obstacles: list[Obstacle] = []
        self.coins: list[Coin] = []

        self.score = 0
        self.collected_coins = 0
        self.distance = 0.0
        self.lives = 3
        self.frame = 0

        self.base_speed = 0.58 if self.use_physical_input else 0.66
        self.max_speed = 1.18 if self.use_physical_input else 1.46
        self.speed_ramp = 0.0014 if self.use_physical_input else 0.00185
        self.spawn_padding = 2 if self.use_physical_input else 0

        self.speed = self.base_speed
        self.spawn_timer = 15
        self.highscore_path = EXAMPLES_DIR / "subway_surfers.xml"
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

    def _draw_highscores(self, flash: bool) -> None:
        self.highscore_board.draw(self.highscores, self.last_initials, self.score, flash)

    def _compute_lane_centers(self) -> list[int]:
        return [
            max(3, self.cols // 6),
            self.cols // 2,
            min(self.cols - 4, (self.cols * 5) // 6),
        ]

    def reset_round(self) -> None:
        self.rows, self.cols = self.cw.pixels.shape[:2]
        self.base_row = max(5, self.rows - 4)
        self.lane_centers = self._compute_lane_centers()

        self.player_lane = 1
        self.player_x = float(self.lane_centers[self.player_lane])
        self.physical_col_float = float(self.cols // 2)
        self.lane_hysteresis = (self.cols / 3.0) * 0.07

        self.invuln_timer = 0
        self.crash_flash = 0

        self.obstacles.clear()
        self.coins.clear()

        self.score = 0
        self.collected_coins = 0
        self.distance = 0.0
        self.lives = 3
        self.frame = 0

        self.speed = self.base_speed
        self.spawn_timer = 15

    def _process_input(self, key: int, physical_col: int | None) -> bool:
        key = normalize_key(key)
        if key in (27, ord("q"), ord("Q")):
            return False

        if self.use_physical_input and physical_col is not None:
            self.physical_col_float = (0.45 * self.physical_col_float) + (
                0.55 * float(physical_col)
            )

            lane_width = self.cols / 3.0
            left_border = lane_width
            right_border = 2 * lane_width
            margin = self.lane_hysteresis
            pos = self.physical_col_float

            if self.player_lane == 0 and pos > (left_border + margin):
                self.player_lane = 1
            elif self.player_lane == 2 and pos < (right_border - margin):
                self.player_lane = 1
            elif self.player_lane == 1:
                if pos < (left_border - margin):
                    self.player_lane = 0
                elif pos > (right_border + margin):
                    self.player_lane = 2
        else:
            if key in LEFT_KEYS or key in (ord("a"), ord("A")):
                self.player_lane = max(0, self.player_lane - 1)
            elif key in RIGHT_KEYS or key in (ord("d"), ord("D")):
                self.player_lane = min(2, self.player_lane + 1)

        return True

    def _spawn_wave(self) -> None:
        lanes = [0, 1, 2]
        random.shuffle(lanes)

        block_lanes: list[int]
        if random.random() < 0.24:
            block_lanes = lanes[:2]
        else:
            block_lanes = [lanes[0]]

        for lane in block_lanes:
            self.obstacles.append(Obstacle(lane=lane, y=-2.2))

        safe_lanes = [lane for lane in [0, 1, 2] if lane not in block_lanes]
        if safe_lanes and random.random() < 0.78:
            coin_lane = random.choice(safe_lanes)
            self.coins.append(Coin(lane=coin_lane, y=-3.5))

        min_gap = max(10, int(24 - (self.speed * 6)) + self.spawn_padding)
        max_gap = max(min_gap + 2, int(33 - (self.speed * 6)) + self.spawn_padding)
        self.spawn_timer = random.randint(min_gap, max_gap)

    def _update_world(self) -> None:
        self.frame += 1
        self.speed = min(self.max_speed, self.base_speed + (self.distance * self.speed_ramp))
        self.distance += self.speed
        self.score += int(1 + self.speed * 1.2)

        if self.invuln_timer > 0:
            self.invuln_timer -= 1
        if self.crash_flash > 0:
            self.crash_flash -= 1

        target_x = float(self.lane_centers[self.player_lane])
        self.player_x += float(np.clip(target_x - self.player_x, -2.9, 2.9))

        if self.spawn_timer <= 0:
            self._spawn_wave()
        else:
            self.spawn_timer -= 1

        for obstacle in self.obstacles:
            obstacle.y += self.speed
        for coin in self.coins:
            coin.y += self.speed * 1.02

        self.obstacles = [o for o in self.obstacles if o.y < self.rows + 3]
        self.coins = [c for c in self.coins if c.y < self.rows + 2]

        self._check_collisions()

    def _check_collisions(self) -> None:
        player_row = self.base_row

        if self.invuln_timer <= 0:
            player_top = player_row - 2
            player_bottom = player_row + 1
            for obstacle in self.obstacles:
                if obstacle.lane != self.player_lane:
                    continue
                if not (player_top - 1 <= obstacle.y <= player_bottom + 1):
                    continue

                self.lives -= 1
                self.invuln_timer = 18
                self.crash_flash = 10
                self.obstacles.clear()
                self.coins.clear()
                self.player_lane = 1
                self.player_x = float(self.lane_centers[self.player_lane])
                self.spawn_timer = 16
                return

        remaining_coins: list[Coin] = []
        for coin in self.coins:
            if coin.lane == self.player_lane and abs(coin.y - player_row) <= 1.6:
                self.collected_coins += 1
                self.score += 45
            else:
                remaining_coins.append(coin)
        self.coins = remaining_coins

    def _fill_rect(
        self, row0: int, row1: int, col0: int, col1: int, color: tuple[int, int, int]
    ) -> None:
        row0 = int(np.clip(row0, 0, self.rows))
        row1 = int(np.clip(row1, 0, self.rows))
        col0 = int(np.clip(col0, 0, self.cols))
        col1 = int(np.clip(col1, 0, self.cols))
        if row1 <= row0 or col1 <= col0:
            return
        self.cw.pixels[row0:row1, col0:col1] = color

    def _set_pixel(self, row: int, col: int, color: tuple[int, int, int]) -> None:
        if 0 <= row < self.rows and 0 <= col < self.cols:
            self.cw.pixels[row, col] = color

    def _draw_background(self) -> None:
        self.cw.pixels[:] = (5, 7, 12)

        for row in range(self.rows):
            shade = 5 + int((row / max(1, self.rows - 1)) * 18)
            self.cw.pixels[row, :] = (shade // 2, shade // 2, shade)

        boundaries = [self.cols // 3, (self.cols * 2) // 3]
        for b in boundaries:
            for row in range(2, self.rows):
                if ((row + (self.frame // 2)) % 6) < 3:
                    self._fill_rect(row, row + 1, b - 1, b + 1, (22, 26, 36))

        for i in range(10):
            row = (self.frame + i * 4) % self.rows
            col = (i * 9 + self.frame) % self.cols
            if row > 2:
                self._fill_rect(row, row + 1, col, col + 1, (18, 20, 30))

        if self.crash_flash > 0 and (self.crash_flash % 2 == 0):
            bright = np.clip(self.cw.pixels.astype(np.int16) + 45, 0, 255)
            self.cw.pixels[:, :] = bright.astype(np.uint8)

    def _draw_obstacles_and_coins(self) -> None:
        for obstacle in self.obstacles:
            y = int(round(obstacle.y))
            if y < -4 or y >= self.rows + 3:
                continue

            center_x = self.lane_centers[obstacle.lane]
            width = int(np.clip(3 + (max(y, 0) / max(1, self.rows - 1)) * 5, 3, 8))
            x0 = center_x - width
            x1 = center_x + width + 1
            self._fill_rect(y - 2, y + 2, x0, x1, (230, 80, 70))

        for coin in self.coins:
            y = int(round(coin.y))
            if y < 0 or y >= self.rows:
                continue
            x = self.lane_centers[coin.lane]
            self._fill_rect(y, y + 1, x - 1, x + 2, (255, 220, 80))
            self._fill_rect(y - 1, y, x, x + 1, (255, 220, 80))
            self._fill_rect(y + 1, y + 2, x, x + 1, (255, 220, 80))

    def _draw_runner(self) -> None:
        row = self.base_row
        x = int(round(self.player_x))

        outline = (6, 10, 18)
        head = (255, 232, 124)
        torso = (82, 246, 232)
        accent = (128, 255, 244)
        lane_marker = (255, 245, 148)

        if self.invuln_timer > 0 and (self.invuln_timer % 2 == 1):
            dim = 0.42
            outline = tuple(int(c * dim) for c in outline)
            head = tuple(int(c * dim) for c in head)
            torso = tuple(int(c * dim) for c in torso)
            accent = tuple(int(c * dim) for c in accent)
            lane_marker = tuple(int(c * dim) for c in lane_marker)

        # A small floor strip makes lane position obvious at a glance.
        self._fill_rect(row + 2, row + 3, x - 2, x + 3, lane_marker)

        step_phase = (self.frame // 3) % 2
        if step_phase == 0:
            leg_cols = (-1, 1)
            arm_offsets = [(-1, -2), (-1, 2)]
        else:
            leg_cols = (-2, 0)
            arm_offsets = [(-2, -2), (-2, 2)]

        sprite_pixels: list[tuple[int, int, tuple[int, int, int]]] = [
            (row - 3, x, head),
            (row - 2, x - 1, head),
            (row - 2, x, head),
            (row - 2, x + 1, head),
            (row - 1, x - 1, torso),
            (row - 1, x, torso),
            (row - 1, x + 1, torso),
            (row, x - 1, torso),
            (row, x, torso),
            (row, x + 1, torso),
        ]
        for dr, dc in arm_offsets:
            sprite_pixels.append((row + dr, x + dc, accent))
        for dc in leg_cols:
            sprite_pixels.append((row + 1, x + dc, accent))

        occupied: set[tuple[int, int]] = set()
        for r, c, _ in sprite_pixels:
            if 0 <= r < self.rows and 0 <= c < self.cols:
                occupied.add((r, c))

        for r, c in occupied:
            for nr in range(r - 1, r + 2):
                for nc in range(c - 1, c + 2):
                    if (nr, nc) in occupied:
                        continue
                    self._set_pixel(nr, nc, outline)

        for r, c, color in sprite_pixels:
            self._set_pixel(r, c, color)

    def _draw_hud(self) -> None:
        draw_lives(self.cw, self.lives, start_row=0, start_col=0, spacing=4)

        score_width = min(self.cols, self.score // 110)
        if score_width > 0:
            self._fill_rect(0, 1, self.cols - score_width, self.cols, (90, 175, 255))

        distance_width = min(self.cols // 2, int(self.distance // 22))
        if distance_width > 0:
            self._fill_rect(1, 2, 0, distance_width, (60, 220, 110))

    def _draw_digit(self, digit: int, color: tuple[int, int, int]) -> None:
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

        start_row = max(2, (self.rows // 2) - 2)
        start_col = max(1, (self.cols // 2) - 1)
        self.cw.fill_solid(0, 0, 0)
        for r, row in enumerate(pattern):
            for c, bit in enumerate(row):
                if bit == "1":
                    self._fill_rect(
                        start_row + r, start_row + r + 1, start_col + c, start_col + c + 1, color
                    )

    def _render(self) -> None:
        self._draw_background()
        self._draw_obstacles_and_coins()
        self._draw_runner()
        self._draw_hud()

    def _wait_for_restart(self) -> None:
        print(
            f"Game over. Score: {self.score}. Distance: {int(self.distance)}."
        )
        self._record_highscore()
        start = time.perf_counter()
        flash = False
        while time.perf_counter() - start < 5.0:
            flash = not flash
            self.cw.fill_solid(0, 0, 0)
            self._draw_highscores(flash)
            self.cw.show(sleep_ms=220)

    def run(self) -> int:
        print("Subway Surfers (ContourWall Edition)")
        if self.use_physical_input:
            print("Physical mode enabled: move left-right in front of your webcam.")
        else:
            print("Keyboard mode: A/D or arrows for lanes.")
        print("Lane dodge only. Quit: Q/ESC")

        print("Starting in 5...")
        for count in range(5, 0, -1):
            self._draw_digit(count, (80, 220, 255))
            self.cw.show(sleep_ms=1000)

        self.reset_round()
        key = -1

        while self.lives > 0:
            frame_start = time.perf_counter()

            physical_col = None
            if self.motion_controller is not None:
                physical_col = self.motion_controller.read_target_col(self.cols)
                camera_key = normalize_key(self.motion_controller.read_key())
                if camera_key in (27, ord("q"), ord("Q")):
                    return self.score
                if camera_key != -1:
                    key = camera_key

            if not self._process_input(key, physical_col):
                return self.score

            self._update_world()
            self._render()
            key = normalize_key(self.cw.show())

            frame_time = time.perf_counter() - frame_start
            target_dt = 0.051 if self.use_physical_input else 0.044
            if frame_time < target_dt:
                time.sleep(target_dt - frame_time)

        self._wait_for_restart()
        return self.score


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Subway Surfers style demo for ContourWallEmulator."
    )
    parser.add_argument(
        "--physical",
        action="store_true",
        help="Use webcam motion as lane input (left-right).",
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
        help="Show webcam debug window in --physical mode.",
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
    game = SubwaySurfersGame(
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
