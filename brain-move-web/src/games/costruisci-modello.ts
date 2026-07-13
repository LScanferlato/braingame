import { BaseGame } from './base-game'
import { Difficulty } from '../engine/difficulty'
import { Scoring } from '../engine/scoring'

const SHAPES: Record<string, { shape: string; color: string; label: string }> = {
  cerchio_rosso: { shape: "circle", color: "#dc3232", label: "Cerchio Rosso" },
  quadrato_bl: { shape: "rect", color: "#3232dc", label: "Quadrato Blu" },
  triangolo_verde: { shape: "triangle", color: "#32b432", label: "Triangolo Verde" },
  stella_gialla: { shape: "star", color: "#dcc832", label: "Stella Gialla" },
  diamante_arancio: { shape: "diamond", color: "#dc8c32", label: "Diamante Arancio" },
  cuore_rosa: { shape: "heart", color: "#dc6496", label: "Cuore Rosa" },
}

export class CostruisciModello extends BaseGame {
  modelPieces: string[] = []
  userPieces: string[] = []
  phase: "showing" | "building" = "showing"
  showTimer = 0
  showDuration = 15.0
  availablePieces = Object.keys(SHAPES)

  constructor(difficulty: Difficulty, scoring: Scoring) {
    super(difficulty, scoring)
    this.name = "costruisci_modello"
    this.displayName = "Costruisci il Modello"
  }

  start(): void {
    super.start()
    const level = this.difficulty.getLevel()
    const numPieces = Math.min(3 + level, this.availablePieces.length)
    this.modelPieces = this.availablePieces.sort(() => Math.random() - 0.5).slice(0, numPieces)
    this.userPieces = []
    this.phase = "showing"
    this.showTimer = Date.now()
    this.feedbackMessage = "Osserva il modello e ricordalo"
  }

  update(_poseData?: any, _dt?: number): void {
    if (!this.running) return
    if (this.phase === "showing" && (Date.now() - this.showTimer) / 1000 >= this.showDuration) {
      this.phase = "building"
      this.feedbackMessage = "Ora ricostruisci il modello"
    }
  }

  placePiece(pieceName: string): void {
    if (this.phase !== "building") return
    this.userPieces.push(pieceName)
    if (this.userPieces.length >= this.modelPieces.length) this._checkAnswer()
  }

  private _checkAnswer(): void {
    const correct = this.userPieces.filter((p, i) => p === this.modelPieces[i]).length
    const accuracy = correct / Math.max(this.modelPieces.length, 1)
    this.result = { completed: true, accuracy, correct, total: this.modelPieces.length, model: this.modelPieces }
    this.difficulty.adapt(accuracy)
    this.scoring.addScore(this.name, Math.round(accuracy * 40))
    this.stop()
    this.feedbackMessage = `Hai costruito ${correct} su ${this.modelPieces.length} pezzi correttamente!`
  }

  getModelPreview(): string[] {
    if (this.phase === "showing" && (Date.now() - this.showTimer) / 1000 < this.showDuration - 2) return this.modelPieces
    return []
  }

  getShapeInfo(key: string): { shape: string; color: string; label: string } | null { return SHAPES[key] ?? null }
  getAvailablePieces(): string[] { return this.availablePieces }

  getProgress(): number {
    if (this.phase === "showing") return Math.min((Date.now() - this.showTimer) / (this.showDuration * 1000), 1) * 0.4
    return 0.4 + 0.6 * (this.userPieces.length / Math.max(this.modelPieces.length, 1))
  }
}
