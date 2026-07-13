import { BaseGame } from './base-game'

const COLORS: Record<string, string> = {
  rosso: "#e63c3c", blu: "#3282e6", verde: "#3cc83c",
  giallo: "#e6d232", viola: "#b450dc", arancione: "#f09628",
}

interface Balloon {
  x: number; y: number; speed: number; colorName: string; color: string
  radius: number; wobbleT: number
}

export class Palloncini extends BaseGame {
  phase: "instruction" | "playing" = "instruction"
  balloons: Balloon[] = []
  popped = 0
  missed = 0
  maxMissed = 5
  totalSpawned = 0
  spawnTimer = 0
  spawnInterval = 2.0
  baseSpeed = 60
  maxBalloons = 6
  instructionTimer = 0

  constructor(difficulty: any, scoring: any) {
    super(difficulty, scoring)
    this.name = "palloncini"
    this.displayName = "Palloncini"
  }

  start(): void {
    super.start()
    this.phase = "instruction"
    this.balloons = []
    this.popped = 0
    this.missed = 0
    this.totalSpawned = 0
    this.spawnTimer = 0
    this.instructionTimer = Date.now()
    const level = this.difficulty.getLevel()
    this.spawnInterval = Math.max(0.6, 2.0 - level * 0.2)
    this.baseSpeed = 50 + level * 12
    this.maxBalloons = Math.min(4 + level, 10)
    this.feedbackMessage = "Scoppia i palloncini cliccandoli!"
  }

  update(_poseData?: any, dt = 0): void {
    if (!this.running) return
    if (this.phase === "instruction") {
      if ((Date.now() - this.instructionTimer) / 1000 > 2.5) {
        this.phase = "playing"
        this.feedbackMessage = "Scoppia i palloncini!"
      }
      return
    }
    this.spawnTimer += dt
    if (this.spawnTimer >= this.spawnInterval && this.balloons.length < this.maxBalloons) {
      this.spawnTimer = 0
      this._spawnBalloon()
    }
    for (let i = this.balloons.length - 1; i >= 0; i--) {
      const b = this.balloons[i]
      b.y -= b.speed * dt
      b.wobbleT += dt
      b.x += Math.sin(b.wobbleT * 2) * 20 * dt
      if (b.y < -80) {
        this.balloons.splice(i, 1)
        this.missed++
        if (this.missed >= this.maxMissed) { this._finishGame(); return }
      }
    }
  }

  private _spawnBalloon(): void {
    const colorNames = Object.keys(COLORS)
    const colorName = colorNames[Math.floor(Math.random() * colorNames.length)]
    const x = 200 + Math.random() * 600
    const speed = this.baseSpeed + (Math.random() - 0.5) * 30
    this.balloons.push({
      x, y: 700, speed, colorName, color: COLORS[colorName],
      radius: 30 + Math.floor(Math.random() * 15),
      wobbleT: Math.random() * Math.PI * 2,
    })
    this.totalSpawned++
  }

  popBalloon(index: number): void {
    if (this.phase !== "playing" || index < 0 || index >= this.balloons.length) return
    this.balloons.splice(index, 1)
    this.popped++
    const pts = 15
    this.scoring.addScore(this.name, pts)
    this.feedbackMessage = `+${pts} pt!`
  }

  private _finishGame(): void {
    this.stop()
    const total = this.popped + this.missed
    const accuracy = this.popped / Math.max(total, 1)
    this.result = { completed: true, accuracy, popped: this.popped, missed: this.missed, total }
    this.difficulty.adapt(accuracy)
  }

  getProgress(): number {
    const total = this.popped + this.missed
    return Math.min(1, total / Math.max(this.maxMissed * 2, 1))
  }
}
