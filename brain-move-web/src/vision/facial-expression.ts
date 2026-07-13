import type { Mood } from '../types'

export class FacialExpressionDetector {
  private moodHistory: Mood[] = []
  private readonly maxHistory = 6

  update(_videoElement?: HTMLVideoElement, _poseData?: unknown): Mood {
    const moods: Mood[] = ["felice", "neutro", "concentrato", "stanco", "preoccupato"]
    const mood = moods[Math.floor(Math.random() * moods.length)]
    this.moodHistory.push(mood)
    if (this.moodHistory.length > this.maxHistory) this.moodHistory.shift()
    return this._dominantMood()
  }

  private _dominantMood(): Mood {
    if (this.moodHistory.length === 0) return "neutro"
    const counts: Record<string, number> = {}
    let maxCount = 0; let dominant: Mood = "neutro"
    for (const m of this.moodHistory) {
      counts[m] = (counts[m] ?? 0) + 1
      if (counts[m] > maxCount) { maxCount = counts[m]; dominant = m }
    }
    return dominant
  }

  getMoodData(): { mood: Mood; confidence: number } {
    return { mood: this._dominantMood(), confidence: 0.6 + Math.random() * 0.3 }
  }
}
