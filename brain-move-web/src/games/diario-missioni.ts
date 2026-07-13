import { BaseGame } from './base-game'
import { Difficulty } from '../engine/difficulty'
import { Scoring } from '../engine/scoring'

const QUESTIONS = [
  "Quale gioco ti è piaciuto di più oggi?",
  "Ti senti calmo, normale o stanco?",
  "Vuoi rifare lo stesso percorso domani?",
]

const CAREGIVER_NOTES = [
  "attenzione_buona", "affaticamento", "umore_positivo",
  "bisogno_di_pausa", "difficolta_memoria", "difficolta_movimento",
]

const CAREGIVER_LABELS: Record<string, string> = {
  attenzione_buona: "Attenzione buona",
  affaticamento: "Affaticamento",
  umore_positivo: "Umore positivo",
  bisogno_di_pausa: "Bisogno di pausa",
  difficolta_memoria: "Difficoltà memoria",
  difficolta_movimento: "Difficoltà movimento",
}

export class DiarioMissioni extends BaseGame {
  currentQuestion = 0
  answers: string[] = []
  caregiverNotes: string[] = []
  phase: "questions" | "caregiver" = "questions"

  constructor(difficulty: Difficulty, scoring: Scoring) {
    super(difficulty, scoring)
    this.name = "diario_missioni"
    this.displayName = "Diario delle Missioni"
  }

  start(): void {
    super.start()
    this.currentQuestion = 0
    this.answers = []
    this.caregiverNotes = []
    this.phase = "questions"
    this.feedbackMessage = QUESTIONS[0]
  }

  update(_poseData?: any, _dt?: number): void {}

  answerQuestion(answer: string): void {
    if (this.phase !== "questions") return
    this.answers.push(answer)
    this.currentQuestion++
    if (this.currentQuestion >= QUESTIONS.length) {
      this.phase = "caregiver"
      this.feedbackMessage = "Caregiver: seleziona le osservazioni"
    } else {
      this.feedbackMessage = QUESTIONS[this.currentQuestion]
    }
  }

  addCaregiverNote(note: string): void {
    if (CAREGIVER_NOTES.includes(note) && !this.caregiverNotes.includes(note))
      this.caregiverNotes.push(note)
  }

  removeCaregiverNote(note: string): void {
    this.caregiverNotes = this.caregiverNotes.filter(n => n !== note)
  }

  complete(): void {
    this.result = { completed: true, accuracy: 1, answers: this.answers, caregiverNotes: this.caregiverNotes }
    this.scoring.addScore(this.name, 10)
    this.stop()
    this.feedbackMessage = "Sessione completata, ottimo lavoro!"
  }

  getCurrentQuestion(): string | null {
    return this.phase === "questions" && this.currentQuestion < QUESTIONS.length ? QUESTIONS[this.currentQuestion] : null
  }

  getCaregiverOptions(): string[] { return CAREGIVER_NOTES }
  getCaregiverLabel(note: string): string { return CAREGIVER_LABELS[note] ?? note }

  getProgress(): number {
    if (this.phase === "questions") return this.currentQuestion / Math.max(QUESTIONS.length, 1) * 0.7
    return 0.7 + 0.3 * Math.min(this.caregiverNotes.length / 3, 1)
  }
}
