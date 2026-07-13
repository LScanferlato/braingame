import random
import time
from games.base_game import BaseGame


class ParoleIncrociate(BaseGame):
    """Gioco cruciverba semplificato con parole incrociate."""

    WORDS = [
        {"word": "CASA", "hint": "Dove abiti"},
        {"word": "MARE", "hint": "Acqua salata e grande"},
        {"word": "SOLE", "hint": "Luce nel cielo di giorno"},
        {"word": "LUNA", "hint": "Brilla di notte"},
        {"word": "ALbero", "hint": "Ha rami e foglie"},
        {"word": "GATTO", "hint": "Fa miao"},
        {"word": "CANE", "hint": "Fa bau"},
        {"word": "FIore", "hint": "Colorato e profumato"},
        {"word": "ACQUA", "hint": "Si beve"},
        {"word": "PANE", "hint": "Si mangia a colazione"},
        {"word": "MELA", "hint": "Frutto rosso"},
        {"word": "LIBro", "hint": "Lo leggi"},
        {"word": "TAVOLO", "hint": "Dove mangi"},
        {"word": "SEDIA", "hint": "Dove ti siedi"},
        {"word": "PORTA", "hint": "Entri e esci da qui"},
        {"word": "FINESTRA", "hint": "Vedi fuori da qui"},
        {"word": "SCUOLA", "hint": "Dove impari"},
        {"word": "GIARDINO", "hint": "Hai fiori e erba"},
        {"word": "CUCINA", "hint": "Dai cucini"},
        {"word": "BAGNO", "hint": "Ti lavi qui"},
        {"word": "SOFFITTO", "hint": "E sopra di te"},
        {"word": "PARCO", "hint": "Passeggi qui"},
        {"word": "PESCE", "hint": "Vive nell'acqua"},
        {"word": "CAFFE", "hint": "Bevi la mattina"},
        {"word": "LATTEnA", "hint": "Fiorisce di notte"},
        {"word": "PRATO", "hint": "Erba verde"},
        {"word": "NUVOLA", "hint": "Vol nel cielo"},
        {"word": "STELLA", "hint": "Brilla di notte"},
        {"word": "PIAZZA", "hint": "Cuore del paese"},
        {"word": "CHIESE", "hint": "Dai preghi"},
    ]

    def __init__(self, difficulty_engine, scoring_engine):
        super().__init__(difficulty_engine, scoring_engine)
        self.name = "parole_incrociate"
        self.display_name = "Parole Incrociate"
        self.grid_size = 7
        self.grid = []
        self.solution = []
        self.placed_words = []
        self.current_word_index = 0
        self.user_input = []
        self.selected_cell = None
        self.direction = "across"
        self.correct_words = 0
        self.total_words = 0
        self.attempts = 0
        self.phase = "playing"
        self.hints_shown = True

    def start(self):
        super().start()
        level = self.difficulty.get_level()
        if level <= 2:
            self.grid_size = 6
            self.total_words = 3
        elif level <= 3:
            self.grid_size = 7
            self.total_words = 4
        else:
            self.grid_size = 8
            self.total_words = 5

        self.grid = [["" for _ in range(self.grid_size)] for _ in range(self.grid_size)]
        self.solution = [["" for _ in range(self.grid_size)] for _ in range(self.grid_size)]
        self.placed_words = []
        self.correct_words = 0
        self.attempts = 0
        self.phase = "playing"
        self.current_word_index = 0

        self._place_words()
        self.user_input = list(self.placed_words[0]["word"]) if self.placed_words else []
        self.selected_cell = 0
        self.feedback_message = "Incroci le parole! Clicca sulla casella e scrivi"

    def _place_words(self):
        words = random.sample(self.WORDS, min(self.total_words + 5, len(self.WORDS)))
        words.sort(key=lambda w: len(w["word"]), reverse=True)

        placed = []
        for word_data in words:
            word = word_data["word"].upper()
            if len(word) > self.grid_size:
                continue

            for attempt in range(20):
                direction = random.choice(["across", "down"])
                if direction == "across":
                    row = random.randint(0, self.grid_size - 1)
                    col = random.randint(0, self.grid_size - len(word))
                else:
                    row = random.randint(0, self.grid_size - len(word))
                    col = random.randint(0, self.grid_size - 1)

                if self._can_place(word, row, col, direction):
                    self._do_place(word, row, col, direction)
                    placed.append({
                        "word": word,
                        "hint": word_data["hint"],
                        "row": row,
                        "col": col,
                        "direction": direction,
                        "solved": False,
                    })
                    break

            if len(placed) >= self.total_words:
                break

        self.placed_words = placed
        self.total_words = len(placed)

    def _can_place(self, word, row, col, direction):
        for i, ch in enumerate(word):
            if direction == "across":
                r, c = row, col + i
            else:
                r, c = row + i, col

            if r >= self.grid_size or c >= self.grid_size:
                return False
            if self.solution[r][c] != "" and self.solution[r][c] != ch:
                return False
            if self.solution[r][c] == ch:
                continue

            for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                nr, nc = r + dr, c + dc
                if 0 <= nr < self.grid_size and 0 <= nc < self.grid_size:
                    if self.solution[nr][nc] != "":
                        return False
        return True

    def _do_place(self, word, row, col, direction):
        for i, ch in enumerate(word):
            if direction == "across":
                self.solution[row][col + i] = ch
            else:
                self.solution[row + i][col] = ch

    def update(self, pose_data=None, dt=0):
        if not self.running:
            return

    def set_cell_letter(self, letter):
        if self.phase != "playing" or not self.placed_words:
            return
        if self.current_word_index >= len(self.placed_words):
            return

        word_info = self.placed_words[self.current_word_index]
        if word_info["solved"]:
            return

        if self.selected_cell is not None and 0 <= self.selected_cell < len(self.user_input):
            self.user_input[self.selected_cell] = letter.upper()
            if self.selected_cell < len(self.user_input) - 1:
                self.selected_cell += 1

    def delete_letter(self):
        if self.phase != "playing" or not self.placed_words:
            return
        if self.selected_cell is not None and self.selected_cell > 0:
            self.user_input[self.selected_cell] = ""
            self.selected_cell -= 1

    def move_cursor(self, direction):
        if not self.placed_words:
            return
        word_info = self.placed_words[self.current_word_index]
        word_len = len(word_info["word"])
        if direction == "right":
            self.selected_cell = min((self.selected_cell or 0) + 1, word_len - 1)
        elif direction == "left":
            self.selected_cell = max((self.selected_cell or 0) - 1, 0)

    def select_cell(self, row, col):
        if self.phase != "playing":
            return
        for idx, wp in enumerate(self.placed_words):
            if wp["solved"]:
                continue
            if wp["direction"] == "across":
                if wp["row"] == row and wp["col"] <= col < wp["col"] + len(wp["word"]):
                    self.current_word_index = idx
                    self.user_input = list(" " * len(wp["word"]))
                    self.selected_cell = col - wp["col"]
                    self.feedback_message = wp["hint"]
                    return
            else:
                if wp["col"] == col and wp["row"] <= row < wp["row"] + len(wp["word"]):
                    self.current_word_index = idx
                    self.user_input = list(" " * len(wp["word"]))
                    self.selected_cell = row - wp["row"]
                    self.feedback_message = wp["hint"]
                    return

    def check_word(self):
        if self.phase != "playing" or not self.placed_words:
            return
        if self.current_word_index >= len(self.placed_words):
            return

        word_info = self.placed_words[self.current_word_index]
        if word_info["solved"]:
            return

        guess = "".join(self.user_input).strip().upper()
        self.attempts += 1

        if guess == word_info["word"]:
            word_info["solved"] = True
            self.correct_words += 1
            self.scoring.add_score(self.name, 20)
            self.feedback_message = f"Corretto! {word_info['word']}"

            r, c = word_info["row"], word_info["col"]
            for i, ch in enumerate(word_info["word"]):
                if word_info["direction"] == "across":
                    self.grid[r][c + i] = ch
                else:
                    self.grid[r + i][c] = ch

            self._next_word()
        else:
            self.feedback_message = "Non e corretto, riprova"

    def _next_word(self):
        for idx, wp in enumerate(self.placed_words):
            if not wp["solved"]:
                self.current_word_index = idx
                self.user_input = list(" " * len(wp["word"]))
                self.selected_cell = 0
                self.feedback_message = wp["hint"]
                return

        self._finish_game()

    def _finish_game(self):
        self.stop()
        accuracy = self.correct_words / max(self.total_words, 1)
        self.result = {
            "completed": True,
            "accuracy": accuracy,
            "correct": self.correct_words,
            "total": self.total_words,
            "attempts": self.attempts,
        }
        self.difficulty.adapt(accuracy)
        self.scoring.add_score(self.name, int(accuracy * 40))

    def get_current_word(self):
        if not self.placed_words or self.current_word_index >= len(self.placed_words):
            return None
        return self.placed_words[self.current_word_index]

    def get_current_word_display(self):
        word_info = self.get_current_word()
        if not word_info:
            return [], -1
        return self.user_input, self.selected_cell

    def get_grid(self):
        display = [row[:] for row in self.grid]
        word_info = self.get_current_word()
        if word_info and not word_info["solved"]:
            r, c = word_info["row"], word_info["col"]
            for i, ch in enumerate(self.user_input):
                if ch and ch.strip():
                    if word_info["direction"] == "across":
                        display[r][c + i] = ch
                    else:
                        display[r + i][c] = ch
        return display

    def get_hints(self):
        hints = []
        for i, wp in enumerate(self.placed_words):
            num = i + 1
            direction = " → " if wp["direction"] == "across" else " ↓ "
            solved_mark = " ✓" if wp["solved"] else ""
            hints.append(f"{num}. {wp['hint']}{direction}{wp['word']}{solved_mark}")
        return hints

    def get_progress(self):
        return self.correct_words / max(self.total_words, 1)
