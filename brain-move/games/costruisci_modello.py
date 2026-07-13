import random
import time
from games.base_game import BaseGame


class CostruisciModello(BaseGame):
    """Gioco 5: Memoria di lavoro - ricorda e ricostruisci un modello."""

    SHAPES = {
        "cerchio_rosso": {"shape": "circle", "color": (220, 50, 50), "label": "Cerchio Rosso"},
        "quadrato_bl": {"shape": "rect", "color": (50, 50, 220), "label": "Quadrato Blu"},
        "triangolo_verde": {"shape": "triangle", "color": (50, 180, 50), "label": "Triangolo Verde"},
        "stella_gialla": {"shape": "star", "color": (220, 200, 50), "label": "Stella Gialla"},
        "diamante_arancio": {"shape": "diamond", "color": (220, 140, 50), "label": "Diamante Arancio"},
        "cuore_rosa": {"shape": "heart", "color": (220, 100, 150), "label": "Cuore Rosa"},
    }

    def __init__(self, difficulty_engine, scoring_engine):
        super().__init__(difficulty_engine, scoring_engine)
        self.name = "costruisci_modello"
        self.display_name = "Costruisci il Modello"
        self.model_pieces = []
        self.user_pieces = []
        self.phase = "showing"
        self.show_timer = 0
        self.show_duration = 15.0
        self.available_pieces = list(self.SHAPES.keys())

    def start(self):
        super().start()
        level = self.difficulty.get_level()
        num_pieces = min(3 + level, len(self.SHAPES))
        self.model_pieces = random.sample(self.available_pieces, num_pieces)
        self.user_pieces = []
        self.phase = "showing"
        self.show_timer = time.time()
        self.feedback_message = "Osserva il modello e ricordalo"

    def update(self, pose_data=None, dt=0):
        if not self.running:
            return

        if self.phase == "showing":
            elapsed = time.time() - self.show_timer
            if elapsed >= self.show_duration:
                self.phase = "building"
                self.feedback_message = "Ora ricostruisci il modello"
        elif self.phase == "building":
            pass

    def place_piece(self, piece_name):
        if self.phase != "building":
            return
        self.user_pieces.append(piece_name)
        if len(self.user_pieces) >= len(self.model_pieces):
            self._check_answer()

    def _check_answer(self):
        correct = sum(1 for u, m in zip(self.user_pieces, self.model_pieces) if u == m)
        accuracy = correct / max(len(self.model_pieces), 1)
        self.result = {
            "completed": True,
            "accuracy": accuracy,
            "correct": correct,
            "total": len(self.model_pieces),
            "model": self.model_pieces,
        }
        self.difficulty.adapt(accuracy)
        self.scoring.add_score(self.name, int(accuracy * 40))
        self.stop()
        self.feedback_message = f"Hai costruito {correct} su {len(self.model_pieces)} pezzi correttamente!"

    def get_model_preview(self):
        if self.phase == "showing":
            elapsed = time.time() - self.show_timer
            if elapsed < self.show_duration - 2:
                return self.model_pieces
        return []

    def get_available_pieces(self):
        return self.available_pieces

    def get_progress(self):
        if self.phase == "showing":
            return min((time.time() - self.show_timer) / self.show_duration, 1.0) * 0.4
        placed = len(self.user_pieces)
        return 0.4 + 0.6 * (placed / max(len(self.model_pieces), 1))
