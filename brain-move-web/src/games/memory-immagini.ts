import { BaseGame } from './base-game'

const FAMILIAR: Record<string, string> = {
  nonno: "\u{1F474}", nonna: "\u{1F475}", mamma: "\u{1F469}", papa: "\u{1F468}",
  bambino: "\u{1F476}", bambina: "\u{1F467}", casa: "\u{1F3E0}", macchina: "\u{1F697}",
  cane: "\u{1F436}", gatto: "\u{1F431}", albero: "\u{1F333}", fiore: "\u{1F33C}",
  pane: "\u{1F35E}", mela: "\u{1F34E}", acqua: "\u{1F4A7}", sole: "\u{1F31E}",
  luna: "\u{1F319}", stella: "\u2B50", cuore: "\u2764\uFE0F", sorriso: "\u{1F60A}",
  libro: "\u{1F4DA}", palla: "\u26BD", torta: "\u{1F370}", orologio: "\u{1F570}",
}

export class MemoryImmagini extends BaseGame {
  phase: "instruction" | "study" | "playing" = "instruction"
  gridRows = 0
  gridCols = 0
  cards: Array<{ label: string; icon: string }> = []
  revealed: boolean[] = []
  matched: boolean[] = []
  firstCard: number | null = null
  secondCardIdx: number | null = null
  waiting = false
  waitTimer = 0
  pairsFound = 0
  totalPairs = 0
  attempts = 0
  instructionTimer = 0
  studyTimer = 0
  studyDuration = 5

  constructor(difficulty: any, scoring: any) {
    super(difficulty, scoring)
    this.name = "memory_immagini"
    this.displayName = "Memory Immagini"
  }

  start(): void {
    super.start()
    const level = this.difficulty.getLevel()
    this.gridCols = Math.min(3 + level, 6)
    this.gridRows = Math.min(2 + Math.floor(level / 2), 4)
    if (this.gridCols * this.gridRows % 2 !== 0) this.gridRows++
    this.totalPairs = (this.gridCols * this.gridRows) / 2
    this.studyDuration = Math.max(3, 7 - level)
    this.phase = "instruction"
    this.instructionTimer = Date.now()
    this.feedbackMessage = `Memorizza le immagini! Hai ${this.studyDuration} secondi`
    const keys = Object.keys(FAMILIAR).sort(() => Math.random() - 0.5).slice(0, this.totalPairs)
    const deck = [...keys, ...keys].sort(() => Math.random() - 0.5)
    this.cards = deck.map(label => ({ label, icon: FAMILIAR[label] }))
    this.revealed = new Array(this.cards.length).fill(false)
    this.matched = new Array(this.cards.length).fill(false)
    this.firstCard = null
    this.waiting = false
    this.pairsFound = 0
    this.attempts = 0
  }

  update(_poseData?: any, dt = 0): void {
    if (!this.running) return
    if (this.phase === "instruction" && (Date.now() - this.instructionTimer) / 1000 > 2) {
      this.phase = "study"
      this.studyTimer = Date.now()
      this.revealed = new Array(this.cards.length).fill(true)
    } else if (this.phase === "study" && (Date.now() - this.studyTimer) / 1000 > this.studyDuration) {
      this.phase = "playing"
      this.revealed = new Array(this.cards.length).fill(false)
      this.feedbackMessage = "Trova le coppie!"
    } else if (this.phase === "playing" && this.waiting) {
      this.waitTimer -= dt
      if (this.waitTimer <= 0) this._endWait()
    }
  }

  selectCard(idx: number): boolean {
    if (this.phase !== "playing" || this.waiting || this.matched[idx] || this.revealed[idx]) return false
    this.revealed[idx] = true
    if (this.firstCard === null) { this.firstCard = idx; return true }
    this.attempts++
    const second = idx
    if (this.cards[this.firstCard].label === this.cards[second].label) {
      this.matched[this.firstCard] = true; this.matched[second] = true
      this.pairsFound++
      this.firstCard = null
      this.feedbackMessage = `Trovata coppia! ${this.pairsFound}/${this.totalPairs}`
      if (this.pairsFound === this.totalPairs) this._finishGame()
      return true
    }
    this.waiting = true
    this.waitTimer = 1.2
    this.secondCardIdx = second
    this.feedbackMessage = "Non è la coppia giusta"
    return true
  }

  private _endWait(): void {
    if (this.firstCard !== null) this.revealed[this.firstCard] = false
    if (this.secondCardIdx !== null) this.revealed[this.secondCardIdx] = false
    this.firstCard = null; this.waiting = false
  }

  private _finishGame(): void {
    this.stop()
    const accuracy = this.totalPairs / Math.max(this.attempts, 1)
    this.result = { completed: true, accuracy: Math.min(accuracy, 1), pairsFound: this.pairsFound, attempts: this.attempts }
    this.difficulty.adapt(Math.min(accuracy, 1))
    this.scoring.addScore(this.name, Math.round(accuracy * 30))
  }

  getProgress(): number { return this.pairsFound / Math.max(this.totalPairs, 1) }
  isCardRevealed(idx: number): boolean { return this.revealed[idx] }
  isCardMatched(idx: number): boolean { return this.matched[idx] }
  getCardIcon(idx: number): string { return this.cards[idx]?.icon ?? "?" }
  getGridSize(): [number, number] { return [this.gridRows, this.gridCols] }
}
