import { BaseGame } from './base-game'

export class BrainTrainer extends BaseGame {
  phase: "instruction" | "playing" | "result" = "instruction"
  round = 0
  totalRounds = 10
  subGame: "math" | "recall" | "count" = "math"
  correctCount = 0
  totalAnswered = 0
  currentQuestion: Record<string, unknown> = {}
  streak = 0
  instructionTimer = 0
  resultTimer = 0
  subGames = ["math", "recall", "count"]

  constructor(difficulty: any, scoring: any) {
    super(difficulty, scoring)
    this.name = "brain_trainer"
    this.displayName = "Brain Trainer"
  }

  start(): void {
    super.start()
    this.phase = "instruction"
    this.round = 0
    this.correctCount = 0
    this.totalAnswered = 0
    this.streak = 0
    this.instructionTimer = Date.now()
    this.feedbackMessage = "Brain Trainer: rispondi alle domande!"
  }

  update(_poseData?: any, dt = 0): void {
    if (!this.running) return
    if (this.phase === "instruction") {
      if ((Date.now() - this.instructionTimer) / 1000 > 2.5) this._nextRound()
      return
    }
    if (this.phase === "result") {
      this.resultTimer -= dt
      if (this.resultTimer <= 0) this._nextRound()
    }
  }

  private _nextRound(): void {
    if (this.round >= this.totalRounds) { this._finishGame(); return }
    this.round++
    this.phase = "playing"
    this.subGame = this.subGames[Math.floor(Math.random() * this.subGames.length)] as "math" | "recall" | "count"
    if (this.subGame === "math") this._genMath()
    else if (this.subGame === "recall") this._genRecall()
    else this._genCount()
  }

  private _genMath(): void {
    const level = this.difficulty.getLevel()
    const maxNum = 5 + level * 2
    let a = Math.floor(Math.random() * maxNum) + 1
    let b = Math.floor(Math.random() * maxNum) + 1
    const op = Math.random() < 0.5 ? "+" : "-"
    if (op === "-" && a < b) [a, b] = [b, a]
    const answer = op === "+" ? a + b : a - b
    const wrongs = new Set<number>()
    while (wrongs.size < 3) { const w = answer + Math.floor(Math.random() * 7) - 3; if (w !== answer && w >= 0) wrongs.add(w) }
    const options = [answer, ...wrongs].sort(() => Math.random() - 0.5)
    this.currentQuestion = { type: "math", text: `${a} ${op} ${b} = ?`, options, answer }
    this.feedbackMessage = `Round ${this.round}/${this.totalRounds}: ${a} ${op} ${b} = ?`
  }

  private _genRecall(): void {
    const level = this.difficulty.getLevel()
    const items = ["\u{1F34E}", "\u{1F431}", "\u{1F697}", "\u{1F3E0}", "\u{1F31E}", "\u{1F436}", "\u{1F33C}", "\u2B50", "\u{1F30A}", "\u{1F308}", "\u{1F422}", "\u{1F426}"]
    const count = Math.min(3 + level, 6)
    const recallItems = items.sort(() => Math.random() - 0.5).slice(0, count)
    const answer = recallItems[Math.floor(Math.random() * recallItems.length)]
    const options = [...recallItems].sort(() => Math.random() - 0.5)
    this.currentQuestion = { type: "recall", text: "Ricorda l'immagine cerchiata!", items: recallItems, highlight: answer, options, answer }
    this.feedbackMessage = `Round ${this.round}: ricorda e scegli l'immagine giusta`
  }

  private _genCount(): void {
    const level = this.difficulty.getLevel()
    const count = 3 + level
    const target = Math.floor(Math.random() * count) + 3
    const symbols = ["\u{1F535}", "\u{1F7E2}", "\u{1F534}", "\u{1F7E1}"]
    const s = symbols[Math.floor(Math.random() * symbols.length)]
    const grid = new Array(target).fill(s)
    const optionsSet = new Set<number>([target])
    while (optionsSet.size < 4) { const w = target + Math.floor(Math.random() * 7) - 3; if (w > 0) optionsSet.add(w) }
    const options = [...optionsSet].sort(() => Math.random() - 0.5).slice(0, 4)
    this.currentQuestion = { type: "count", text: "Quanti simboli ci sono?", symbols: grid, symbolChar: s, options, answer: target }
    this.feedbackMessage = `Round ${this.round}: conta i simboli!`
  }

  answer(value: unknown): void {
    if (this.phase !== "playing") return
    const q = this.currentQuestion
    const correct = value === q.answer
    this.totalAnswered++
    if (correct) {
      this.correctCount++; this.streak++
      this.feedbackMessage = "Corretto! +25 punti"
      this.scoring.addScore(this.name, 25)
    } else {
      this.streak = 0
      this.feedbackMessage = `Sbagliato! Era ${q.answer}`
    }
    this.phase = "result"
    this.resultTimer = 2.0
  }

  private _finishGame(): void {
    this.stop()
    const accuracy = this.correctCount / Math.max(this.totalAnswered, 1)
    this.result = { completed: true, accuracy, correct: this.correctCount, total: this.totalAnswered, streak: this.streak }
    this.difficulty.adapt(accuracy)
    this.scoring.addScore(this.name, Math.round(accuracy * 30))
  }

  getProgress(): number { return this.round / Math.max(this.totalRounds, 1) }
  getQuestionOptions(): unknown[] { return (this.currentQuestion.options as unknown[]) ?? [] }
  getCurrentQuestion(): Record<string, unknown> { return this.currentQuestion }
  getSubGame(): string { return this.subGame }
}
