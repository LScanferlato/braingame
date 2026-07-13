import { Scoring } from './scoring'
import { Difficulty } from './difficulty'
import { SafetyEngine } from './safety'
import { Profile } from './profile'
import type { GameResult } from '../types'

export class Session {
  sessionId: string
  startTime: number | null = null
  gameLog: Array<{
    sessionId: string
    game: string
    difficulty: number
    result: GameResult
    timestamp: number
  }> = []
  currentGame: string | null = null

  constructor(
    public profile: Profile,
    public scoring: Scoring,
    public difficulty: Difficulty,
    public safety: SafetyEngine,
  ) {
    this.sessionId = new Date().toISOString().replace(/[:.]/g, '-').slice(0, 19)
  }

  start(): void {
    this.startTime = Date.now()
    this.safety.reset()
  }

  logGame(gameName: string, result: GameResult): void {
    this.gameLog.push({
      sessionId: this.sessionId,
      game: gameName,
      difficulty: this.difficulty.getLevel(),
      result,
      timestamp: Date.now(),
    })
  }

  end(): {
    sessionId: string
    durationSeconds: number
    totalScore: number
    finalDifficulty: number
    safetyEvents: Array<{ type: string; details: string }>
    games: Array<{ sessionId: string; game: string; difficulty: number; result: GameResult; timestamp: number }>
  } {
    const duration = this.startTime ? (Date.now() - this.startTime) / 1000 : 0
    const summary = {
      sessionId: this.sessionId,
      durationSeconds: Math.round(duration * 10) / 10,
      totalScore: this.scoring.getTotal(),
      finalDifficulty: this.difficulty.getLevel(),
      safetyEvents: this.safety.getEvents(),
      games: this.gameLog,
    }
    this._save(summary)
    return summary
  }

  private _save(summary: unknown): void {
    try {
      const stored = JSON.parse(localStorage.getItem('brainmove_sessions') ?? '[]')
      stored.push(summary)
      localStorage.setItem('brainmove_sessions', JSON.stringify(stored))
    } catch { /* storage full or unavailable */ }
  }

  getElapsedMinutes(): number {
    if (!this.startTime) return 0
    return (Date.now() - this.startTime) / 60000
  }
}
