import { BaseGame } from './base-game'
import { Difficulty } from '../engine/difficulty'
import { Scoring } from '../engine/scoring'

interface WordEntry {
  word: string
  found: boolean
}

interface PlacedWord {
  word: string
  row: number
  col: number
  dr: number
  dc: number
}

const WORD_POOLS: Record<string, string[]> = {
  animali: ["GATTO", "CANE", "LEONE", "PESCE", "UCCELLO", "CAVALLO", "CONIGLIO", "TIGRE", "VOLPE", "CERVELLO"],
  colori: ["ROSSO", "BLU", "VERDE", "GIALLO", "ROSA", "ARANCIONE", "MARRONE", "BIANCO", "NERO", "GRIGIO"],
  cibo: ["PANE", "LATTE", "CARNE", "FRUTTA", "DOLCE", "POMODORO", "FORMAGGIO", "PASTA", "ZUCCHERO", "SALE"],
  corpo: ["MANO", "TESTA", "PIEDE", "NASO", "OCCHIO", "ORECCHIO", "BOCCA", "GOMITO", "SPALLA", "DITO"],
}

const DIRS: [number, number][] = [
  [0, 1], [1, 0], [1, 1], [-1, 1],
]

export class CercaParole extends BaseGame {
  phase: "instruction" | "playing" = "instruction"
  grid: string[][] = []
  gridSize = 8
  words: WordEntry[] = []
  placed: PlacedWord[] = []
  selectedCells: [number, number][] = []
  foundCells: Set<string> = new Set()
  selectStart: [number, number] | null = null
  foundCount = 0
  totalWords = 0
  wordPool: string[] = []
  instructionTimer = 0

  constructor(difficulty: Difficulty, scoring: Scoring) {
    super(difficulty, scoring)
    this.name = "cerca_parole"
    this.displayName = "Cerca Parole"
  }

  start(): void {
    super.start()
    const level = this.difficulty.getLevel()
    this.gridSize = Math.min(6 + level, 12)
    this.phase = "instruction"
    this.instructionTimer = Date.now()
    this.selectedCells = []
    this.foundCells = new Set()
    this.foundCount = 0
    this.selectStart = null
    const poolKeys = Object.keys(WORD_POOLS)
    this.wordPool = WORD_POOLS[poolKeys[Math.floor(Math.random() * poolKeys.length)]]
    this.totalWords = Math.min(3 + level, this.wordPool.length)
    const chosen = this.wordPool.slice().sort(() => Math.random() - 0.5).slice(0, this.totalWords)
    this.words = chosen.map(w => ({ word: w, found: false }))
    this.placed = []
    this.grid = Array.from({ length: this.gridSize }, () =>
      Array.from({ length: this.gridSize }, () => '')
    )
    this._placeWords()
    this._fillEmpty()
    this.words = this.words.filter(w => this.placed.some(p => p.word === w.word))
    this.totalWords = this.words.length
    this.feedbackMessage = `Trova ${this.totalWords} parole nella griglia`
  }

  private _placeWords(): void {
    const sorted = [...this.words].sort((a, b) => b.word.length - a.word.length)
    for (const entry of sorted) {
      this._tryPlace(entry.word)
    }
  }

  private _tryPlace(word: string): boolean {
    const maxAttempts = 200
    for (let a = 0; a < maxAttempts; a++) {
      const dirIdx = Math.floor(Math.random() * DIRS.length)
      const [dr, dc] = DIRS[dirIdx]
      const row = Math.floor(Math.random() * this.gridSize)
      const col = Math.floor(Math.random() * this.gridSize)
      if (this._canPlace(word, row, col, dr, dc)) {
        for (let i = 0; i < word.length; i++) {
          this.grid[row + i * dr][col + i * dc] = word[i]
        }
        this.placed.push({ word, row, col, dr, dc })
        return true
      }
    }
    return false
  }

