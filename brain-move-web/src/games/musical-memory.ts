import { BaseGame } from './base-game'
import { Difficulty } from '../engine/difficulty'
import { Scoring } from '../engine/scoring'

export class MusicalMemory extends BaseGame {
  phase: "instruction" | "showing" | "input" | "result" = "instruction"
  sequence: number[] = []
  userInput: number[] = []
  inputIndex = 0
  showIndex = 0
  showing = false
  showTimer = 0
  flashTimer = 0
  flashNote = -1
  round = 0
  maxRounds = 10
  correctRounds = 0
  instructionTimer = 0
  private audioCtx: AudioContext | null = null
  colors = ["#e63c3c", "#3c82e6", "#3cc83c", "#e6d232"]
  freqs = [262, 330, 392, 523]
  labels = ["Do", "Mi", "Sol", "Do'"]

  constructor(difficulty: Difficulty, scoring: Scoring) {
    super(difficulty, scoring)
    this.name = "musical_memory"
    this.displayName = "Musical Memory"
  }

  private _getAudioCtx(): AudioContext {
    if (!this.audioCtx) this.audioCtx = new AudioContext()
    return this.audioCtx
  }

  private _playNote(noteIdx: number): void {
    try {
      const ctx = this._getAudioCtx()
      const osc = ctx.createOscillator()
      const gain = ctx.createGain()
      osc.connect(gain)
      gain.connect(ctx.destination)
      osc.frequency.value = this.freqs[noteIdx]
      osc.type = "sine"
      gain.gain.setValueAtTime(0.25, ctx.currentTime)
      gain.gain.exponentialRampToValueAtTime(0.01, ctx.currentTime + 0.35)
      osc.start(ctx.currentTime)
      osc.stop(ctx.currentTime + 0.35)
    } catch { /* audio not available */ }
  }

  start(): void {
    super.start()
    this.phase = "instruction"
    this.sequence = []
    this.round = 0
    this.correctRounds = 0
    this.inputIndex = 0
    this.showing = false
    this.instructionTimer = Date.now()
    this.feedbackMessage = "Ripeti la sequenza musicale!"
  }

  update(_poseData?: any, dt = 0): void {
    if (!this.running) return
    if (this.phase === "instruction") {
      if ((Date.now() - this.instructionTimer) / 1000 > 2) this._nextNote()
      return
    }
    if (this.showing) {
      this.showTimer -= dt
      this.flashTimer -= dt
      if (this.flashTimer <= 0) this.flashNote = -1
      if (this.showTimer <= 0) {
        this.showing = false
        this.phase = "input"
        this.inputIndex = 0
        this.feedbackMessage = `Ripeti! (${this.round}/${this.maxRounds})`
      }
    } else if (this.phase === "result") {
      this.showTimer -= dt
      if (this.showTimer <= 0) this._nextNote()
    }
  }

  private _nextNote(): void {
    this.round++
    this.sequence.push(Math.floor(Math.random() * 4))
    this.showing = true
    this.showIndex = 0
    this.showTimer = this.sequence.length * 0.8
    this._flashNext()
  }

  private _flashNext(): void {
    if (this.showIndex < this.sequence.length) {
      const note = this.sequence[this.showIndex]
      this.flashNote = note
      this.flashTimer = 0.6
      this._playNote(note)
      this.showIndex++
      setTimeout(() => this._flashNext(), 800)
    }
  }

  pressButton(noteIdx: number): void {
    if (this.phase !== "input") return
    this._playNote(noteIdx)
    if (noteIdx === this.sequence[this.inputIndex]) {
      this.inputIndex++
      if (this.inputIndex >= this.sequence.length) {
        this.correctRounds++
        this.feedbackMessage = `Corretto! ${this.correctRounds}/${this.round}`
        if (this.round >= this.maxRounds) this._finishGame()
        else { this.phase = "result"; this.showTimer = 1.5 }
      }
    } else {
      this.feedbackMessage = "Sbagliato!"
      this._finishGame()
    }
  }

  private _finishGame(): void {
    this.stop()
    const accuracy = this.correctRounds / Math.max(this.round, 1)
    this.result = { completed: true, accuracy, correctRounds: this.correctRounds, totalRounds: this.round, sequenceLength: this.sequence.length }
    this.difficulty.adapt(accuracy)
    this.scoring.addScore(this.name, Math.round(accuracy * 30))
  }

  getProgress(): number { return this.round / Math.max(this.maxRounds, 1) }
  getFlashNote(): number { return this.flashNote }
  getPhase(): string { return this.showing ? "showing" : this.phase }
}
