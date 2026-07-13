import time
from games.base_game import BaseGame


class DiarioMissioni(BaseGame):
    """Gioco 6: Diario sessione - feedback finale e memorizzazione leggera."""

    QUESTIONS = [
        "Quale gioco ti e piaciuto di piu oggi?",
        "Ti senti calmo, normale o stanco?",
        "Vuoi rifare lo stesso percorso domani?",
    ]

    CAREGIVER_NOTES = [
        "attenzione_buona",
        "affaticamento",
        "umore_positivo",
        "bisogno_di_pausa",
        "difficolta_memoria",
        "difficolta_movimento",
    ]

    def __init__(self, difficulty_engine, scoring_engine):
        super().__init__(difficulty_engine, scoring_engine)
        self.name = "diario_missioni"
        self.display_name = "Diario delle Missioni"
        self.current_question = 0
        self.answers = []
        self.caregiver_notes = []
        self.phase = "questions"
        self.timer = 0

    def start(self):
        super().start()
        self.current_question = 0
        self.answers = []
        self.caregiver_notes = []
        self.phase = "questions"
        self.timer = time.time()
        self.feedback_message = self.QUESTIONS[0]

    def answer_question(self, answer):
        if self.phase != "questions":
            return
        self.answers.append(answer)
        self.current_question += 1
        if self.current_question >= len(self.QUESTIONS):
            self.phase = "caregiver"
            self.feedback_message = "Caregiver: seleziona le osservazioni"
        else:
            self.feedback_message = self.QUESTIONS[self.current_question]

    def add_caregiver_note(self, note):
        if note in self.CAREGIVER_NOTES:
            self.caregiver_notes.append(note)

    def complete(self):
        self.result = {
            "completed": True,
            "answers": dict(zip(self.QUESTIONS, self.answers)),
            "caregiver_notes": self.caregiver_notes,
        }
        self.scoring.add_score(self.name, 10)
        self.stop()
        self.feedback_message = "Sessione completata, ottimo lavoro!"

    def get_current_question(self):
        if self.phase == "questions" and self.current_question < len(self.QUESTIONS):
            return self.QUESTIONS[self.current_question]
        return None

    def get_caregiver_options(self):
        return self.CAREGIVER_NOTES

    def get_progress(self):
        if self.phase == "questions":
            return self.current_question / max(len(self.QUESTIONS), 1) * 0.7
        return 0.7 + 0.3 * min(len(self.caregiver_notes) / 3, 1.0)
