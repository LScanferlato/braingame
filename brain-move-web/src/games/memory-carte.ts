import { BaseGame } from './base-game'
import { Difficulty } from '../engine/difficulty'
import { Scoring } from '../engine/scoring'

const SYMBOLS: Record<string, string> = {
  gatto: "\u{1F431}", cane: "\u{1F436}", leone: "\u{1F981}",
  coniglio: "\u{1F430}", tartaruga: "\u{1F422}", delfino: "\u{1F42C}",
  farfalla: "\u{1F98B}", uccello: "\u{1F426}", stella: "\u2B50",
  cuore: "\u2764\uFE0F", sole: "\u{1F31E}", luna: "\u{1F319}",
  fiore: "\u{1F33C}", albero: "\u{1F333}", montagna: "\u26F0\uFE0F", onda: "\u{1F30A}",
}

export class MemoryCarte extends BaseGame {
  grid: string[] = []
  revealed: boolean[] = []
  matched: boolean[] = []
  firstCard: number | null = null
  secondCard: number | null = null
  waiting = false
  waitTimer = 0
  waitDelay = 1.0
  pairsFound = 0
  totalPairs = 0
  attempts = 0
  cols = 4
  rows = 3
  phase: "preview" | "playing" = "preview"
  showAllTimer = 0
  showAllDuration = 3.0

  constructor(difficulty: Difficulty, scoring: Scoring) {
    super(difficulty, scoring)
    this.name = "memory_carte"
    this.displayName = "Memory Carte"
  }

  start(): void {
    super.start()
    const level = this.difficulty.getLevel()
    if (level <= 2) { this.rows = 3; this.cols = 4 }
    else if (level <= 3) { this.rows = 4; this.cols = 4 }
    else { this.rows = 4; this.cols = 5 }
    const totalCells = this.rows * this.cols
    this.totalPairs = Math.floor(totalCells / 2)
    const symbols = Object.keys(SYMBOLS)
    const chosen = symbols.sort(() => Math.random() - 0.5).slice(0, this.totalPairs)
    const pairs = [...chosen, ...chosen].sort(() => Math.random() - 0.5)
    this.grid = pairs
    this.revealed = new Array(pairs.length).fill(true)
    this.matched = new Array(pairs.length).fill(false)
    this.firstCard = null
    this.secondCard = null
    this.waiting = false
    this.pairsFound = 0
    this.attempts = 0
    this.phase = "preview"
    this.showAllTimer = Date.now()
    this.feedbackMessage = "Ricorda le posizioni delle carte!"
  }

  update(_poseData?: any, dt?: number): void {
    if (!this.running) return
    if (this.phase === "preview") {
      if ((Date.now() - this.showAllTimer) / 1000 >= this.showAllDuration) {
        this.revealed = new Array(this.grid.length).fill(false)
        this.phase = "playing"
        this.feedbackMessage = "Trova le coppie! Seleziona due carte"
      }
    } else if (this.phase === "playing" && this.waiting) {
      const elapsed = (Date.now() - this.waitTimer) / 1000
      if (elapsed >= this.waitDelay) this._hidePair()
    }
  }

  selectCard(index: number): void {
    if (this.phase !== "playing" || this.waiting) return
    if (index < 0 || index >= this.grid.length || this.revealed[index] || this.matched[index]) return
    this.revealed[index] = true
    if (this.firstCard === null) {
      this.firstCard = index
      this.feedbackMessage = "Seleziona un'altra carta"
    } else if (this.secondCard === null && index !== this.firstCard) {
      this.secondCard = index
      this.attempts++
      this._checkMatch()
    }
  }

  private _checkMatch(): void {
    const i = this.firstCard!, j = this.secondCard!
    if (this.grid[i] === this.grid[j]) {
      this.matched[i] = true; this.matched[j] = true
      this.pairsFound++
      this.scoring.addScore(this.name, 15)
      this.feedbackMessage = `Coppia trovata: ${SYMBOLS[this.grid[i]]}!`
      this.firstCard = null; this.secondCard = null
      if (this.pairsFound === this.totalPairs) this._finishGame()
    } else {
      this.waiting = true
      this.waitTimer = Date.now()
      this.waitDelay = 1.0
      this.feedbackMessage = "Non corrispondono..."
    }
  }

  private _hidePair(): void {
    if (this.firstCard !== null) this.revealed[this.firstCard] = false
    if (this.secondCard !== null) this.revealed[this.secondCard] = false
    this.firstCard = null; this.secondCard = null
    this.waiting = false
    this.feedbackMessage = "Trova le coppie!"
  }

  private _finishGame(): void {
    this.stop()
    const accuracy = this.pairsFound / Math.max(this.attempts, 1)
    this.result = { completed: true, accuracy: Math.min(accuracy, 1), pairsFound: this.pairsFound, totalPairs: this.totalPairs, attempts: this.attempts }
    this.difficulty.adapt(Math.min(accuracy, 1))
    this.scoring.addScore(this.name, Math.round(accuracy * 40))
  }

  getCardSymbol(index: number): string { return SYMBOLS[this.grid[index]] ?? "?" }
  isCardRevealed(index: number): boolean { return this.revealed[index] || this.matched[index] }
  isCardMatched(index: number): boolean { return this.matched[index] }
  getGridSize(): [number, number] { return [this.rows, this.cols] }
  getProgress(): number { return this.pairsFound / Math.max(this.totalPairs, 1) }
}
