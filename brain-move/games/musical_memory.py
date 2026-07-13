import random
import time
import math
import struct
from games.base_game import BaseGame


class MusicalMemory(BaseGame):
    COLORS = [
        (230, 60, 60),
        (60, 130, 230),
        (60, 200, 60),
        (230, 210, 50),
    ]
    FREQS = [262, 330, 392, 523]
    LABELS = ["Do", "Mi", "Sol", "Do'"]

    def __init__(self, difficulty_engine, scoring_engine):
        super().__init__(difficulty_engine, scoring_engine)
        self.name = "musical_memory"
        self.display_name = "Musical Memory"
        self.phase = "instruction"
        self.sequence = []
        self.user_input = []
        self.input_index = 0
        self.show_index = 0
        self.showing = False
        self.show_timer = 0
        self.flash_timer = 0
        self.flash_note = -1
        self.round = 0
        self.max_rounds = 10
        self.correct_rounds = 0
        self.instruction_timer = 0
        self.sounds = []
        self._init_sounds()

    def _init_sounds(self):
        for freq in self.FREQS:
            sound = self._make_tone(freq, 0.35)
            self.sounds.append(sound)

    def _make_tone(self, freq, duration):
        try:
            import pygame
            sample_rate = 22050
            num = int(sample_rate * duration)
            samples = []
            for i in range(num):
                t = i / sample_rate
                v = math.sin(2 * math.pi * freq * t)
                env = 1.0
                fade = int(sample_rate * 0.05)
                if i > num - fade:
                    env = (num - i) / fade
                v *= env * 0.25 * 32767
                samples.append(int(v))
            data = struct.pack("<" + "h" * num, *samples)
            return pygame.mixer.Sound(buffer=data)
        except Exception:
            return None

    def start(self):
        super().start()
        self.phase = "instruction"
        self.sequence = []
        self.round = 0
        self.correct_rounds = 0
        self.input_index = 0
        self.showing = False
        self.instruction_timer = time.time()
        self.feedback_message = "Ripeti la sequenza musicale!"

    def update(self, pose_data=None, dt=0):
        if not self.running:
            return

        if self.phase == "instruction":
            if time.time() - self.instruction_timer > 2.0:
                self._next_note()
            return

        if self.showing:
            self.show_timer -= dt
            self.flash_timer -= dt
            if self.flash_timer <= 0:
                self.flash_note = -1
            if self.show_timer <= 0:
                self.showing = False
                self.phase = "input"
                self.input_index = 0
                self.feedback_message = f"Ripeti! ({self.round}/{self.max_rounds})"

    def _next_note(self):
        self.round += 1
        self.sequence.append(random.randint(0, 3))
        self.showing = True
        self.show_index = 0
        self.show_timer = len(self.sequence) * 0.8
        self._flash_next()

    def _flash_next(self):
        if self.show_index < len(self.sequence):
            note = self.sequence[self.show_index]
            self.flash_note = note
            self.flash_timer = 0.6
            self._play_note(note)
            self.show_index += 1

    def _play_note(self, note_idx):
        if 0 <= note_idx < len(self.sounds) and self.sounds[note_idx]:
            try:
                self.sounds[note_idx].play()
            except Exception:
                pass

    def press_button(self, note_idx):
        if self.phase != "input":
            return
        self._play_note(note_idx)
        if note_idx == self.sequence[self.input_index]:
            self.input_index += 1
            if self.input_index >= len(self.sequence):
                self.correct_rounds += 1
                self.feedback_message = f"Corretto! {self.correct_rounds}/{self.round}"
                if self.round >= self.max_rounds:
                    self._finish_game()
                else:
                    self.phase = "result"
                    self.show_timer = 1.5
        else:
            self.feedback_message = f"Sbagliato! Era la sequenza corretta"
            self._finish_game()

    def _finish_game(self):
        self.stop()
        accuracy = self.correct_rounds / max(self.round, 1)
        self.result = {
            "completed": True,
            "accuracy": accuracy,
            "correct_rounds": self.correct_rounds,
            "total_rounds": self.round,
            "sequence_length": len(self.sequence),
        }
        self.difficulty.adapt(accuracy)
        self.scoring.add_score(self.name, int(accuracy * 30))

    def get_progress(self):
        return self.round / max(self.max_rounds, 1)

    def get_flash_note(self):
        return self.flash_note
