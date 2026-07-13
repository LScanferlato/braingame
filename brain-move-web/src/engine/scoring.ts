export class Scoring {
  totalScore = 0
  gameScores: Record<string, number> = {}

  addScore(gameName: string, points: number): void {
    this.totalScore += points
    if (!(gameName in this.gameScores)) this.gameScores[gameName] = 0
    this.gameScores[gameName] += points
  }

  getTotal(): number { return this.totalScore }
  getGameScore(gameName: string): number { return this.gameScores[gameName] ?? 0 }

  reset(): void {
    this.totalScore = 0
    this.gameScores = {}
  }
}
