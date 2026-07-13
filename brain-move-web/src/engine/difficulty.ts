export class Difficulty {
  level: number
  history: Array<["up" | "down" | "keep", number]> = []
  private minLevel: number
  private maxLevel: number

  constructor(initialLevel = 1, minLevel = 1, maxLevel = 5) {
    this.level = initialLevel
    this.minLevel = minLevel
    this.maxLevel = maxLevel
  }

  increase(): void {
    if (this.level < this.maxLevel) this.level++
    this.history.push(["up", this.level])
  }

  decrease(): void {
    if (this.level > this.minLevel) this.level--
    this.history.push(["down", this.level])
  }

  keep(): void {
    this.history.push(["keep", this.level])
  }

  adapt(accuracy: number, fatigueLevel: string = "bassa"): void {
    if (accuracy > 0.8 && fatigueLevel === "bassa") this.increase()
    else if (accuracy < 0.5 || fatigueLevel === "alta") this.decrease()
    else this.keep()
  }

  getLevel(): number { return this.level }
}
