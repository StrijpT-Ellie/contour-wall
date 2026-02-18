from __future__ import annotations

import sys
from dataclasses import dataclass

import cv2 as cv
import numpy as np

# Canonical arrow key values used by existing demos.
LEFT_KEY = 81
UP_KEY = 82
RIGHT_KEY = 83
DOWN_KEY = 84

LEFT_KEYS = {81}
RIGHT_KEYS = {83}
UP_KEYS = {82}
DOWN_KEYS = {84}

# Raw codes observed across OpenCV backends/platforms.
_LEFT_RAW = {LEFT_KEY, 2424832, 65361, 63234}
_UP_RAW = {UP_KEY, 2490368, 65362, 63232}
_RIGHT_RAW = {RIGHT_KEY, 2555904, 65363, 63235}
_DOWN_RAW = {DOWN_KEY, 2621440, 65364, 63233}


def normalize_key(key: int) -> int:
    if key is None:
        return -1
    key = int(key)
    if key < 0:
        return -1

    if key in _LEFT_RAW:
        return LEFT_KEY
    if key in _UP_RAW:
        return UP_KEY
    if key in _RIGHT_RAW:
        return RIGHT_KEY
    if key in _DOWN_RAW:
        return DOWN_KEY

    # Printable and simple keys (letters, space, ESC, etc.).
    if 0 <= key <= 255:
        return key

    # Some backends encode keys in high bits; preserve low byte if available.
    low = key & 0xFF
    if low != 0:
        return low

    return -1


