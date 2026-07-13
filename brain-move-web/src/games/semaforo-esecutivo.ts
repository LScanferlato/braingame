import { BaseGame } from './base-game'

const COLORS: Record<string, { action: string; display: string; label: string }> = {
  verde: { action: "passo_avanti", display: "\u{1F7E2}", label: "Avanti" },
  rosso: { action: "fermo", display: "\u{1F534}", label: "Fermo" },
  blu: { action: "passo_sinistra", display: "\u{1F535}", label: "Sinistra" },
  giallo: { action: "passo_destra", display: "\u{1F7E1}", label: "Destra" },
}

export class SemaforoEsecutivo extends BaseGame {
  currentColor: string | null = null
  currentCommand: string | null = null
  colorTimer = 0
  colorInterval = 4.0
  roundCount = 0
  maxRounds = 10
  correctCount = 0
  inhibitionErrors = 0
  waitingForResponse = false
  responseReceived = false
  inhibitionMode = false

  constructor(difficulty: any, scoring: any) {
    super(difficulty, scoring)
    this.name = "semaforo_esecutivo"
    this.displayName = "Semaforo Esecutivo"
  }

  start(): void {
    super.start()
    this.roundCount = 0
    this.correctCount = 0
    this.inhibitionErrors = 0
    this._nextRound()
    this.feedbackMessage = "Segui il colore con il movimento giusto"
  }

  private _nextRound(): void {
    if (this.roundCount >= this.maxRounds) { this._finishGame(); return }
    const level = this.difficulty.getLevel()
    this.roundCount++
    this.waitingForResponse = true
    this.responseReceived = false
    if (level >= 3 && Math.random() < 0.3) {
      this.inhibitionMode = true
      this.currentColor = Math.random() < 0.5 ? "verde" : "rosso"
      this.currentCommand = "fermo"
      this.feedbackMessage = "Attenzione: regola speciale! Resta fermo"
    } else {
      this.inhibitionMode = false
      const colors = Object.keys(COLORS)
      const color = colors[Math.floor(Math.random() * colors.length)]
      this.currentColor = color
      this.currentCommand = COLORS[color].action
      this.feedbackMessage = `${COLORS[color].display} ${COLORS[color].label}`
    }
    this.colorTimer = Date.now()
  }

  update(_poseData?: any, _dt?: number): void {
    if (!this.running) return
    if (this.waitingForResponse) {
      if ((Date.now() - this.colorTimer) / 1000 > this.colorInterval) {
        if (!this.responseReceived) this.inhibitionErrors++
        this._nextRound()
      }
    }
  }

  validateAction(movement: string): void {
    if (!this.waitingForResponse || this.responseReceived) return
    this.responseReceived = true
    if (this.inhibitionMode) {
      if (movement === "center" || movement === "stationary") {
        this.correctCount++
        this.feedbackMessage = "Ottimo controllo inibitorio!"
      } else {
        this.inhibitionErrors++
        this.feedbackMessage = "Dovevi restare fermo, ma va bene"
      }
    } else {
      const expected = this.currentCommand
      const match =
        (expected === "passo_avanti" && movement === "forward") ||
        (expected === "fermo" && (movement === "center" || movement === "stationary")) ||
        (expected === "passo_sinistra" && movement === "left") ||
        (expected === "passo_destra" && movement === "right")
      if (match) { this.correctCount++; this.feedbackMessage = "Perfetto!" }
      else { this.feedbackMessage = "Prossimo round, riprova" }
    }
  }

  private _finishGame(): void {
    this.stop()
    const total = this.correctCount + this.inhibitionErrors
    const accuracy = this.correctCount / Math.max(total, 1)
    this.result = { completed: true, accuracy, correct: this.correctCount, errors: this.inhibitionErrors, totalRounds: this.roundCount }
    this.difficulty.adapt(accuracy)
    this.scoring.addScore(this.name, Math.round(accuracy * 50))
  }

  getCurrentColor(): string | null { return this.currentColor }
  getColorDisplay(): { action: string; display: string; label: string } | null {
    return this.currentColor ? COLORS[this.currentColor] ?? null : null
  }
  getProgress(): number { return this.roundCount / this.maxRounds }
}
