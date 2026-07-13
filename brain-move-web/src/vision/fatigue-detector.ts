import type { PoseData } from '../types'

export class FatigueDetector {
  private speedHistory: number[] = []
  private instHistory: number[] = []
  private trunkHistory: number[] = []
  private readonly maxHistory = 30

  update(poseData: PoseData | null): string {
    if (!poseData) return "bassa"
    const speed = Math.abs(poseData.instability ?? 0)
    const inst = poseData.instability ?? 0
    const trunk = poseData.trunk_angle ?? 0
    this.speedHistory.push(speed); if (this.speedHistory.length > this.maxHistory) this.speedHistory.shift()
    this.instHistory.push(inst); if (this.instHistory.length > this.maxHistory) this.instHistory.shift()
    this.trunkHistory.push(trunk); if (this.trunkHistory.length > this.maxHistory) this.trunkHistory.shift()
    if (this.instHistory.length < 10) return "bassa"
    const avgInst = this.instHistory.reduce((a, b) => a + b, 0) / this.instHistory.length
    const avgTrunk = this.trunkHistory.reduce((a, b) => a + b, 0) / this.trunkHistory.length
    if (avgInst > 0.5) return "alta"
    if (avgTrunk > 20) return "media"
    return "bassa"
  }

  shouldSuggestPause(): boolean { return this.instHistory.length >= 10 && this.instHistory.reduce((a, b) => a + b, 0) / this.instHistory.length > 0.5 }

  reset(): void { this.speedHistory = []; this.instHistory = []; this.trunkHistory = [] }
}
