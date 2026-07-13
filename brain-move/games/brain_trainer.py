import random
import time
import math
from games.base_game import BaseGame


class BrainTrainer(BaseGame):
    def __init__(self, difficulty_engine, scoring_engine):
        super().__init__(difficulty_engine, scoring_engine)
        self.name = "brain_trainer"
        self.display_name = "Brain Trainer"
        self.phase = "instruction"
        self.round = 0
        self.total_rounds = 10
        self.sub_game = "math"
        self.correct_count = 0
        self.total_answered = 0
        self.current_question = {}
        self.streak = 0
        self.instruction_timer = 0
        self.next_timer = 0
        self.show_result = ""
        self.show_result_timer = 0
        self.SUB_GAMES = ["math", "recall", "count"]
        self.recall_items = []
        self.recall_answer = ""
        self.count_grid = []
        self.count_target = 0

    def start(self):
        super().start()
        self.phase = "instruction"
        self.round = 0
        self.correct_count = 0
        self.total_answered = 0
        self.streak = 0
        self.instruction_timer = time.time()
        self.feedback_message = "Brain Trainer: rispondi alle domande!"

    def update(self, pose_data=None, dt=0):
        if not self.running:
            return
        if self.phase == "instruction":
            if time.time() - self.instruction_timer > 2.5:
                self._next_round()
            return
        if self.phase == "result":
            self.show_result_timer -= dt
            if self.show_result_timer <= 0:
                self._next_round()

    def _next_round(self):
        if self.round >= self.total_rounds:
            self._finish_game()
            return
        self.round += 1
        self.show_result = ""
        self.phase = "playing"
        self.sub_game = random.choice(self.SUB_GAMES)
        if self.sub_game == "math":
            self._gen_math()
        elif self.sub_game == "recall":
            self._gen_recall()
        else:
            self._gen_count()

    def _gen_math(self):
        level = self.difficulty.get_level()
        max_num = 5 + level * 2
        a = random.randint(1, max_num)
        b = random.randint(1, max_num)
        op = random.choice(["+", "-"])
        if op == "-" and a < b:
            a, b = b, a
        answer = a + b if op == "+" else a - b
        wrongs = set()
        while len(wrongs) < 3:
            w = answer + random.randint(-3, 3)
            if w != answer and w >= 0:
                wrongs.add(w)
        options = [answer] + list(wrongs)
        random.shuffle(options)
        self.current_question = {
            "type": "math",
            "text": f"{a} {op} {b} = ?",
            "options": options,
            "answer": answer,
        }
        self.feedback_message = f"Round {self.round}/{self.total_rounds}: {a} {op} {b} = ?"

    def _gen_recall(self):
        level = self.difficulty.get_level()
        items = ["\U0001F34E", "\U0001F431", "\U0001F697", "\U0001F3E0",
                 "\U0001F31E", "\U0001F436", "\U0001F33C", "\u2B50",
                 "\U0001F30A", "\U0001F308", "\U0001F422", "\U0001F426"]
        count = min(3 + level, 6)
        self.recall_items = random.sample(items, count)
        self.recall_answer = random.choice(self.recall_items)
        self.current_question = {
            "type": "recall",
            "text": "Ricorda l'immagine cerchiata!",
            "items": self.recall_items,
            "highlight": self.recall_answer,
            "options": self.recall_items[:],
            "answer": self.recall_answer,
        }
        random.shuffle(self.current_question["options"])
        self.feedback_message = f"Round {self.round}: ricorda e scegli l'immagine giusta"

    def _gen_count(self):
        level = self.difficulty.get_level()
        count = 3 + level
        self.count_target = random.randint(3, count + 2)
        symbols = ["\U0001F535", "\U0001F7E2", "\U0001F534", "\U0001F7E1"]
        s = random.choice(symbols)
        self.count_grid = [s] * self.count_target
        options = [self.count_target]
        for _ in range(3):
            w = self.count_target + random.randint(-3, 3)
            if w > 0 and w not in options:
                options.append(w)
        options = options[:4]
        random.shuffle(options)
        self.current_question = {
            "type": "count",
            "text": "Quanti simboli ci sono?",
            "symbols": self.count_grid,
            "symbol_char": s,
            "options": options,
            "answer": self.count_target,
        }
        self.feedback_message = f"Round {self.round}: conta i simboli!"

    def answer(self, value):
        if self.phase != "playing":
            return
        q = self.current_question
        correct = (value == q["answer"])
        self.total_answered += 1
        if correct:
            self.correct_count += 1
            self.streak += 1
            self.show_result = "Corretto! +25 punti"
            self.scoring.add_score(self.name, 25)
        else:
            self.streak = 0
            self.show_result = f"Sbagliato! Era {q['answer']}"
        self.phase = "result"
        self.show_result_timer = 2.0

    def _finish_game(self):
        self.stop()
        accuracy = self.correct_count / max(self.total_answered, 1)
        self.result = {
            "completed": True,
            "accuracy": accuracy,
            "correct": self.correct_count,
            "total": self.total_answered,
            "streak": self.streak,
        }
        self.difficulty.adapt(accuracy)
        self.scoring.add_score(self.name, int(accuracy * 30))

    def get_progress(self):
        return self.round / max(self.total_rounds, 1)

    def get_question_options(self):
        return self.current_question.get("options", [])
