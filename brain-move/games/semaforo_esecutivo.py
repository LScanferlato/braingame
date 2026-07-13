import random
import time
from games.base_game import BaseGame


class SemaforoEsecutivo(BaseGame):
    """Gioco 3: Funzioni esecutive - segui le regole colore-movimento."""

    COLORS = {
        "verde": {"action": "passo_avanti", "display": "\U0001F7E2", "label": "Avanti"},
        "rosso": {"action": "fermo", "display": "\U0001F534", "label": "Fermo"},
        "blu": {"action": "passo_sinistra", "display": "\U0001F535", "label": "Sinistra"},
        "giallo": {"action": "passo_destra", "display": "\U0001F7E1", "label": "Destra"},
    }

    def __init__(self, difficulty_engine, scoring_engine):
        super().__init__(difficulty_engine, scoring_engine)
        self.name = "semaforo_esecutivo"
        self.display_name = "Semaforo Esecutivo"
        self.current_color = None
        self.current_command = None
        self.color_timer = 0
        self.color_interval = 4.0
        self.round_count = 0
        self.max_rounds = 10
        self.correct_count = 0
        self.inhibition_errors = 0
        self.waiting_for_response = False
        self.response_received = False
        self.inhibition_mode = False
        self.round_log = []

    def start(self):
        super().start()
        self.round_count = 0
        self.correct_count = 0
        self.inhibition_errors = 0
        self._next_round()
        self.feedback_message = "Segui il colore con il movimento giusto"

    def _next_round(self):
        if self.round_count >= self.max_rounds:
            self._finish_game()
            return

        level = self.difficulty.get_level()
        self.round_count += 1
        self.waiting_for_response = True
        self.response_received = False

        if level >= 3 and random.random() < 0.3:
            self.inhibition_mode = True
            self.current_color = random.choice(["verde", "rosso"])
            self.current_command = "fermo"
            self.feedback_message = "Attenzione: regola speciale! Resta fermo"
        else:
            self.inhibition_mode = False
            color = random.choice(list(self.COLORS.keys()))
            self.current_color = color
            self.current_command = self.COLORS[color]["action"]
            self.feedback_message = f"{self.COLORS[color]['display']} {self.COLORS[color]['label']}"

        self.color_timer = time.time()

    def update(self, pose_data=None, dt=0):
        if not self.running:
            return

        if self.waiting_for_response:
            elapsed = time.time() - self.color_timer
            if elapsed > self.color_interval:
                if not self.response_received:
                    self.inhibition_errors += 1
                    self.round_log.append({"round": self.round_count, "result": "timeout"})
                self._next_round()

    def validate_action(self, movement):
        if not self.waiting_for_response or self.response_received:
            return

        self.response_received = True

        if self.inhibition_mode:
            if movement == "center" or movement == "stationary":
                self.correct_count += 1
                self.round_log.append({"round": self.round_count, "result": "correct_inhibition"})
                self.feedback_message = "Ottimo controllo inibitorio!"
            else:
                self.inhibition_errors += 1
                self.round_log.append({"round": self.round_count, "result": "inhibition_error"})
                self.feedback_message = "Dovevi restare fermo, ma va bene"
        else:
            expected = self.current_command
            if (expected == "passo_avanti" and movement == "forward") or \
               (expected == "fermo" and movement in ("center", "stationary")) or \
               (expected == "passo_sinistra" and movement == "left") or \
               (expected == "passo_destra" and movement == "right"):
                self.correct_count += 1
                self.round_log.append({"round": self.round_count, "result": "correct"})
                self.feedback_message = "Perfetto!"
            else:
                self.round_log.append({"round": self.round_count, "result": "error"})
                self.feedback_message = "Prossimo round, riprova"

    def _finish_game(self):
        self.stop()
        total = self.correct_count + self.inhibition_errors
        accuracy = self.correct_count / max(total, 1)
        self.result = {
            "completed": True,
            "accuracy": accuracy,
            "correct": self.correct_count,
            "errors": self.inhibition_errors,
            "total_rounds": self.round_count,
        }
        self.difficulty.adapt(accuracy)
        self.scoring.add_score(self.name, int(accuracy * 50))

    def get_current_color(self):
        return self.current_color

    def get_color_display(self):
        if self.current_color and self.current_color in self.COLORS:
            return self.COLORS[self.current_color]
        return None

    def get_progress(self):
        return self.round_count / self.max_rounds
