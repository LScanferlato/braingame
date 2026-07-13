import { BaseGame } from './base-game'
import { Difficulty } from '../engine/difficulty'
import { Scoring } from '../engine/scoring'

const ITEMS = ["mela", "chiave", "fiore", "casa", "sole", "tazza", "libro", "stella"]
const ITEM_ICONS: Record<string, string> = {
  mela: "\u{1F34E}", chiave: "\u{1F511}", fiore: "\u{1F33C}", casa: "\u{1F3E0}",
  sole: "\u{1F31E}", tazza: "\u2615", libro: "\u{1F4D6}", stella: "\u2B50",
}

export class PassiRicorda extends BaseGame {
  sequence: string[] = []
  userAnswer: string[] = []
  phase: "showing" | "moving" | "recall" | "feedback" = "showing"
  showIndex = 0
  showTimer = 0
  showInterval = 2.0
  recallOptions: string[] = []
  movementTimer = 0
  correctCount = 0
  totalAttempts = 0
  itemResults: Array<"correct" | "wrong" | null> = []
  feedbackTimer = 0
  lastAttemptCorrect = false
  lastItemResult: "correct" | "wrong" | null = null
  lastItemValue: string | null = null

  constructor(difficulty: Difficulty, scoring: Scoring) {
    super(difficulty, scoring)
    this.name = "passi_ricorda"
    this.displayName = "Passi e Ricorda"
  }

  start(): void {
    super.start()
    const level = this.difficulty.getLevel()
    const seqLen = Math.min(2 + level, ITEMS.length)
    this.sequence = [...ITEMS].sort(() => Math.random() - 0.5).slice(0, seqLen)
    this.userAnswer = []
    this.recallOptions = [...ITEMS].sort(() => Math.random() - 0.5)
    this.phase = "showing"
    this.showIndex = 0
    this.showTimer = Date.now()
    this.correctCount = 0
    this.totalAttempts = 0
    this.itemResults = []
    this.lastAttemptCorrect = false
    this.lastItemResult = null
    this.lastItemValue = null
    this.feedbackMessage = "Guarda la sequenza e cammina sul posto"
  }

  update(_poseData?: any, dt = 0): void {
    if (!this.running) return
    if (this.phase === "showing") {
      const elapsed = (Date.now() - this.showTimer) / 1000
      if (elapsed >= this.showInterval) {
        this.showIndex++
        this.showTimer = Date.now()
        if (this.showIndex >= this.sequence.length) {
          this.phase = "moving"
          this.movementTimer = Date.now()
          this.feedbackMessage = "Ora cammina piano sul posto!"
        }
      }
    } else if (this.phase === "moving") {
      if ((Date.now() - this.movementTimer) / 1000 > 8) {
        this.phase = "recall"
        this.feedbackMessage = "Scegli gli elementi nell'ordine giusto"
      }
    } else if (this.phase === "feedback") {
      this.feedbackTimer -= dt
      if (this.feedbackTimer <= 0) {
        if (this.lastAttemptCorrect || this.totalAttempts >= 3) {
          this.stop()
          const accuracy = this.correctCount / this.totalAttempts
          this.result = { completed: true, accuracy, correct: this.correctCount, total: this.totalAttempts, sequence: this.sequence }
          this.difficulty.adapt(accuracy)
        } else {
          this.userAnswer = []
          this.itemResults = []
          this.phase = "recall"
          this.lastItemResult = null
          this.lastItemValue = null
          this.feedbackMessage = "Riprova! Scegli gli elementi nell'ordine giusto"
        }
      }
    }
  }

  selectItem(item: string): "correct" | "wrong" | null {
    if (this.phase !== "recall") return null
    const idx = this.userAnswer.length
    const result: "correct" | "wrong" = item === this.sequence[idx] ? "correct" : "wrong"
    this.lastItemResult = result
    this.lastItemValue = item
    this.userAnswer.push(item)
    this.itemResults.push(result)
    if (this.userAnswer.length === this.sequence.length) this._checkAnswer()
    return result
  }

  private _checkAnswer(): void {
    this.totalAttempts++
    this.lastAttemptCorrect = this.itemResults.every(r => r === "correct")
    if (this.lastAttemptCorrect) {
      this.correctCount++
      this.scoring.addScore(this.name, 20)
      this.feedbackMessage = "Perfetto, sequenza corretta!"
    } else {
      this.feedbackMessage = "Non preoccuparti, riproviamo"
    }
    this.phase = "feedback"
    this.feedbackTimer = 2.0
    this.lastItemResult = null
    this.lastItemValue = null
  }

  getCurrentItem(): string | null {
    if (this.phase === "showing" && this.showIndex < this.sequence.length)
      return this.sequence[this.showIndex]
    return null
  }

  getOptions(): string[] { return this.recallOptions }
  getItemIcon(item: string): string { return ITEM_ICONS[item] ?? "?" }
  getItemResult(idx: number): "correct" | "wrong" | null { return this.itemResults[idx] ?? null }

  getProgress(): number {
    if (this.phase === "showing") return (this.showIndex / Math.max(this.sequence.length, 1)) * 0.3
    if (this.phase === "moving") return 0.3 + 0.3 * Math.min((Date.now() - this.movementTimer) / 8000, 1)
    if (this.phase === "recall" || this.phase === "feedback") return 0.6 + 0.4 * (this.userAnswer.length / Math.max(this.sequence.length, 1))
    return 0
  }
}
