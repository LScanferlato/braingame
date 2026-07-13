import time
import math
from games.base_game import BaseGame


class Basket(BaseGame):
    """Gioco basket: lancia la palla con mano destra e sinistra."""

    def __init__(self, difficulty_engine, scoring_engine):
        super().__init__(difficulty_engine, scoring_engine)
        self.name = "basket"
        self.display_name = "Basket"
        self.phase = "instruction"
        self.throw_hand = "right"
        self.right_thrown = False
        self.left_thrown = False
        self.correct_count = 0
        self.total_attempts = 0
        self.max_attempts = 4

        self.wrist_history_r = []
        self.wrist_history_l = []
        self.history_max = 15

        self.ball_pos = None
        self.ball_vel = None
        self.ball_trail = []
        self.ball_flying = False
        self.ball_start_time = 0
        self.ball_duration = 1.5

        self.hoop_x = 0.85
        self.hoop_y = 0.30
        self.hoop_radius = 40

        self.score_display = ""
        self.score_timer = 0
        self.instruction_timer = 0

    def start(self):
        super().start()
        self.phase = "instruction"
        self.throw_hand = "right"
        self.right_thrown = False
        self.left_thrown = False
        self.correct_count = 0
        self.total_attempts = 0
        self.wrist_history_r = []
        self.wrist_history_l = []
        self.ball_flying = False
        self.ball_trail = []
        self.score_display = ""
        self.score_timer = 0
        self.instruction_timer = time.time()
        self.feedback_message = "Lancia con la mano DESTRA! Alzala e lancia"

    def update(self, pose_data=None, dt=0):
        if not self.running:
            return

        if self.phase == "instruction":
            if time.time() - self.instruction_timer > 3.0:
                self.phase = "ready"
                self.feedback_message = self._hand_instruction()
            return

        if self.phase == "ready" and pose_data:
            self._track_wrist(pose_data)

        if self.ball_flying:
            elapsed = time.time() - self.ball_start_time
            t = elapsed / self.ball_duration
            if t >= 1.0:
                self._check_hoop()
            else:
                self._update_ball_physics(t)

        if self.score_timer > 0:
            self.score_timer -= dt
            if self.score_timer <= 0:
                self._next_throw()

    def _hand_instruction(self):
        if self.throw_hand == "right":
            return "Ora lancia con la MANO DESTRA!"
        return "Ora lancia con la MANO SINISTRA!"

    def _track_wrist(self, pose_data):
        if self.ball_flying:
            return

        if self.throw_hand == "right" and "r_wrist" in pose_data:
            wrist = pose_data["r_wrist"]
            self.wrist_history_r.append((wrist, time.time()))
            if len(self.wrist_history_r) > self.history_max:
                self.wrist_history_r.pop(0)
            self.ball_pos = wrist
            self._check_throw(self.wrist_history_r, "right")

        elif self.throw_hand == "left" and "l_wrist" in pose_data:
            wrist = pose_data["l_wrist"]
            self.wrist_history_l.append((wrist, time.time()))
            if len(self.wrist_history_l) > self.history_max:
                self.wrist_history_l.pop(0)
            self.ball_pos = wrist
            self._check_throw(self.wrist_history_l, "left")

    def _check_throw(self, history, hand):
        if len(history) < 5:
            return

        recent = history[-5:]
        positions = [p for p, t in recent]
        times = [t for p, t in recent]

        dt_total = times[-1] - times[0]
        if dt_total < 0.05:
            return

        dx = positions[-1][0] - positions[0][0]
        dy = positions[-1][1] - positions[0][1]
        speed = math.sqrt(dx * dx + dy * dy) / dt_total

        level = self.difficulty.get_level()
        throw_threshold = max(150, 300 - level * 30)

        if speed > throw_threshold and dy < -20:
            self._launch_ball(positions[-1], (dx / dt_total, dy / dt_total), hand)

    def _launch_ball(self, start_pos, velocity, hand):
        self.ball_flying = True
        self.ball_start_time = time.time()
        self.ball_pos = start_pos
        self.ball_vel = velocity
        self.ball_trail = [start_pos]
        self.total_attempts += 1
        self.feedback_message = "Lancio!"

    def _update_ball_physics(self, t):
        if self.ball_pos is None or self.ball_vel is None:
            return
        vx, vy = self.ball_vel
        gravity = 400
        px = self.ball_pos[0] + vx * t
        py = self.ball_pos[1] + vy * t + 0.5 * gravity * t * t
        self.ball_pos = (px, py)
        self.ball_trail.append((px, py))
        if len(self.ball_trail) > 30:
            self.ball_trail.pop(0)

    def _check_hoop(self):
        self.ball_flying = False
        if self.ball_pos is None:
            self._miss()
            return

        hoop_screen_x = self.hoop_x * 640
        hoop_screen_y = self.hoop_y * 480
        bx, by = self.ball_pos
        dist = math.sqrt((bx - hoop_screen_x) ** 2 + (by - hoop_screen_y) ** 2)

        if dist < self.hoop_radius * 2:
            self._score()
        else:
            self._miss()

    def _score(self):
        self.correct_count += 1
        hand_label = "destra" if self.throw_hand == "right" else "sinistra"
        self.score_display = f"CANESTRO! ({hand_label})"
        self.score_timer = 2.0
        self.scoring.add_score(self.name, 25)
        self.feedback_message = f"Canestro con la mano {hand_label}!"

        if self.throw_hand == "right":
            self.right_thrown = True
        else:
            self.left_thrown = True

    def _miss(self):
        hand_label = "destra" if self.throw_hand == "right" else "sinistra"
        self.score_display = f"Mancato ({hand_label})"
        self.score_timer = 2.0
        self.feedback_message = f"Mancato con la mano {hand_label}, riprova!"

        if self.throw_hand == "right":
            self.right_thrown = True
        else:
            self.left_thrown = True

    def _next_throw(self):
        self.score_display = ""
        self.ball_pos = None
        self.ball_vel = None
        self.ball_trail = []
        self.wrist_history_r = []
        self.wrist_history_l = []

        if not self.left_thrown:
            self.throw_hand = "left"
            self.feedback_message = "Ora lancia con la MANO SINISTRA!"
        elif not self.right_thrown:
            self.throw_hand = "right"
            self.feedback_message = "Ora lancia con la MANO DESTRA!"
        else:
            self._finish_game()

    def _finish_game(self):
        self.stop()
        accuracy = self.correct_count / max(self.total_attempts, 1)
        self.result = {
            "completed": True,
            "accuracy": accuracy,
            "correct": self.correct_count,
            "total_attempts": self.total_attempts,
            "right_thrown": self.right_thrown,
            "left_thrown": self.left_thrown,
        }
        self.difficulty.adapt(accuracy)
        self.scoring.add_score(self.name, int(accuracy * 30))

    def get_ball_pos(self):
        return self.ball_pos

    def get_ball_trail(self):
        return self.ball_trail

    def get_hoop_pos(self):
        return self.hoop_x, self.hoop_y, self.hoop_radius

    def get_progress(self):
        done = (1 if self.right_thrown else 0) + (1 if self.left_thrown else 0)
        return done / 2.0
