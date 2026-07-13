import { BaseGame } from './base-game'
import { Difficulty } from '../engine/difficulty'
import { Scoring } from '../engine/scoring'

const WORDS = [
  { word: "CASA", hint: "Dove abiti" }, { word: "MARE", hint: "Acqua salata e grande" },
  { word: "SOLE", hint: "Luce nel cielo di giorno" }, { word: "LUNA", hint: "Brilla di notte" },
  { word: "GATTO", hint: "Fa miao" }, { word: "CANE", hint: "Fa bau" },
  { word: "FIORE", hint: "Colorato e profumato" }, { word: "ACQUA", hint: "Si beve" },
  { word: "PANE", hint: "Si mangia a colazione" }, { word: "MELA", hint: "Frutto rosso" },
  { word: "LIBRO", hint: "Lo leggi" }, { word: "TAVOLO", hint: "Dove mangi" },
  { word: "SEDIA", hint: "Dove ti siedi" }, { word: "PORTA", hint: "Entri e esci da qui" },
  { word: "FINESTRA", hint: "Vedi fuori da qui" }, { word: "SCUOLA", hint: "Dove impari" },
  { word: "CUCINA", hint: "Dove cucini" }, { word: "BAGNO", hint: "Ti lavi qui" },
  { word: "PARCO", hint: "Passeggi qui" }, { word: "PESCE", hint: "Vive nell'acqua" },
  { word: "CAFFE", hint: "Bevi la mattina" }, { word: "STELLA", hint: "Brilla di notte" },
  { word: "PIAZZA", hint: "Cuore del paese" }, { word: "PRATO", hint: "Erba verde" },
  { word: "NUVOLA", hint: "Vol nel cielo" }, { word: "SOFFITTO", hint: "È sopra di te" },
]

interface PlacedWord {
  word: string; hint: string; row: number; col: number; direction: "across" | "down"; solved: boolean
}

export class ParoleIncrociate extends BaseGame {
  gridSize = 7
  grid: string[][] = []
  solution: string[][] = []
  placedWords: PlacedWord[] = []
  currentWordIndex = 0
  userInput: string[] = []
  selectedCell = 0
  correctWords = 0
  totalWords = 0
  attempts = 0
  phase: "playing" = "playing"

  constructor(difficulty: Difficulty, scoring: Scoring) {
    super(difficulty, scoring)
    this.name = "parole_incrociate"
    this.displayName = "Parole Incrociate"
  }

  start(): void {
    super.start()
    const level = this.difficulty.getLevel()
    this.gridSize = level <= 2 ? 6 : level <= 3 ? 7 : 8
    this.totalWords = level <= 2 ? 3 : level <= 3 ? 4 : 5
    this.grid = Array.from({ length: this.gridSize }, () => new Array(this.gridSize).fill(""))
    this.solution = Array.from({ length: this.gridSize }, () => new Array(this.gridSize).fill(""))
    this.placedWords = []
    this.correctWords = 0
    this.attempts = 0
    this.currentWordIndex = 0
    this._placeWords()
    this.userInput = this.placedWords.length > 0 ? new Array(this.placedWords[0].word.length).fill(" ") : []
    this.selectedCell = 0
    this.feedbackMessage = "Incrocia le parole! Clicca sulla casella e scrivi"
  }

  private _placeWords(): void {
    const shuffled = [...WORDS].sort(() => Math.random() - 0.5).slice(0, this.totalWords + 5)
    shuffled.sort((a, b) => b.word.length - a.word.length)
    const placed: PlacedWord[] = []
    for (const wd of shuffled) {
      const word = wd.word.toUpperCase()
      if (word.length > this.gridSize) continue
      for (let attempt = 0; attempt < 20; attempt++) {
        const direction: "across" | "down" = Math.random() < 0.5 ? "across" : "down"
        const row = direction === "across" ? Math.floor(Math.random() * this.gridSize) : Math.floor(Math.random() * (this.gridSize - word.length + 1))
        const col = direction === "across" ? Math.floor(Math.random() * (this.gridSize - word.length + 1)) : Math.floor(Math.random() * this.gridSize)
        if (this._canPlace(word, row, col, direction)) {
          this._doPlace(word, row, col, direction)
          placed.push({ word, hint: wd.hint, row, col, direction, solved: false })
          break
        }
      }
      if (placed.length >= this.totalWords) break
    }
    this.placedWords = placed
    this.totalWords = placed.length
  }

  private _canPlace(word: string, row: number, col: number, direction: "across" | "down"): boolean {
    for (let i = 0; i < word.length; i++) {
      const r = direction === "across" ? row : row + i
      const c = direction === "across" ? col + i : col
      if (r >= this.gridSize || c >= this.gridSize) return false
      if (this.solution[r][c] !== "" && this.solution[r][c] !== word[i]) return false
      if (this.solution[r][c] === word[i]) continue
      for (const [dr, dc] of [[-1, 0], [1, 0], [0, -1], [0, 1]]) {
        const nr = r + dr, nc = c + dc
        if (nr >= 0 && nr < this.gridSize && nc >= 0 && nc < this.gridSize && this.solution[nr][nc] !== "") return false
      }
    }
    return true
  }

