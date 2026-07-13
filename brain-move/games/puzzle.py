import random
import time
import math
from games.base_game import BaseGame


class Puzzle(BaseGame):
    def __init__(self, difficulty_engine, scoring_engine):
        super().__init__(difficulty_engine, scoring_engine)
        self.name = "puzzle"
        self.display_name = "Puzzle"
        self.phase = "instruction"
        self.grid_size = 2
        self.EMOJI_POOL = [
            "\U0001F34E", "\U0001F34A", "\U0001F34B", "\U0001F347",
            "\U0001F349", "\U0001F353", "\U0001F33C", "\U0001F33B",
            "\U0001F33A", "\U0001F337", "\U0001F331", "\U0001F340",
            "\u2B50", "\U0001F535", "\U0001F7E2", "\U0001F534",
            "\U0001F7E1", "\U0001F7E3", "\U0001F7E0", "\U0001F7E4",
            "\U0001F31F", "\U0001F308", "\U0001F300", "\U0001F31E",
        ]
        self.target_grid = []
        self.current_grid = []
        self.selected_r = -1
        self.selected_c = -1
        self.correct_count = 0
        self.total_moves = 0
        self.hint_count = 0
        self.max_hints = 3
        self.instruction_timer = 0

    def start(self):
        super().start()
        level = self.difficulty.get_level()
        self.grid_size = min(2 + level, 6)
        self.max_hints = max(1, 4 - level)
        self.phase = "instruction"
        self.selected_r = -1
        self.selected_c = -1
        self.correct_count = 0
        self.total_moves = 0
        self.hint_count = 0
        self.instruction_timer = time.time()
        self.feedback_message = f"Puzzle {self.grid_size}x{self.grid_size}: scambia due tessere per ricreare l'immagine"

    def _generate_puzzle(self):
        self.target_grid = [[random.choice(self.EMOJI_POOL) for _ in range(self.grid_size)] for _ in range(self.grid_size)]
        flat = [self.target_grid[r][c] for r in range(self.grid_size) for c in range(self.grid_size)]
        random.shuffle(flat)
        self.current_grid = [flat[i * self.grid_size:(i + 1) * self.grid_size] for i in range(self.grid_size)]

    def update(self, pose_data=None, dt=0):
        if not self.running:
            return
        if self.phase == "instruction":
            if time.time() - self.instruction_timer > 2.0:
                self.phase = "playing"
                self._generate_puzzle()

    def select_piece(self, r, c):
        if self.phase != "playing":
            return
        if self.selected_r == -1:
            self.selected_r, self.selected_c = r, c
            self.feedback_message = f"Selezionato: riga {r+1}, colonna {c+1}. Scegli dove spostarlo"
        else:
            if self.selected_r == r and self.selected_c == c:
                self.selected_r = -1
                self.feedback_message = "Selezione annullata"
                return
            self._swap(self.selected_r, self.selected_c, r, c)
            self.selected_r = -1
            self.selected_c = -1

    def _swap(self, r1, c1, r2, c2):
        self.current_grid[r1][c1], self.current_grid[r2][c2] = self.current_grid[r2][c2], self.current_grid[r1][c1]
        self.total_moves += 1
        self._check_progress()

    def _check_progress(self):
        correct = 0
        for r in range(self.grid_size):
            for c in range(self.grid_size):
                if self.current_grid[r][c] == self.target_grid[r][c]:
                    correct += 1
        self.correct_count = correct
        total = self.grid_size * self.grid_size
        if correct == total:
            self.feedback_message = "Puzzle completato!"
            self._finish_game()
        else:
            self.feedback_message = f"{correct}/{total} tessere al posto giusto"

    def use_hint(self):
        if self.phase != "playing" or self.hint_count >= self.max_hints:
            return None
        for r in range(self.grid_size):
            for c in range(self.grid_size):
                if self.current_grid[r][c] != self.target_grid[r][c]:
                    self.hint_count += 1
                    self.feedback_message = f"Indizio: la tessera in ({r+1},{c+1}) e' sbagliata"
                    return (r, c)
        return None

    def _finish_game(self):
        self.stop()
        penalty = 1 - (self.hint_count / max(self.max_hints, 1)) * 0.15
        efficiency = max(0.3, 1 - self.total_moves / max(self.grid_size * self.grid_size * 3, 1))
        accuracy = (0.7 * efficiency + 0.3 * penalty)
        self.result = {
            "completed": True,
            "accuracy": accuracy,
            "correct": self.correct_count,
            "total_moves": self.total_moves,
            "grid_size": self.grid_size,
            "hints_used": self.hint_count,
        }
        self.difficulty.adapt(accuracy)
        self.scoring.add_score(self.name, int(accuracy * 30))

    def get_progress(self):
        total = self.grid_size * self.grid_size
        return self.correct_count / max(total, 1)

    def is_selected(self, r, c):
        return self.selected_r == r and self.selected_c == c
