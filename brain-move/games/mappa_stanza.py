import random
import time
from games.base_game import BaseGame


class MappaStanza(BaseGame):
    """Gioco 4: Abilita visuospaziali - ricorda e riposiziona oggetti nella stanza."""

    OBJECTS = {
        "sedia": "\U0001F6CB",
        "tavolo": "\U0001F4CB",
        "pianta": "\U0001F333",
        "finestra": "\U0001F5BC",
        "libro": "\U0001F4D6",
        "lampada": "\U0001F4A1",
    }

    def __init__(self, difficulty_engine, scoring_engine):
        super().__init__(difficulty_engine, scoring_engine)
        self.name = "mappa_stanza"
        self.display_name = "Mappa della Stanza"
        self.grid_size = 2
        self.num_objects = 3
        self.object_positions = {}
        self.user_positions = {}
        self.phase = "showing"
        self.show_timer = 0
        self.show_duration = 8.0
        self.selected_cell = None

    def start(self):
        super().start()
        level = self.difficulty.get_level()
        self.grid_size = 2 if level <= 2 else 3
        self.num_objects = min(3 + level, len(self.OBJECTS), self.grid_size * self.grid_size)

        all_objects = list(self.OBJECTS.keys())
        chosen = random.sample(all_objects, self.num_objects)

        positions = [(r, c) for r in range(self.grid_size) for c in range(self.grid_size)]
        random.shuffle(positions)

        self.object_positions = {}
        for i, obj in enumerate(chosen):
            self.object_positions[obj] = positions[i]

        self.user_positions = {}
        self.phase = "showing"
        self.show_timer = time.time()
        self.feedback_message = "Osserva la posizione degli oggetti"

    def update(self, pose_data=None, dt=0):
        if not self.running:
            return

        if self.phase == "showing":
            elapsed = time.time() - self.show_timer
            if elapsed >= self.show_duration:
                self.phase = "recall"
                self.feedback_message = "Posiziona gli oggetti nella posizione corretta"
        elif self.phase == "recall":
            pass

    def place_object(self, obj_name, row, col):
        if self.phase != "recall":
            return
        self.user_positions[obj_name] = (row, col)
        if len(self.user_positions) >= self.num_objects:
            self._check_answer()

    def select_cell_from_direction(self, direction):
        if self.phase != "recall":
            return
        if not hasattr(self, "_current_object_index"):
            self._current_object_index = 0

        objects_to_place = [o for o in self.object_positions if o not in self.user_positions]
        if not objects_to_place:
            return

        current_obj = objects_to_place[0]
        mapping = {
            "up": (0, self.grid_size // 2),
            "down": (self.grid_size - 1, self.grid_size // 2),
            "left": (self.grid_size // 2, 0),
            "right": (self.grid_size // 2, self.grid_size - 1),
        }
        if direction in mapping:
            self.place_object(current_obj, *mapping[direction])

    def _check_answer(self):
        correct = 0
        for obj, expected_pos in self.object_positions.items():
            if obj in self.user_positions and self.user_positions[obj] == expected_pos:
                correct += 1

        accuracy = correct / max(self.num_objects, 1)
        self.result = {
            "completed": True,
            "accuracy": accuracy,
            "correct": correct,
            "total": self.num_objects,
            "object_positions": {k: list(v) for k, v in self.object_positions.items()},
        }
        self.difficulty.adapt(accuracy)
        self.scoring.add_score(self.name, int(accuracy * 50))
        self.stop()
        self.feedback_message = f"Hai trovato {correct} su {self.num_objects} oggetti!"

    def get_objects_to_place(self):
        return [o for o in self.object_positions if o not in self.user_positions]

    def get_progress(self):
        if self.phase == "showing":
            return min((time.time() - self.show_timer) / self.show_duration, 1.0) * 0.4
        placed = len(self.user_positions)
        return 0.4 + 0.6 * (placed / max(self.num_objects, 1))
