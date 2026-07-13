import { BaseGame } from './base-game'

const EMOJI_POOL = [
  "\u{1F34E}", "\u{1F34A}", "\u{1F34B}", "\u{1F347}", "\u{1F349}", "\u{1F353}",
  "\u{1F33C}", "\u{1F33B}", "\u{1F33A}", "\u{1F337}", "\u{1F331}", "\u{1F340}",
  "\u2B50", "\u{1F535}", "\u{1F7E2}", "\u{1F534}", "\u{1F7E1}", "\u{1F7E3}",
  "\u{1F7E0}", "\u{1F7E4}", "\u{1F31F}", "\u{1F308}", "\u{1F300}", "\u{1F31E}",
]

export class Puzzle extends BaseGame {
  phase: "instruction" | "playing" = "instruction"
  gridSize = 2
  targetGrid: string[][] = []
  currentGrid: string[][] = []
  selectedR = -1
  selectedC = -1
  correctCount = 0
  totalMoves = 0
  hintCount = 0
  maxHints = 3
  instructionTimer = 0

  constructor(difficulty: any, scoring: any) {
    super(difficulty, scoring)
    this.name = "puzzle"
    this.displayName = "Puzzle"
  }

  start(): void {
    super.start()
    const level = this.difficulty.getLevel()
    this.gridSize = Math.min(2 + level, 6)
    this.maxHints = Math.max(1, 4 - level)
    this.phase = "instruction"
    this.selectedR = -1
    this.selectedC = -1
    this.correctCount = 0
    this.totalMoves = 0
    this.hintCount = 0
    this.instructionTimer = Date.now()
    this.feedbackMessage = `Puzzle ${this.gridSize}x${this.gridSize}: scambia due tessere per ricreare l'immagine`
  }

  update(_poseData?: any, _dt?: number): void {
    if (!this.running) return
    if (this.phase === "instruction" && (Date.now() - this.instructionTimer) / 1000 > 2) {
      this.phase = "playing"
      this._generatePuzzle()
    }
  }

  private _generatePuzzle(): void {
    this.targetGrid = Array.from({ length: this.gridSize }, () =>
      Array.from({ length: this.gridSize }, () => EMOJI_POOL[Math.floor(Math.random() * EMOJI_POOL.length)])
    )
    const flat = this.targetGrid.flat().sort(() => Math.random() - 0.5)
    this.currentGrid = Array.from({ length: this.gridSize }, (_, r) =>
      flat.slice(r * this.gridSize, (r + 1) * this.gridSize)
    )
  }

  selectPiece(r: number, c: number): void {
    if (this.phase !== "playing") return
    if (this.selectedR === -1) {
      this.selectedR = r; this.selectedC = c
      this.feedbackMessage = `Selezionato: riga ${r + 1}, colonna ${c + 1}. Scegli dove spostarlo`
    } else {
      if (this.selectedR === r && this.selectedC === c) {
        this.selectedR = -1; this.feedbackMessage = "Selezione annullata"; return
      }
      this._swap(this.selectedR, this.selectedC, r, c)
      this.selectedR = -1
    }
  }

  private _swap(r1: number, c1: number, r2: number, c2: number): void {
    const tmp = this.currentGrid[r1][c1]
    this.currentGrid[r1][c1] = this.currentGrid[r2][c2]
    this.currentGrid[r2][c2] = tmp
    this.totalMoves++
    this._checkProgress()
  }

  private _checkProgress(): void {
    let correct = 0
    for (let r = 0; r < this.gridSize; r++)
      for (let c = 0; c < this.gridSize; c++)
        if (this.currentGrid[r][c] === this.targetGrid[r][c]) correct++
    this.correctCount = correct
    const total = this.gridSize * this.gridSize
    if (correct === total) { this.feedbackMessage = "Puzzle completato!"; this._finishGame() }
    else this.feedbackMessage = `${correct}/${total} tessere al posto giusto`
  }

  useHint(): [number, number] | null {
    if (this.phase !== "playing" || this.hintCount >= this.maxHints) return null
    for (let r = 0; r < this.gridSize; r++)
      for (let c = 0; c < this.gridSize; c++)
        if (this.currentGrid[r][c] !== this.targetGrid[r][c]) {
          this.hintCount++
          this.feedbackMessage = `Indizio: la tessera in (${r + 1},${c + 1}) è sbagliata`
          return [r, c]
        }
    return null
  }

  private _finishGame(): void {
    this.stop()
    const penalty = 1 - (this.hintCount / Math.max(this.maxHints, 1)) * 0.15
    const efficiency = Math.max(0.3, 1 - this.totalMoves / Math.max(this.gridSize * this.gridSize * 3, 1))
    const accuracy = 0.7 * efficiency + 0.3 * penalty
    this.result = { completed: true, accuracy, correct: this.correctCount, totalMoves: this.totalMoves, gridSize: this.gridSize, hintsUsed: this.hintCount }
    this.difficulty.adapt(accuracy)
    this.scoring.addScore(this.name, Math.round(accuracy * 30))
  }

  getProgress(): number { return this.correctCount / Math.max(this.gridSize * this.gridSize, 1) }
  isSelected(r: number, c: number): boolean { return this.selectedR === r && this.selectedC === c }
}
