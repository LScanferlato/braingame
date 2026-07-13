import { BaseGame } from './base-game'
import { Difficulty } from '../engine/difficulty'
import { Scoring } from '../engine/scoring'
import type { QuestionData } from '../types'

const QUESTIONS: QuestionData[] = [
  { q: "Quale di questi non è un colore primario?", opts: ["Rosso", "Blu", "Verde", "Giallo"], ans: 2 },
  { q: "Quante zampe ha un cane?", opts: ["2", "4", "6", "8"], ans: 1 },
  { q: "In che stagione cadono le foglie?", opts: ["Primavera", "Estate", "Autunno", "Inverno"], ans: 2 },
  { q: "Cosa usiamo per misurare la temperatura?", opts: ["Bilancia", "Orologio", "Termometro", "Righello"], ans: 2 },
  { q: "Di che colore è il cielo sereno?", opts: ["Verde", "Rosso", "Blu", "Grigio"], ans: 2 },
  { q: "Cosa usiamo per scrivere?", opts: ["Forbici", "Penna", "Tazza", "Piatto"], ans: 1 },
  { q: "Quale animale vive al Polo Nord?", opts: ["Leone", "Orso polare", "Elefante", "Giraffa"], ans: 1 },
  { q: "Quante dita abbiamo in una mano?", opts: ["3", "4", "5", "6"], ans: 2 },
  { q: "Cosa si accende in un temporale?", opts: ["Lampo", "Neve", "Arcobaleno", "Stella"], ans: 0 },
  { q: "Primo pasto della giornata?", opts: ["Pranzo", "Cena", "Merenda", "Colazione"], ans: 3 },
  { q: "Che forma ha un pallone?", opts: ["Quadrato", "Triangolare", "Rotondo", "Stellato"], ans: 2 },
  { q: "Cosa fa il gatto felice?", opts: ["Abbaia", "Miaoala", "Fusa", "Ringhia"], ans: 2 },
  { q: "Dove vive il pesce?", opts: ["Terra", "Aria", "Acqua", "Fuoco"], ans: 2 },
  { q: "Mese dopo giugno?", opts: ["Maggio", "Luglio", "Agosto", "Settembre"], ans: 1 },
  { q: "Per tagliare il pane?", opts: ["Forchetta", "Cucchiaio", "Coltello", "Pentola"], ans: 2 },
  { q: "Animale che produce latte?", opts: ["Gallina", "Mucca", "Maiale", "Pecora"], ans: 1 },
  { q: "Foglie in estate?", opts: ["Gialle", "Marroni", "Verdi", "Rosse"], ans: 2 },
  { q: "Indossiamo ai piedi?", opts: ["Cappello", "Guanti", "Scarpe", "Sciarpa"], ans: 2 },
  { q: "Numero dopo 9?", opts: ["10", "8", "11", "7"], ans: 0 },
  { q: "Per vedere lontano?", opts: ["Occhiali", "Microscopio", "Binocolo", "Lente"], ans: 2 },
]

export class Quiz extends BaseGame {
  phase: "instruction" | "playing" = "instruction"
  questions: QuestionData[] = []
  currentQ = 0
  totalQ = 8
  correctCount = 0
  answered = 0
  selectedAnswer = -1
  showFeedback = false
  feedbackTimer = 0
  instructionTimer = 0

  constructor(difficulty: Difficulty, scoring: Scoring) {
    super(difficulty, scoring)
    this.name = "quiz"
    this.displayName = "Quiz"
  }

  start(): void {
    super.start()
    this.phase = "instruction"
    this.instructionTimer = Date.now()
    const level = this.difficulty.getLevel()
    this.totalQ = Math.min(6 + level, 12)
    this.questions = [...QUESTIONS].sort(() => Math.random() - 0.5).slice(0, this.totalQ)
    this.currentQ = 0
    this.correctCount = 0
    this.answered = 0
    this.selectedAnswer = -1
    this.showFeedback = false
    this.feedbackMessage = "Rispondi alle domande!"
  }

  update(_poseData?: any, dt = 0): void {
    if (!this.running) return
    if (this.phase === "instruction") {
      if ((Date.now() - this.instructionTimer) / 1000 > 2) { this.phase = "playing"; this._showQuestion() }
      return
    }
    if (this.showFeedback) {
      this.feedbackTimer -= dt
      if (this.feedbackTimer <= 0) {
        this.showFeedback = false
        this.selectedAnswer = -1
        this.currentQ++
        this.currentQ >= this.totalQ ? this._finishGame() : this._showQuestion()
      }
    }
  }

  private _showQuestion(): void {
    this.feedbackMessage = this.questions[this.currentQ].q
  }

  selectAnswer(idx: number): void {
    if (this.phase !== "playing" || this.showFeedback) return
    const q = this.questions[this.currentQ]
    this.selectedAnswer = idx
    this.showFeedback = true
    this.feedbackTimer = 2.0
    this.answered++
    if (idx === q.ans) {
      this.correctCount++
      this.scoring.addScore(this.name, 20)
      this.feedbackMessage = "Corretto! \u{1F44D}"
    } else {
      this.feedbackMessage = `No! Era: ${q.opts[q.ans]}`
    }
  }

  private _finishGame(): void {
    this.stop()
    const accuracy = this.correctCount / Math.max(this.answered, 1)
    this.result = { completed: true, accuracy, correct: this.correctCount, total: this.answered }
    this.difficulty.adapt(accuracy)
  }

  getProgress(): number { return this.currentQ / Math.max(this.totalQ, 1) }
  getCurrentQuestion(): QuestionData | null {
    return this.phase === "playing" && this.currentQ < this.totalQ ? this.questions[this.currentQ] : null
  }
}
