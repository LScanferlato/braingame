import { BaseGame } from './base-game'

const OBJECTS: Record<string, string> = {
  sedia: "\u{1F6CB}", tavolo: "\u{1F4CB}", pianta: "\u{1F333}",
  finestra: "\u{1F5BC}", libro: "\u{1F4D6}", lampada: "\u{1F4A1}",
}

export class MappaStanza extends BaseGame {
  gridSize = 2
  numObjects = 3
  objectPositions: Record<string, [number, number]> = {}
  userPositions: Record<string, [number, number]> = {}
  phase: "showing" | "recall" = "showing"
  showTimer = 0
  showDuration = 8.0

  constructor(difficulty: any, scoring: any) {
    super(difficulty, scoring)
    this.name = "mappa_stanza"
    this.displayName = "Mappa della Stanza"
  }

  start(): void {
    super.start()
    const level = this.difficulty.getLevel()
    this.gridSize = level <= 2 ? 2 : 3
    this.numObjects = Math.min(3 + level, Object.keys(OBJECTS).length, this.gridSize * this.gridSize)
    const allObjects = Object.keys(OBJECTS)
    const chosen = allObjects.sort(() => Math.random() - 0.5).slice(0, this.numObjects)
    const positions: [number, number][] = []
    for (let r = 0; r < this.gridSize; r++)
      for (let c = 0; c < this.gridSize; c++)
        positions.push([r, c])
    positions.sort(() => Math.random() - 0.5)
    this.objectPositions = {}
    chosen.forEach((obj, i) => { this.objectPositions[obj] = positions[i] })
    this.userPositions = {}
    this.phase = "showing"
    this.showTimer = Date.now()
    this.feedbackMessage = "Osserva la posizione degli oggetti"
  }

  update(_poseData?: any, _dt?: number): void {
    if (!this.running) return
    if (this.phase === "showing" && (Date.now() - this.showTimer) / 1000 >= this.showDuration) {
      this.phase = "recall"
      this.feedbackMessage = "Posiziona gli oggetti nella posizione corretta"
    }
  }

  placeObject(objName: string, row: number, col: number): void {
    if (this.phase !== "recall") return
    this.userPositions[objName] = [row, col]
    if (Object.keys(this.userPositions).length >= this.numObjects) this._checkAnswer()
  }

  private _checkAnswer(): void {
    let correct = 0
    for (const [obj, expectedPos] of Object.entries(this.objectPositions)) {
      const userPos = this.userPositions[obj]
      if (userPos && userPos[0] === expectedPos[0] && userPos[1] === expectedPos[1]) correct++
    }
    const accuracy = correct / Math.max(this.numObjects, 1)
    this.result = { completed: true, accuracy, correct, total: this.numObjects }
    this.difficulty.adapt(accuracy)
    this.scoring.addScore(this.name, Math.round(accuracy * 50))
    this.stop()
    this.feedbackMessage = `Hai trovato ${correct} su ${this.numObjects} oggetti!`
  }

  getObjectsToPlace(): string[] { return Object.keys(this.objectPositions).filter(o => !(o in this.userPositions)) }
  getObjectIcon(obj: string): string { return OBJECTS[obj] ?? "?" }

  getProgress(): number {
    if (this.phase === "showing") return Math.min((Date.now() - this.showTimer) / (this.showDuration * 1000), 1) * 0.4
    return 0.4 + 0.6 * (Object.keys(this.userPositions).length / Math.max(this.numObjects, 1))
  }
}