  private _canPlace(word: string, row: number, col: number, dr: number, dc: number): boolean {
    if (dr !== 0 && dc !== 0) {
      if (this.gridSize <= 7) return false
    }
    const endR = row + (word.length - 1) * dr
    const endC = col + (word.length - 1) * dc
    if (endR < 0 || endR >= this.gridSize || endC < 0 || endC >= this.gridSize) return false
    for (let i = 0; i < word.length; i++) {
      const r = row + i * dr
      const c = col + i * dc
      const existing = this.grid[r][c]
      if (existing !== '' && existing !== word[i]) return false
    }
    return true
  }

  private _fillEmpty(): void {
    const letters = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    for (let r = 0; r < this.gridSize; r++) {
      for (let c = 0; c < this.gridSize; c++) {
        if (this.grid[r][c] === '') {
          this.grid[r][c] = letters[Math.floor(Math.random() * letters.length)]
        }
      }
    }
  }

  update(_poseData?: any, _dt?: number): void {
    if (!this.running) return
    if (this.phase === "instruction" && (Date.now() - this.instructionTimer) / 1000 > 2) {
      this.phase = "playing"
    }
  }

  private _wordKey(r: number, c: number): string { return `${r},${c}` }

  selectCell(r: number, c: number): void {
    if (this.phase !== "playing") return
    if (r < 0 || r >= this.gridSize || c < 0 || c >= this.gridSize) return
    if (this.foundCells.has(this._wordKey(r, c))) return
    if (this.selectStart === null) {
      this.selectStart = [r, c]
      this.selectedCells = [[r, c]]
      return
    }
    const [sr, sc] = this.selectStart
    const dr = Math.sign(r - sr)
    const dc = Math.sign(c - sc)
    if (dr === 0 && dc === 0) {
      this.selectStart = null
      this.selectedCells = []
      return
    }
    const len = Math.max(Math.abs(r - sr), Math.abs(c - sc)) + 1
    const cells: [number, number][] = []
    for (let i = 0; i < len; i++) {
      cells.push([sr + i * dr, sc + i * dc])
    }
    const valid = cells.every(([cr, cc]) =>
      cr >= 0 && cr < this.gridSize && cc >= 0 && cc < this.gridSize
    )
    if (!valid) {
      this.selectStart = null
      this.selectedCells = []
      return
    }
    this.selectedCells = cells
    this._checkWord(cells)
  }

  private _checkWord(cells: [number, number][]): void {
    const selected = cells.map(([r, c]) => this.grid[r][c]).join('')
    const reversed = cells.map(([r, c]) => this.grid[r][c]).reverse().join('')
    for (const entry of this.words) {
      if (entry.found) continue
      if (entry.word === selected || entry.word === reversed) {
        entry.found = true
        this.foundCount++
        for (const [r, c] of cells) {
          this.foundCells.add(this._wordKey(r, c))
        }
        this.scoring.addScore(this.name, 20)
        this.feedbackMessage = `Trovata: ${entry.word}! (${this.foundCount}/${this.totalWords})`
        this.selectStart = null
        this.selectedCells = []
        if (this.foundCount === this.totalWords) this._finishGame()
        return
      }
    }
    this.feedbackMessage = "Parola non trovata, riprova"
    this.selectStart = null
    this.selectedCells = []
  }

  private _finishGame(): void {
    this.stop()
    const accuracy = this.foundCount / Math.max(this.totalWords, 1)
    this.result = { completed: true, accuracy, found: this.foundCount, total: this.totalWords, gridSize: this.gridSize }
    this.difficulty.adapt(accuracy)
    this.scoring.addScore(this.name, Math.round(accuracy * 40))
  }

  isSelected(r: number, c: number): boolean {
    return this.selectedCells.some(([sr, sc]) => sr === r && sc === c)
  }

  isFound(r: number, c: number): boolean {
    return this.foundCells.has(this._wordKey(r, c))
  }

  getGridSize(): number { return this.gridSize }
  getProgress(): number { return this.foundCount / Math.max(this.totalWords, 1) }
}
