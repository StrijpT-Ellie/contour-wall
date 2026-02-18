#!/usr/bin/env python3
"""
Brick Breaker for ContourWallEmulator.

Controls:
- Move: Left/Right arrows or A/D
- Quit: Q or ESC
- Restart after game over: R

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
try:
    import mediapipe as mp
except ImportError:
    mp = None

_THIS_DIR = Path(__file__).resolve().parent
EXAMPLES_DIR = _THIS_DIR.parent
UTILS_DIR = EXAMPLES_DIR / "utils"
WRAPPER_DIR = EXAMPLES_DIR.parent

for _p in (str(WRAPPER_DIR), str(UTILS_DIR)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from contourwall_emulator import ContourWallEmulator
from game_input import LEFT_KEYS, RIGHT_KEYS, PhysicalMotionController, normalize_key
from lives_display import draw_lives
from highscore_board import HighscoreBoard, highscore_path


class PoseController:
    def __init__(self, camera_index=0, show_window=False):
        self.show_window = show_window
        if cv is None or mp is None or not hasattr(mp, "solutions"):
            raise RuntimeError("MediaPipe Pose is unavailable.")
        self.use_cuda = bool(getattr(cv, "cuda", None)) and cv.cuda.getCudaEnabledDeviceCount() > 0
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
        self.gpu_frame = cv.cuda_GpuMat() if self.use_cuda else None

    def read_key(self):
        if not self.show_window or cv is None:
            return -1
        return normalize_key(cv.waitKey(1))

    def read_target_col(self, cols):
        ret, frame = self.cap.read()
        if not ret:
            return None
        if self.use_cuda:
            self.gpu_frame.upload(frame)
            flipped = cv.cuda.flip(self.gpu_frame, 1)
            rgb = cv.cuda.cvtColor(flipped, cv.COLOR_BGR2RGB).download()
            frame = rgb[:, :, ::-1]
        else:
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


@dataclass
class Brick:
    x0: int
    x1: int
    y: int
    color: tuple[int, int, int]


class BrickBreakerGame:
    DIGIT_PATTERNS = {
        "0": ["111", "101", "101", "101", "111"],
        "1": ["010", "110", "010", "010", "111"],
        "2": ["111", "001", "111", "100", "111"],
        "3": ["111", "001", "111", "001", "111"],
        "4": ["101", "101", "111", "001", "001"],
        "5": ["111", "100", "111", "001", "111"],
        "6": ["111", "100", "111", "101", "111"],
        "7": ["111", "001", "001", "001", "001"],
        "8": ["111", "101", "111", "101", "111"],
        "9": ["111", "101", "111", "001", "111"],
    }
    CHAR_PATTERNS = {
        "A": ["010", "101", "111", "101", "101"],
        "B": ["110", "101", "110", "101", "110"],
        "C": ["011", "100", "100", "100", "011"],
        "D": ["110", "101", "101", "101", "110"],
        "E": ["111", "100", "110", "100", "111"],
        "F": ["111", "100", "110", "100", "100"],
        "G": ["011", "100", "101", "101", "011"],
        "H": ["101", "101", "111", "101", "101"],
        "I": ["111", "010", "010", "010", "111"],
        "J": ["001", "001", "001", "101", "010"],
        "K": ["101", "110", "100", "110", "101"],
        "L": ["100", "100", "100", "100", "111"],
        "M": ["101", "111", "111", "101", "101"],
        "N": ["101", "111", "111", "101", "101"],
        "O": ["111", "101", "101", "101", "111"],
        "P": ["110", "101", "110", "100", "100"],
        "Q": ["111", "101", "101", "111", "001"],
        "R": ["110", "101", "110", "101", "101"],
        "S": ["011", "100", "111", "001", "110"],
        "T": ["111", "010", "010", "010", "010"],
        "U": ["101", "101", "101", "101", "111"],
        "V": ["101", "101", "101", "101", "010"],
        "W": ["101", "101", "111", "111", "101"],
        "X": ["101", "101", "010", "101", "101"],
        "Y": ["101", "101", "010", "010", "010"],
        "Z": ["111", "001", "010", "100", "111"],
        "_": ["000", "000", "000", "000", "111"],
    }

    def __init__(
        self,
        wall: ContourWallEmulator,
        motion_controller: PhysicalMotionController | None = None,
        player_name: str | None = None,
    ):
        self.cw = wall
        self.motion_controller = motion_controller
        self.use_physical_input = motion_controller is not None

        self.rows, self.cols = wall.pixels.shape[:2]
        self.paddle_width = max(7, (self.cols // 9) + 2)
        self.paddle_row = self.rows - 3

        self.paddle_x = 0.0
        self.ball_x = 0.0
        self.ball_y = 0.0
        self.ball_vx = 0.0
        self.ball_vy = 0.0

        self.bricks: list[Brick] = []
        self.score = 0
        self.lives = 3
        self.level = 1
        self.frame = 0
        self.highscore_path = highscore_path(EXAMPLES_DIR, "brick_breaker")
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

    def reset_game(self) -> None:
        self.score = 0
        self.lives = 3
        self.level = 1
        self.frame = 0
        self._start_level(self.level)

    def _start_level(self, level: int) -> None:
        self.level = level
        self._create_bricks(level)
        self.paddle_x = (self.cols - self.paddle_width) / 2
        self._reset_ball()

    def _create_bricks(self, level: int) -> None:
        row_count = min(7, 4 + max(0, level - 1))
        brick_w = max(4, self.cols // 13)
        gap = 1
        col_count = max(6, self.cols // (brick_w + gap))
        total_w = col_count * brick_w + (col_count - 1) * gap
        x_start = max(0, (self.cols - total_w) // 2)
        palette = [
            (230, 90, 35),
            (220, 160, 35),
            (80, 220, 90),
            (45, 160, 240),
            (155, 120, 245),
            (245, 120, 210),
        ]

        self.bricks.clear()
        for row in range(row_count):
            y = 2 + (row * 2)
            if y >= self.paddle_row - 3:
                break
            color = palette[row % len(palette)]
            for i in range(col_count):
                x0 = x_start + i * (brick_w + gap)
                x1 = min(self.cols - 1, x0 + brick_w - 1)
                self.bricks.append(Brick(x0=x0, x1=x1, y=y, color=color))

    def _reset_ball(self) -> None:
        self.ball_x = self.paddle_x + (self.paddle_width / 2)
        self.ball_y = self.paddle_row - 1.2
        speed = 1.05 + (self.level * 0.06)
        vx_seed = random.choice([-0.85, -0.7, 0.7, 0.85])
        self.ball_vx = vx_seed
        self.ball_vy = -max(0.75, speed - abs(vx_seed) * 0.35)

    def _process_input(self, key: int, physical_target_col: int | None) -> bool:
        key = normalize_key(key)
        if key in (27, ord("q"), ord("Q")):
            return False

        if self.use_physical_input and physical_target_col is not None:
            target_left = float(
                np.clip(
                    physical_target_col - (self.paddle_width / 2),
                    0,
                    self.cols - self.paddle_width,
                )
            )
            self.paddle_x += float(np.clip(target_left - self.paddle_x, -2.6, 2.6))
            return True

        if key in LEFT_KEYS or key in (ord("a"), ord("A")):
            self.paddle_x -= 2.2
        elif key in RIGHT_KEYS or key in (ord("d"), ord("D")):
            self.paddle_x += 2.2

        self.paddle_x = float(np.clip(self.paddle_x, 0, self.cols - self.paddle_width))
        return True

    def _update_ball(self) -> None:
        prev_x = self.ball_x
        prev_y = self.ball_y
        next_x = self.ball_x + self.ball_vx
        next_y = self.ball_y + self.ball_vy

        if next_x <= 0:
            next_x = 0
            self.ball_vx = abs(self.ball_vx)
        elif next_x >= self.cols - 1:
            next_x = self.cols - 1
            self.ball_vx = -abs(self.ball_vx)

        if next_y <= 2:
            next_y = 2
            self.ball_vy = abs(self.ball_vy)

        # Paddle collision: only bounce when crossing the paddle plane from above.
        paddle_y = self.paddle_row - 1.2
        if self.ball_vy > 0 and prev_y < paddle_y <= next_y:
            if (self.paddle_x - 0.4) <= next_x <= (self.paddle_x + self.paddle_width + 0.4):
                hit_offset = (
                    next_x - (self.paddle_x + self.paddle_width / 2)
                ) / max(1.0, self.paddle_width / 2)
                hit_offset = float(np.clip(hit_offset, -1.0, 1.0))

                base_speed = min(2.4, 1.05 + self.level * 0.09 + self.score / 1400)
                self.ball_vx = float(np.clip(hit_offset * 1.45, -1.35, 1.35))
                self.ball_vy = -max(0.78, base_speed - abs(self.ball_vx) * 0.30)
                next_y = self.paddle_row - 1.25

        # Brick collision: detect entry side to reduce jittery bounces.
        hit_idx = -1
        hit_axis = "y"
        for idx, brick in enumerate(self.bricks):
            inside_next = brick.x0 <= next_x <= brick.x1 and brick.y <= next_y <= (brick.y + 1)
            if not inside_next:
                continue

            enter_from_top = prev_y < brick.y <= next_y
            enter_from_bottom = prev_y > (brick.y + 1) >= next_y
            enter_from_left = prev_x < brick.x0 <= next_x
            enter_from_right = prev_x > brick.x1 >= next_x

            if enter_from_left or enter_from_right:
                hit_axis = "x"
            elif enter_from_top or enter_from_bottom:
                hit_axis = "y"
            else:
                # Fallback: pick axis with smaller overlap
                dx = min(abs(next_x - brick.x0), abs(next_x - brick.x1))
                dy = min(abs(next_y - brick.y), abs(next_y - (brick.y + 1)))
                hit_axis = "x" if dx < dy else "y"

            hit_idx = idx
            break

        if hit_idx != -1:
            self.bricks.pop(hit_idx)
            self.score += 12 + (self.level * 2)
            if hit_axis == "x":
                self.ball_vx *= -1
            else:
                self.ball_vy *= -1
            speed_scale = 1.01
            self.ball_vx *= speed_scale
            self.ball_vy *= speed_scale
            self.ball_vx = float(np.clip(self.ball_vx, -1.45, 1.45))
            self.ball_vy = float(np.clip(self.ball_vy, -1.85, 1.85))
            next_y = self.ball_y + self.ball_vy

        self.ball_x = next_x
        self.ball_y = next_y

        if self.ball_y >= self.rows - 1:
            self.lives -= 1
            if self.lives > 0:
                self._reset_ball()

    def _draw_hud(self) -> None:
        draw_lives(self.cw, self.lives, start_row=0, start_col=0, spacing=4)

        level_start = min(self.cols - 1, (self.lives * 4) + 1)
        level_width = min(max(0, self.cols - level_start), self.level * 4)
        if level_width > 0:
            self.cw.pixels[1, level_start:level_start + level_width] = (80, 140, 250)

        self.highscore_board.draw_number(
            value=self.score,
            top_row=0,
            right_col=self.cols - 1,
            color=(245, 245, 245),
        )

    def _draw_digit(self, digit: int) -> None:
        if digit < 0 or digit > 9:
            return
        start_row = max(0, (self.rows // 2) - 2)
        start_col = max(0, (self.cols // 2) - 1)
        self.cw.fill_solid(0, 0, 0)
        right_col = min(self.cols - 1, start_col + 2)
        self.highscore_board.draw_number(
            value=digit,
            top_row=start_row,
            right_col=right_col,
            color=(80, 140, 250),
        )

    def _render(self) -> None:
        self.cw.pixels[:] = (6, 10, 18)

        for i in range(16):
            row = (self.frame + i * 7) % self.rows
            col = (i * 9 + self.frame // 2) % self.cols
            if row > 1:
                self.cw.pixels[row, col] = (16, 24, 38)

        for brick in self.bricks:
            self.cw.pixels[brick.y:brick.y + 2, brick.x0:brick.x1 + 1] = brick.color

        px0 = int(round(self.paddle_x))
        px1 = int(np.clip(px0 + self.paddle_width, 0, self.cols))
        self.cw.pixels[self.paddle_row:self.paddle_row + 2, px0:px1] = (250, 235, 115)

        bx = int(np.clip(round(self.ball_x), 0, self.cols - 1))
        by = int(np.clip(round(self.ball_y), 2, self.rows - 1))
        self.cw.pixels[by, bx] = (245, 245, 245)

        self._draw_hud()

    def _wait_for_restart_or_quit(self) -> bool:
        print(f"Game over. Final score: {self.score}. Returning to launcher.")
        if self.highscores:
            print("Top scores:")
            for idx, (name, score) in enumerate(self.highscores[:10], start=1):
                print(f" {idx:>2}. {name} - {score}")
        start = time.perf_counter()
        flash = False
        while time.perf_counter() - start < 5.0:
            flash = not flash
            if flash:
                self.cw.fill_solid(6, 6, 20)
            else:
                self.cw.fill_solid(0, 0, 0)
            self._draw_highscores(flash)
            self.cw.show(sleep_ms=220)
        return False

    def run(self) -> None:
        print("Brick Breaker")
        if self.use_physical_input:
            print("Physical mode enabled: move left-right in front of your webcam.")
        else:
            print("Move paddle with Left/Right or A/D.")
        print("Press Q or ESC to quit.")

        print("Starting in 5...")
        for count in range(5, 0, -1):
            self._draw_digit(count)
            self.cw.show(sleep_ms=1000)

        running = True
        while running:
            self.reset_game()
            key = -1

            while self.lives > 0:
                frame_start = time.perf_counter()
                self.frame += 1

                physical_target_col = None
                if self.motion_controller is not None:
                    physical_target_col = self.motion_controller.read_target_col(self.cols)
                    camera_key = normalize_key(self.motion_controller.read_key())
                    if camera_key in (27, ord("q"), ord("Q")):
                        return

                if not self._process_input(key, physical_target_col):
                    return

                self._update_ball()
                if not self.bricks:
                    self._start_level(self.level + 1)

                self._render()
                key = self.cw.show()

                frame_time = time.perf_counter() - frame_start
                target_dt = 0.038  # ~26 FPS
                if frame_time < target_dt:
                    time.sleep(target_dt - frame_time)

            self._record_highscore()
            running = self._wait_for_restart_or_quit()


def main() -> None:
    parser = argparse.ArgumentParser(description="Brick Breaker for ContourWallEmulator.")
    parser.add_argument(
        "--physical",
        action="store_true",
        help="Use webcam motion as physical paddle input.",
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
    cw = ContourWallEmulator()
    cw.new()

    motion_controller: PhysicalMotionController | None = None
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

    player_name = args.player_name.strip()
    game = BrickBreakerGame(
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
