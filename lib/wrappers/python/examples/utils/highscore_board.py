from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import sys
import xml.etree.ElementTree as ET


@dataclass
class HighscoreEntry:
    name: str
    score: int
    is_current: bool
    rank: int


def highscore_path(base_dir: Path, game_name: str) -> Path:
    safe_name = "".join(ch for ch in game_name if ch.isalnum() or ch in ("-", "_"))
    safe_name = safe_name.strip("-_") or "game"
    return base_dir / f"highscores_{safe_name}.xml"


class HighscoreBoard:
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

    def __init__(self, rows: int, cols: int, pixels) -> None:
        self.rows = rows
        self.cols = cols
        self.pixels = pixels

    def load(self, path: Path) -> list[tuple[str, int]]:
        if not path.exists():
            return []
        try:
            tree = ET.parse(path)
            root = tree.getroot()
        except (ET.ParseError, OSError):
            return []

        scores: list[tuple[str, int]] = []
        for entry in root.findall("score"):
            name = entry.get("name", "")
            value = entry.get("value", "0")
            try:
                score = int(value)
            except ValueError:
                continue
            name = name.strip() or "AAA"
            scores.append((self.normalize_initials(name), score))

        scores.sort(key=lambda item: item[1], reverse=True)
        return scores[:10]

    def save(self, path: Path, highscores: list[tuple[str, int]]) -> None:
        root = ET.Element("highscores")
        for name, score in highscores[:10]:
            entry = ET.SubElement(root, "score")
            entry.set("name", name)
            entry.set("value", str(score))
        tree = ET.ElementTree(root)
        try:
            tree.write(path, encoding="utf-8", xml_declaration=True)
        except OSError:
            pass

    def record(
        self,
        highscores: list[tuple[str, int]],
        score: int,
        last_initials: str,
        path: Path | None = None,
    ) -> tuple[str, list[tuple[str, int]]]:
        if not sys.stdin or not sys.stdin.isatty():
            return "YOU", highscores
        try:
            name = input("Enter your name for the high score list (blank to skip): ").strip()
        except (EOFError, KeyboardInterrupt):
            return "YOU", highscores
        if not name:
            return "YOU", highscores
        initials = self.normalize_initials(name)
        highscores.append((initials, score))
        highscores.sort(key=lambda item: item[1], reverse=True)
        highscores = highscores[:10]
        if path is not None:
            self.save(path, highscores)
        return initials, highscores

    def record_and_save(
        self,
        highscores: list[tuple[str, int]],
        score: int,
        last_initials: str,
        path: Path,
        allow_prompt: bool = True,
    ) -> tuple[str, list[tuple[str, int]]]:
        recorded = False
        if score > 0:
            if allow_prompt and sys.stdin and sys.stdin.isatty():
                previous = list(highscores)
                last_initials, highscores = self.record(
                    highscores,
                    score,
                    last_initials,
                    path=None,
                )
                recorded = highscores != previous

            if not recorded:
                initials = self.normalize_initials(last_initials)
                if not any(name == initials and value == score for name, value in highscores):
                    highscores.append((initials, score))
                    highscores.sort(key=lambda item: item[1], reverse=True)
                    highscores = highscores[:10]

        path.parent.mkdir(parents=True, exist_ok=True)
        self.save(path, highscores)
        return last_initials, highscores

    @staticmethod
    def normalize_initials(name: str) -> str:
        cleaned = "".join(ch for ch in name if ch.isalnum()).upper()
        return (cleaned[:3] if cleaned else "AAA").ljust(3, "_")

    @staticmethod
    def build_display_highscores(
        highscores: list[tuple[str, int]],
        last_initials: str,
        score: int,
    ) -> list[HighscoreEntry]:
        current_entry = (last_initials, score, True)
        entries = [(name, value, False) for name, value in highscores]
        current_pos = -1
        for idx, (name, value, _) in enumerate(entries):
            if name == last_initials and value == score:
                entries[idx] = (name, value, True)
                current_pos = idx
                break
        if current_pos == -1:
            entries.append((last_initials, score, True))
            current_pos = len(entries) - 1

        ranked = sorted(entries, key=lambda item: item[1], reverse=True)
        for idx, entry in enumerate(ranked):
            if entry[2]:
                current_pos = idx
                break

        if current_pos < 3:
            display = ranked[:3]
        else:
            display = ranked[:3] + [ranked[current_pos]]

        display_with_rank: list[HighscoreEntry] = []
        for idx, (name, value, is_current) in enumerate(display):
            rank = next(
                (
                    pos + 1
                    for pos, entry in enumerate(ranked)
                    if entry == (name, value, is_current)
                ),
                idx + 1,
            )
            display_with_rank.append(
                HighscoreEntry(name=name, score=value, is_current=is_current, rank=rank)
            )
        return display_with_rank

    def draw(
        self,
        highscores: list[tuple[str, int]],
        last_initials: str,
        score: int,
        flash: bool,
    ) -> None:
        if not highscores and score <= 0:
            return

        max_rows = (self.rows - 2) // 6
        display_count = max(1, min(4, max_rows, 4))
        start_row = 2
        display_entries = self.build_display_highscores(highscores, last_initials, score)
        for idx, entry in enumerate(display_entries[:display_count]):
            if entry.is_current and flash:
                name_color = (255, 220, 120)
                score_color = (255, 220, 120)
            elif entry.is_current:
                name_color = (80, 140, 250)
                score_color = (80, 140, 250)
            else:
                name_color = (140, 210, 255)
                score_color = (200, 200, 200)

            row = start_row + idx * 6

            digit_w = 3
            glyph_gap = 1
            rank_text = str(entry.rank)
            rank_width = len(rank_text) * digit_w + (len(rank_text) - 1) * glyph_gap
            name_width = len(entry.name) * digit_w + (len(entry.name) - 1) * glyph_gap
            score_text = str(max(0, entry.score))
            score_width = len(score_text) * digit_w + (len(score_text) - 1) * glyph_gap

            rank_name_gap = 3
            name_score_gap = 4
            total_width = rank_width + rank_name_gap + name_width + name_score_gap + score_width
            start_left = max(0, (self.cols - total_width) // 2)

            rank_right_col = min(self.cols - 1, start_left + rank_width - 1)
            self.draw_number(
                value=entry.rank,
                top_row=row,
                right_col=rank_right_col,
                color=name_color,
            )

            name_left = rank_right_col + rank_name_gap + 1
            if name_left < self.cols:
                self.draw_text(
                    text=entry.name,
                    top_row=row,
                    left_col=name_left,
                    color=name_color,
                )

            score_left = name_left + name_width + name_score_gap
            score_right_col = min(self.cols - 1, score_left + score_width - 1)
            self.draw_number(
                value=entry.score,
                top_row=row,
                right_col=score_right_col,
                color=score_color,
            )

    def draw_number(
        self,
        value: int,
        top_row: int,
        right_col: int,
        color: tuple[int, int, int],
    ) -> None:
        if top_row < 0 or top_row + 5 > self.rows:
            return

        text = str(max(0, value))
        digit_w = 3
        gap = 1
        total_w = len(text) * digit_w + (len(text) - 1) * gap
        left_col = right_col - total_w + 1
        if left_col < 0:
            overflow = -left_col
            trim_digits = (overflow + digit_w + gap - 1) // (digit_w + gap)
            text = text[trim_digits:]
            total_w = len(text) * digit_w + (len(text) - 1) * gap
            left_col = right_col - total_w + 1
            if left_col < 0:
                return

        cursor = left_col
        for ch in text:
            pattern = self.DIGIT_PATTERNS.get(ch)
            if pattern is None:
                cursor += digit_w + gap
                continue
            for r, row in enumerate(pattern):
                for c, cell in enumerate(row):
                    if cell == "1":
                        self.pixels[top_row + r, cursor + c] = color
            cursor += digit_w + gap

    def draw_text(
        self,
        text: str,
        top_row: int,
        left_col: int,
        color: tuple[int, int, int],
    ) -> None:
        if top_row < 0 or top_row + 5 > self.rows:
            return
        if left_col >= self.cols:
            return

        digit_w = 3
        gap = 1
        cursor = left_col
        for ch in text.upper():
            if cursor + digit_w > self.cols:
                break
            pattern = self.CHAR_PATTERNS.get(ch)
            if pattern is None:
                cursor += digit_w + gap
                continue
            for r, row in enumerate(pattern):
                for c, cell in enumerate(row):
                    if cell == "1":
                        self.pixels[top_row + r, cursor + c] = color
            cursor += digit_w + gap
