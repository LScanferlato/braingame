import { BaseGame } from './base-game'
import { Difficulty } from '../engine/difficulty'
import { Scoring } from '../engine/scoring'

export class Basket extends BaseGame {
  phase: "instruction" | "ready" | "thrown" = "instruction"
  throwHand: "right" | "left" = "right"
  rightThrown = false
  leftThrown = false
  correctCount = 0
  totalAttempts = 0
  ballPos: [number, number] | null = null
  ballVel: [number, number] | null = null
  ballTrail: Array<[number, number]> = []
  ballFlying = false
  ballStartTime = 0
  ballDuration = 1.5
  hoopX = 0.85
  hoopY = 0.30
  hoopRadius = 40
  scoreTimer = 0
  instructionTimer = 0

  constructor(difficulty: Difficulty, scoring: Scoring) {
    super(difficulty, scoring)
    this.name = "basket"
    this.displayName = "Basket"
  }

  start(): void {
    super.start()
    this.phase = "instruction"
    this.throwHand = "right"
    this.rightThrown = false
    this.leftThrown = false
    this.correctCount = 0
    this.totalAttempts = 0
    this.ballFlying = false
    this.ballTrail = []
    this.instructionTimer = Date.now()
    this.feedbackMessage = "Lancia con la mano DESTRA! Alzala e lancia"
  }

  update(_poseData?: any, dt = 0): void {
    if (!this.running) return
    if (this.phase === "instruction") {
      if ((Date.now() - this.instructionTimer) / 1000 > 3) {
        this.phase = "ready"
        this.feedbackMessage = this._handInstruction()
      }
      return
    }
    if (this.ballFlying) {
      const elapsed = (Date.now() - this.ballStartTime) / 1000
      const t = elapsed / this.ballDuration
      if (t >= 1) this._checkHoop()
      else this._updateBallPhysics(t)
    }
    if (this.scoreTimer > 0) {
      this.scoreTimer -= dt
      if (this.scoreTimer <= 0) this._nextThrow()
    }
  }

  private _handInstruction(): string {
    return this.throwHand === "right" ? "Ora lancia con la MANO DESTRA!" : "Ora lancia con la MANO SINISTRA!"
  }

  launchBall(hand: "right" | "left"): void {
    if (this.phase !== "ready" || this.ballFlying || hand !== this.throwHand) return
    const startPos: [number, number] = [400, 650]
    const vx = (hand === "right" ? 1 : -1) * 300
    const vy = -500
    this.ballFlying = true
    this.ballStartTime = Date.now()
    this.ballPos = startPos
    this.ballVel = [vx, vy]
    this.ballTrail = [startPos]
    this.totalAttempts++
    this.feedbackMessage = "Lancio!"
  }

  private _updateBallPhysics(t: number): void {
    if (!this.ballPos || !this.ballVel) return
    const [vx, vy] = this.ballVel
    const gravity = 400
    const px = this.ballPos[0] + vx * t * 0.5
    const py = this.ballPos[1] + vy * t * 0.5 + 0.5 * gravity * t * t * 0.25
    this.ballPos = [px, py]
    this.ballTrail.push([px, py])
    if (this.ballTrail.length > 30) this.ballTrail.shift()
  }

  private _checkHoop(): void {
    this.ballFlying = false
    if (!this.ballPos) { this._miss(); return }
    const hoopScreenX = this.hoopX * 800
    const hoopScreenY = this.hoopY * 500
    const [bx, by] = this.ballPos
    const dist = Math.sqrt((bx - hoopScreenX) ** 2 + (by - hoopScreenY) ** 2)
    if (dist < this.hoopRadius * 2) this._score()
    else this._miss()
  }

  private _score(): void {
    this.correctCount++
    const handLabel = this.throwHand === "right" ? "destra" : "sinistra"
    this.scoreTimer = 2.0
    this.scoring.addScore(this.name, 25)
    this.feedbackMessage = `Canestro con la mano ${handLabel}!`
    if (this.throwHand === "right") this.rightThrown = true
    else this.leftThrown = true
  }

  private _miss(): void {
    const handLabel = this.throwHand === "right" ? "destra" : "sinistra"
    this.scoreTimer = 2.0
    this.feedbackMessage = `Mancato con la mano ${handLabel}, riprova!`
    if (this.throwHand === "right") this.rightThrown = true
    else this.leftThrown = true
  }

  private _nextThrow(): void {
    this.ballPos = null; this.ballVel = null; this.ballTrail = []
    if (!this.leftThrown) { this.throwHand = "left"; this.feedbackMessage = "Ora lancia con la MANO SINISTRA!" }
    else if (!this.rightThrown) { this.throwHand = "right"; this.feedbackMessage = "Ora lancia con la MANO DESTRA!" }
    else this._finishGame()
  }

  private _finishGame(): void {
    this.stop()
    const accuracy = this.correctCount / Math.max(this.totalAttempts, 1)
    this.result = { completed: true, accuracy, correct: this.correctCount, totalAttempts: this.totalAttempts }
    this.difficulty.adapt(accuracy)
    this.scoring.addScore(this.name, Math.round(accuracy * 30))
  }

  getBallPos(): [number, number] | null { return this.ballPos }
  getBallTrail(): Array<[number, number]> { return this.ballTrail }
  getHoopPos(): [number, number, number] { return [this.hoopX, this.hoopY, this.hoopRadius] }
  getProgress(): number { return ((this.rightThrown ? 1 : 0) + (this.leftThrown ? 1 : 0)) / 2 }
}
