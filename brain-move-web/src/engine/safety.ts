import type { PoseData } from '../types'

export class SafetyEngine {
  warnings: string[] = []
  events: Array<{ type: string; details: string }> = []
  maxTrunkAngle = 25
  maxInstability = 0.7
  suggestions: Record<string, string> = {
    busto_inclinato: "Mantieni la schiena dritta",
    instabilita_alta: "Fermiamoci un momento e appoggiamoci",
    passo_largo: "Fai passi più piccoli",
    uscita_frame: "Rimani nel raggio della telecamera",
  }

  evaluate(poseData: PoseData | null): { status: string; message: string; warnings?: string[] } {
    this.warnings = []
    if (!poseData) return { status: "no_pose", message: "Non ti vedo bene, sistemiamoci meglio." }

    const trunkAngle = poseData.trunk_angle ?? 0
    const instability = poseData.instability ?? 0
    const inFrame = poseData.in_frame ?? true

    if (!inFrame) this.warnings.push("uscita_frame")
    if (trunkAngle > this.maxTrunkAngle) this.warnings.push("busto_inclinato")
    if (instability > this.maxInstability) this.warnings.push("instabilita_alta")

    if (this.warnings.includes("instabilita_alta") || this.warnings.includes("uscita_frame"))
      return { status: "pause", message: "Fermiamoci un momento e appoggiamoci.", warnings: this.warnings }
    if (this.warnings.length)
      return { status: "warning", message: "Facciamo movimenti più piccoli e lenti.", warnings: this.warnings }
    return { status: "ok", message: "Movimento sicuro.", warnings: [] }
  }

  logEvent(eventType: string, details = ""): void {
    this.events.push({ type: eventType, details })
  }

  getEvents(): Array<{ type: string; details: string }> { return [...this.events] }

  reset(): void { this.warnings = []; this.events = [] }
}
