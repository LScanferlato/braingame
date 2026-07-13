import { BaseGame } from './base-game'
import { Difficulty } from '../engine/difficulty'
import { Scoring } from '../engine/scoring'

const SYMBOLS: Record<string, string> = {
  gatto: "\u{1F431}", cane: "\u{1F436}", coniglio: "\u{1F430}",
  delfino: "\u{1F42C}", farfalla: "\u{1F98B}", uccello: "\u{1F426}",
  stella: "\u2B50", cuore: "\u2764\uFE0F", sole: "\u{1F31E}",
  luna: "\u{1F319}", fiore: "\u{1F33C}", moneta: "\u{1FA99}",
}

export class SequenzaSimboli extends BaseGame {
  sequence: string[] = []
  userSequence: string[] = []
  availableSymbols: string[] = []
  phase: "showing" | "input" | "correct_flash" | "wrong_flash" = "showing"
  showIndex = 0
  showTimer = 0
  showInterval = 1.5
  roundNumber = 0
  maxRounds = 8
  correctCount = 0
  highlightIndex = 0
  flashTimer = 0
  flashDuration = 0

  constructor(difficulty: Difficulty, scoring: Scoring) {
    super(difficulty, scoring)
    this.name = "sequenza_simboli"
    this.displayName = "Sequenza Simboli"
  }

  start(): void {
    super.start()
    const level = this.difficulty.getLevel()
    const seqLen = Math.min(3 + level, 8)
    const symbols = Object.keys(SYMBOLS)
    this.availableSymbols = symbols.sort(() => Math.random() - 0.5).slice(0, Math.min(6, symbols.length))
    this.sequence = Array.from({ length: seqLen }, () => this.availableSymbols[Math.floor(Math.random() * this.availableSymbols.length)])
    this.userSequence = []
    this.roundNumber = 0
    this.correctCount = 0
    this.phase = "showing"
    this.showIndex = 0
    this.showTimer = Date.now()
    this.highlightIndex = 0
    this.feedbackMessage = "Osserva la sequenza!"
  }

  update(_poseData?: any, _dt?: number): void {
    if (!this.running) return
    if (this.phase === "showing") {
      if ((Date.now() - this.showTimer) / 1000 >= this.showInterval) {
        this.showIndex++
        this.showTimer = Date.now()
        if (this.showIndex >= this.sequence.length) {
          this.phase = "input"
          this.highlightIndex = -1
          this.feedbackMessage = "Ripeti la sequenza cliccando i simboli"
        } else {
          this.highlightIndex = this.showIndex
        }
      }
    } else if (this.phase === "correct_flash") {
      if ((Date.now() - this.flashTimer) / 1000 >= 0.8) {
        this.roundNumber++
        this.roundNumber >= this.maxRounds ? this._finishGame() : this._nextRound()
      }
    } else if (this.phase === "wrong_flash") {
      if ((Date.now() - this.flashTimer) / 1000 >= 1.2) this._finishGame()
    }
  }

  private _nextRound(): void {
    const level = this.difficulty.getLevel()
    const extra = Math.min(Math.floor(this.roundNumber / 2), 2)
    const newLen = Math.min(3 + level + extra, Object.keys(SYMBOLS).length)
    this.sequence = Array.from({ length: newLen }, () => this.availableSymbols[Math.floor(Math.random() * this.availableSymbols.length)])
    this.userSequence = []
    this.phase = "showing"
    this.showIndex = 0
    this.showTimer = Date.now()
    this.highlightIndex = 0
    this.feedbackMessage = `Round ${this.roundNumber + 1}: osserva!`
  }

  selectSymbol(symbol: string): void {
    if (this.phase !== "input") return
    this.userSequence.push(symbol)
    const idx = this.userSequence.length - 1
    if (this.userSequence[idx] !== this.sequence[idx]) {
      this.phase = "wrong_flash"
      this.flashTimer = Date.now()
      this.feedbackMessage = "Sbagliato!"
      return
    }
    if (this.userSequence.length === this.sequence.length) {
      this.correctCount++
      this.scoring.addScore(this.name, 20)
      this.phase = "correct_flash"
      this.flashTimer = Date.now()
      this.feedbackMessage = "Corretto!"
    }
  }

  private _finishGame(): void {
    this.stop()
    const accuracy = this.correctCount / Math.max(this.roundNumber, 1)
    this.result = { completed: true, accuracy, correctRounds: this.correctCount, totalRounds: this.roundNumber, sequenceLength: this.sequence.length }
    this.difficulty.adapt(accuracy)
    this.scoring.addScore(this.name, Math.round(accuracy * 50))
  }

  getCurrentShowItem(): string | null {
    if (this.phase === "showing" && this.showIndex < this.sequence.length)
      return SYMBOLS[this.sequence[this.showIndex]] ?? null
    return null
  }

  getAvailableSymbols(): Array<[string, string]> {
    return this.availableSymbols.map(s => [s, SYMBOLS[s]])
  }

  getProgress(): number {
    if (this.phase === "showing") return (this.showIndex / Math.max(this.sequence.length, 1)) * 0.5
    return 0.5 + 0.5 * (this.roundNumber / Math.max(this.maxRounds, 1))
  }

  getRoundInfo(): [number, number] { return [this.roundNumber + 1, this.maxRounds] }
  getPhase(): string { return this.phase }
}