@dataclass
class PhysicalMotionController:
    camera_index: int = 0
    show_window: bool = False
    lock_target: bool = True

    def __post_init__(self) -> None:
        if sys.platform.startswith("win"):
            self.cap = cv.VideoCapture(self.camera_index, cv.CAP_DSHOW)
        else:
            self.cap = cv.VideoCapture(self.camera_index)
        if not self.cap.isOpened():
            raise RuntimeError("Camera failed to open.")
        self.use_cuda = bool(getattr(cv, "cuda", None)) and cv.cuda.getCudaEnabledDeviceCount() > 0
        self.gpu_frame = cv.cuda_GpuMat() if self.use_cuda else None
        # Reduce capture latency where backend supports it.
        self.cap.set(cv.CAP_PROP_BUFFERSIZE, 1)
        self.cap.set(cv.CAP_PROP_FPS, 30)
        self.cap.set(cv.CAP_PROP_FRAME_WIDTH, 640)
        self.cap.set(cv.CAP_PROP_FRAME_HEIGHT, 480)
        self.prev_gray: np.ndarray | None = None
        self.last_key = -1
        self.last_target_col: int | None = None
        self.last_target_age = 0
        self.max_target_age = 12
        self.use_fast_capture = True
        self.capture_failures = 0
        self.min_contour_area = 380.0
        self.lock_cx: float | None = None
        self.lock_cy: float | None = None
        self.lock_area: float | None = None
        self.lock_bbox: tuple[float, float, float, float] | None = None
        self.lock_misses = 0
        self.max_lock_misses = 30
        self.reacquire_after_misses = 12

    def read_key(self) -> int:
        if self.show_window:
            return normalize_key(cv.waitKeyEx(1))
        return -1

    def _reset_lock(self) -> None:
        self.lock_cx = None
        self.lock_cy = None
        self.lock_area = None
        self.lock_bbox = None
        self.lock_misses = 0

    def _extract_candidates(
        self, contours: list[np.ndarray], frame_h: int
    ) -> list[tuple[float, float, float, np.ndarray, tuple[int, int, int, int]]]:
        candidates: list[tuple[float, float, float, np.ndarray, tuple[int, int, int, int]]] = []
        for contour in contours:
            area = float(cv.contourArea(contour))
            if area < self.min_contour_area:
                continue
            moments = cv.moments(contour)
            if moments["m00"] == 0:
                continue
            cx = float(moments["m10"] / moments["m00"])
            cy = float(moments["m01"] / moments["m00"])
            # Background movement often appears in upper image regions.
            if cy < frame_h * 0.10:
                continue
            x, y, w, h = cv.boundingRect(contour)
            candidates.append((cx, cy, area, contour, (x, y, w, h)))
        return candidates

    @staticmethod
    def _bbox_iou(
        a: tuple[float, float, float, float], b: tuple[float, float, float, float]
    ) -> float:
        ax, ay, aw, ah = a
        bx, by, bw, bh = b
        a_x2 = ax + aw
        a_y2 = ay + ah
        b_x2 = bx + bw
        b_y2 = by + bh

        ix1 = max(ax, bx)
        iy1 = max(ay, by)
        ix2 = min(a_x2, b_x2)
        iy2 = min(a_y2, b_y2)
        iw = max(0.0, ix2 - ix1)
        ih = max(0.0, iy2 - iy1)
        inter = iw * ih
        if inter <= 0:
            return 0.0
        union = (aw * ah) + (bw * bh) - inter
        if union <= 0:
            return 0.0
        return inter / union

    def _select_initial_candidate(
        self,
        candidates: list[tuple[float, float, float, np.ndarray, tuple[int, int, int, int]]],
        frame_w: int,
        frame_h: int,
    ) -> tuple[float, float, float, np.ndarray, tuple[int, int, int, int]]:
        cx_center = frame_w * 0.5

        def score(item: tuple[float, float, float, np.ndarray, tuple[int, int, int, int]]) -> float:
            cx, cy, area = item[0], item[1], item[2]
            center_penalty = abs(cx - cx_center) * 2.2
            lower_bonus = (cy / max(1.0, frame_h)) * 300.0
            return (area * 1.3) + lower_bonus - center_penalty

        return max(candidates, key=score)

    def _select_locked_candidate(
        self,
        candidates: list[tuple[float, float, float, np.ndarray, tuple[int, int, int, int]]],
        frame_w: int,
        frame_h: int,
    ) -> tuple[float, float, float, np.ndarray, tuple[int, int, int, int]] | None:
        if not candidates:
            return None

        # No lock yet: choose a central/foreground dominant candidate.
        if (
            not self.lock_target
            or self.lock_cx is None
            or self.lock_area is None
            or self.lock_bbox is None
        ):
            return self._select_initial_candidate(candidates, frame_w, frame_h)

        miss_factor = min(1.0, self.lock_misses / max(1, self.reacquire_after_misses))
        max_dist = max(60.0, frame_w * (0.18 + (0.10 * miss_factor)))
        min_iou_gate = 0.08 - (0.03 * miss_factor)
        min_area_ratio = max(0.35, 0.50 - (0.10 * miss_factor))
        max_area_ratio = 1.8 + (0.8 * miss_factor)
        best: tuple[float, float, float, np.ndarray, tuple[int, int, int, int]] | None = None
        best_score = 1e9

        for cx, cy, area, contour, bbox in candidates:
            dx = cx - self.lock_cx
            dy = cy - (self.lock_cy if self.lock_cy is not None else cy)
            dist = float(np.hypot(dx, dy))
            iou = self._bbox_iou(
                self.lock_bbox,
                (float(bbox[0]), float(bbox[1]), float(bbox[2]), float(bbox[3])),
            )
            if dist > max_dist and iou < min_iou_gate:
                continue

            area_ratio = area / max(self.lock_area, 1.0)
            if area_ratio < min_area_ratio or area_ratio > max_area_ratio:
                continue

            # Prioritize overlap and spatial consistency over raw area.
            area_delta = abs(np.log(max(area_ratio, 1e-6)))
            score = dist + (46.0 * area_delta) - (220.0 * iou)
            if score < best_score:
                best_score = score
                best = (cx, cy, area, contour, bbox)

        # Avoid sudden lock jumps to another person, but relax when lock is stale.
        score_limit = max(90.0, frame_w * (0.16 + (0.08 * miss_factor)))
        if best is not None and best_score > score_limit:
            return None

        # If lock is stale for several frames, allow controlled reacquire.
        if best is None and self.lock_misses >= self.reacquire_after_misses:
            return self._select_initial_candidate(candidates, frame_w, frame_h)

        return best

    def _update_lock(self, cx: float, cy: float, area: float, bbox: tuple[int, int, int, int]) -> None:
        if not self.lock_target:
            return
        if self.lock_cx is None or self.lock_area is None:
            self.lock_cx = cx
            self.lock_cy = cy
            self.lock_area = area
            self.lock_bbox = (float(bbox[0]), float(bbox[1]), float(bbox[2]), float(bbox[3]))
        else:
            self.lock_cx = (0.35 * self.lock_cx) + (0.65 * cx)
            self.lock_cy = (0.35 * (self.lock_cy if self.lock_cy is not None else cy)) + (
                0.65 * cy
            )
            self.lock_area = (0.45 * self.lock_area) + (0.55 * area)
            if self.lock_bbox is not None:
                self.lock_bbox = (
                    (0.35 * self.lock_bbox[0]) + (0.65 * bbox[0]),
                    (0.35 * self.lock_bbox[1]) + (0.65 * bbox[1]),
                    (0.35 * self.lock_bbox[2]) + (0.65 * bbox[2]),
                    (0.35 * self.lock_bbox[3]) + (0.65 * bbox[3]),
                )
            else:
                self.lock_bbox = (float(bbox[0]), float(bbox[1]), float(bbox[2]), float(bbox[3]))
        self.lock_misses = 0

    def _stable_target(self, target: int | None) -> int | None:
        if target is None:
            if self.last_target_col is None:
                return None
            if self.last_target_age < self.max_target_age:
                self.last_target_age += 1
                return self.last_target_col
            return None

        if self.last_target_col is None:
            self.last_target_col = target
        else:
            # Light smoothing to reduce jitter while staying responsive.
            self.last_target_col = int(round((0.35 * self.last_target_col) + (0.65 * target)))
        self.last_target_age = 0
        return self.last_target_col

    def read_target_col(self, cols: int) -> int | None:
        ret = False
        frame = None

        # Fast path: skip queued frames to reduce end-to-end camera latency.
        if self.use_fast_capture:
            self.cap.grab()
            self.cap.grab()
            ret, frame = self.cap.retrieve()

        # Robust fallback: standard read for backends where retrieve is unreliable.
        if not ret:
            ret, frame = self.cap.read()
        if not ret:
            self.capture_failures += 1
            if self.capture_failures >= 6:
                self.use_fast_capture = False
            return self._stable_target(None)
        self.capture_failures = 0
        if self.use_cuda:
            self.gpu_frame.upload(frame)
            gpu_flipped = cv.cuda.flip(self.gpu_frame, 1)
            frame = gpu_flipped.download()
            gpu_gray = cv.cuda.cvtColor(gpu_flipped, cv.COLOR_BGR2GRAY)
            gpu_gray = cv.cuda.GaussianBlur(gpu_gray, (5, 5), 0)
            gray = gpu_gray.download()
        else:
            frame = cv.flip(frame, 1)
            gray = cv.cvtColor(frame, cv.COLOR_BGR2GRAY)
            gray = cv.GaussianBlur(gray, (5, 5), 0)

        if self.prev_gray is None:
            self.prev_gray = gray
            if self.show_window:
                cv.imshow("Motion", frame)
            return self._stable_target(None)

        diff = cv.absdiff(self.prev_gray, gray)
        _, thresh = cv.threshold(diff, 18, 255, cv.THRESH_BINARY)
        thresh = cv.morphologyEx(thresh, cv.MORPH_OPEN, np.ones((3, 3), np.uint8), iterations=1)
        thresh = cv.dilate(thresh, None, iterations=1)
        self.prev_gray = gray

        contours, _ = cv.findContours(thresh, cv.RETR_EXTERNAL, cv.CHAIN_APPROX_SIMPLE)
        if not contours:
            self.lock_misses += 1
            if self.lock_misses > self.max_lock_misses:
                self._reset_lock()
            if self.show_window:
                cv.imshow("Motion", frame)
            return self._stable_target(None)

        candidates = self._extract_candidates(contours, frame.shape[0])
        if not candidates:
            self.lock_misses += 1
            if self.lock_misses > self.max_lock_misses:
                self._reset_lock()
            if self.show_window:
                cv.imshow("Motion", frame)
            return self._stable_target(None)

        selected = self._select_locked_candidate(candidates, frame.shape[1], frame.shape[0])
        if selected is None:
            self.lock_misses += 1
            if self.lock_misses > self.max_lock_misses:
                self._reset_lock()
            if self.show_window:
                cv.imshow("Motion", frame)
            return self._stable_target(None)

        cx, cy, area, contour, bbox = selected
        self._update_lock(cx, cy, area, bbox)
        target = int(np.clip(round(cx / max(1, frame.shape[1] - 1) * (cols - 1)), 0, cols - 1))
        target = self._stable_target(target)
        if self.show_window:
            x, y, w, h = bbox
            cv.rectangle(frame, (x, y), (x + w, y + h), (0, 210, 255), 2)
            cv.circle(frame, (int(cx), int(cy)), 10, (0, 255, 255), 2)
            if self.lock_target and self.lock_cx is not None and self.lock_cy is not None:
                cv.circle(frame, (int(self.lock_cx), int(self.lock_cy)), 5, (0, 180, 0), -1)
                cv.putText(
                    frame,
                    "LOCK",
                    (10, 28),
                    cv.FONT_HERSHEY_SIMPLEX,
                    0.8,
                    (0, 190, 0),
                    2,
                    cv.LINE_AA,
                )
            lane_w = frame.shape[1] // 3
            cv.line(frame, (lane_w, 0), (lane_w, frame.shape[0]), (100, 100, 100), 1)
            cv.line(frame, (lane_w * 2, 0), (lane_w * 2, frame.shape[0]), (100, 100, 100), 1)
            cv.imshow("Motion", frame)
        return target

    def close(self) -> None:
        if self.cap is not None:
            self.cap.release()
        if self.show_window:
            cv.destroyAllWindows()
