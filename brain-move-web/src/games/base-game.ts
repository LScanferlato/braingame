import { Difficulty } from '../engine/difficulty'
import { Scoring } from '../engine/scoring'
import type { PoseData, GameState, GameResult } from '../types'

export abstract class BaseGame {
  difficulty: Difficulty
  scoring: Scoring
  name = "base_game"
  displayName = "Gioco Base"
  running = false
  state: GameState = "idle"
  result: GameResult = { completed: false, accuracy: 0 }
  feedbackMessage = ""
  startTime: number | null = null
  durationSeconds = 0

  constructor(difficultyEngine: Difficulty, scoringEngine: Scoring) {
    this.difficulty = difficultyEngine
    this.scoring = scoringEngine
  }

  start(): void {
    this.running = true
    this.state = "playing"
    this.startTime = Date.now()
    this.feedbackMessage = `Preparati per ${this.displayName}`
  }

  stop(): void {
    this.running = false
    this.state = "finished"
    if (this.startTime) this.durationSeconds = (Date.now() - this.startTime) / 1000
  }

  abstract update(poseData?: PoseData | null, dt?: number): void

  getState() {
    return {
      name: this.name,
      displayName: this.displayName,
      state: this.state,
      feedback: this.feedbackMessage,
      duration: this.durationSeconds,
      result: this.result,
    }
  }

  isFinished(): boolean { return this.state === "finished" }
  getResult(): GameResult { return this.result }
  getProgress(): number { return 0 }
}