  private _doPlace(word: string, row: number, col: number, direction: "across" | "down"): void {
    for (let i = 0; i < word.length; i++) {
      if (direction === "across") this.solution[row][col + i] = word[i]
      else this.solution[row + i][col] = word[i]
    }
  }

  update(_poseData?: any, _dt?: number): void {}

  setCellLetter(letter: string): void {
    if (this.phase !== "playing" || this.currentWordIndex >= this.placedWords.length) return
    const wi = this.placedWords[this.currentWordIndex]
    if (wi.solved) return
    if (this.selectedCell >= 0 && this.selectedCell < this.userInput.length) {
      this.userInput[this.selectedCell] = letter.toUpperCase()
      if (this.selectedCell < this.userInput.length - 1) this.selectedCell++
    }
  }

  deleteLetter(): void {
    if (this.phase !== "playing") return
    if (this.selectedCell > 0) {
      this.userInput[this.selectedCell] = " "
      this.selectedCell--
    }
  }

  moveCursor(dir: "right" | "left"): void {
    const wi = this.placedWords[this.currentWordIndex]
    if (!wi) return
    if (dir === "right") this.selectedCell = Math.min(this.selectedCell + 1, wi.word.length - 1)
    else this.selectedCell = Math.max(this.selectedCell - 1, 0)
  }

  selectCell(row: number, col: number): void {
    if (this.phase !== "playing") return
    for (let idx = 0; idx < this.placedWords.length; idx++) {
      const wp = this.placedWords[idx]
      if (wp.solved) continue
      if (wp.direction === "across" && wp.row === row && wp.col <= col && col < wp.col + wp.word.length) {
        this.currentWordIndex = idx
        this.userInput = new Array(wp.word.length).fill(" ")
        this.selectedCell = col - wp.col
        this.feedbackMessage = wp.hint
        return
      }
      if (wp.direction === "down" && wp.col === col && wp.row <= row && row < wp.row + wp.word.length) {
        this.currentWordIndex = idx
        this.userInput = new Array(wp.word.length).fill(" ")
        this.selectedCell = row - wp.row
        this.feedbackMessage = wp.hint
        return
      }
    }
  }

  checkWord(): void {
    if (this.phase !== "playing" || this.currentWordIndex >= this.placedWords.length) return
    const wi = this.placedWords[this.currentWordIndex]
    if (wi.solved) return
    const guess = this.userInput.join("").trim().toUpperCase()
    this.attempts++
    if (guess === wi.word) {
      wi.solved = true
      this.correctWords++
      this.scoring.addScore(this.name, 20)
      this.feedbackMessage = `Corretto! ${wi.word}`
      const { row, col, direction } = wi
      for (let i = 0; i < wi.word.length; i++) {
        if (direction === "across") this.grid[row][col + i] = wi.word[i]
        else this.grid[row + i][col] = wi.word[i]
      }
      this._nextWord()
    } else {
      this.feedbackMessage = "Non è corretto, riprova"
    }
  }

  private _nextWord(): void {
    for (const wp of this.placedWords) {
      if (!wp.solved) {
        this.currentWordIndex = this.placedWords.indexOf(wp)
        this.userInput = new Array(wp.word.length).fill(" ")
        this.selectedCell = 0
        this.feedbackMessage = wp.hint
        return
      }
    }
    this._finishGame()
  }

  private _finishGame(): void {
    this.stop()
    const accuracy = this.correctWords / Math.max(this.totalWords, 1)
    this.result = { completed: true, accuracy, correct: this.correctWords, total: this.totalWords, attempts: this.attempts }
    this.difficulty.adapt(accuracy)
    this.scoring.addScore(this.name, Math.round(accuracy * 40))
  }

  getCurrentWord(): PlacedWord | null { return this.placedWords[this.currentWordIndex] ?? null }
  getCurrentWordDisplay(): [string[], number] { return [this.userInput, this.selectedCell] }
  getGrid(): string[][] {
    const display = this.grid.map(row => [...row])
    const wi = this.getCurrentWord()
    if (wi && !wi.solved) {
      const { row, col, direction } = wi
      for (let i = 0; i < this.userInput.length; i++) {
        const ch = this.userInput[i]
        if (ch && ch.trim()) {
          if (direction === "across") display[row][col + i] = ch
          else display[row + i][col] = ch
        }
      }
    }
    return display
  }
  getSolution(): string[][] { return this.solution }
  getHints(): string[] {
    return this.placedWords.map((wp, i) => {
      const dir = wp.direction === "across" ? " → " : " ↓ "
      return `${i + 1}. ${wp.hint}${dir}${wp.solved ? " ✓" : ""}`
    })
  }
  getActiveWord(): PlacedWord | null { return this.placedWords[this.currentWordIndex] ?? null }
  isActiveCell(r: number, c: number): boolean {
    const w = this.getActiveWord()
    if (!w || w.solved) return false
    if (w.direction === "across") return w.row === r && c >= w.col && c < w.col + w.word.length
    return w.col === c && r >= w.row && r < w.row + w.word.length
  }
  isPartOfAnyWord(r: number, c: number): boolean {
    return this.solution[r]?.[c] !== undefined && this.solution[r][c] !== ""
  }
  getProgress(): number { return this.correctWords / Math.max(this.totalWords, 1) }
}
