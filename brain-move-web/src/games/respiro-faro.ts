import { BaseGame } from './base-game'
import { Difficulty } from '../engine/difficulty'
import { Scoring } from '../engine/scoring'

export class RespiroFaro extends BaseGame {
  phase: "inspira" | "espira" = "inspira"
  phaseDuration = 4.0
  cycleCount = 0
  totalCycles = 6
  phaseStart = 0
  circleScale = 0.3
  instructions = ["Inspira lentamente...", "Espira lentamente...", "Mantieni il ritmo..."]

  constructor(difficulty: Difficulty, scoring: Scoring) {
    super(difficulty, scoring)
    this.name = "respiro_faro"
    this.displayName = "Respiro del Faro"
  }

  start(): void {
    super.start()
    this.phase = "inspira"
    this.cycleCount = 0
    this.phaseStart = Date.now()
    this.circleScale = 0.3
    this.feedbackMessage = "Inspira lentamente..."
  }

  update(_poseData?: any, _dt?: number): void {
    if (!this.running) return
    const elapsed = (Date.now() - this.phaseStart) / 1000
    if (elapsed < this.phaseDuration) {
      const progress = elapsed / this.phaseDuration
      this.circleScale = this.phase === "inspira" ? 0.3 + 0.7 * progress : 1.0 - 0.7 * progress
    } else {
      this.phase = this.phase === "inspira" ? "espira" : "inspira"
      this.phaseStart = Date.now()
      this.cycleCount++
      if (this.cycleCount >= this.totalCycles) {
        this.stop()
        this.result = { completed: true, accuracy: 1, cycles: this.cycleCount }
        this.scoring.addScore(this.name, 10)
        this.feedbackMessage = "Ottimo controllo, sessione completata!"
        return
      }
      this.feedbackMessage = this.instructions[Math.floor(Math.random() * this.instructions.length)]
    }
  }

  getCircleScale(): number { return this.circleScale }
  getProgress(): number { return Math.min(this.cycleCount / this.totalCycles, 1) }
}
