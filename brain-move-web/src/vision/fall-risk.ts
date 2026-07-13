import type { PoseData } from '../types'

export class FallRiskDetector {
  private prevHipY: number | null = null
  private prevShoulderWidth: number | null = null
  events: string[] = []

  evaluate(poseData: PoseData | null): "ok" | "medio" | "alto" {
    this.events = []
    if (!poseData) return "ok"
    const hipY = poseData.hip_center?.[1]
    const shoulderWidth = poseData.shoulder_width
    const trunkAngle = poseData.trunk_angle ?? 0
    const instability = poseData.instability ?? 0
    const inFrame = poseData.in_frame ?? true
    if (!inFrame && this.prevHipY !== null) this.events.push("uscita_improvvisa")
    if (trunkAngle > 30) this.events.push("busto_pericoloso")
    if (instability > 0.8) this.events.push("instabilita_elevata")
    if (this.prevHipY !== null && hipY !== undefined && (hipY - this.prevHipY) > 50) this.events.push("caduta_anca")
    if (this.prevShoulderWidth !== null && shoulderWidth !== undefined && Math.abs(shoulderWidth - this.prevShoulderWidth) / this.prevShoulderWidth > 0.4)
      this.events.push("rotazione_brusca")
    this.prevHipY = hipY ?? null
    this.prevShoulderWidth = shoulderWidth ?? null
    if (this.events.length >= 2) return "alto"
    if (this.events.length === 1) return "medio"
    return "ok"
  }

  reset(): void { this.prevHipY = null; this.prevShoulderWidth = null; this.events = [] }
}
