import { BaseGame } from './base-game'

interface Question { q: string; opts: string[] }
interface CaregiverQ { q: string; pts: number }

const CAREGIVER_QS: CaregiverQ[] = [
  { q: "Il tuo caro ha perdite di memoria?", pts: 1 },
  { q: "La sua memoria è peggiore rispetto a qualche anno fa?", pts: 1 },
  { q: "Ripete domande, frasi o storie nello stesso giorno?", pts: 2 },
  { q: "Dimentica appuntamenti o eventi programmati?", pts: 1 },
  { q: "Perde o mette nel posto sbagliato oggetti?", pts: 1 },
  { q: "Dà la colpa ad altri di nascondere ciò che non trova?", pts: 1 },
  { q: "Ha problemi con giorno, data, mese, anno?", pts: 2 },
  { q: "È spaesato in ambienti non familiari?", pts: 1 },
  { q: "Ha problemi a maneggiare il denaro?", pts: 1 },
  { q: "Ha problemi a pagare fatture?", pts: 2 },
  { q: "Dimentica di prendere le medicine?", pts: 1 },
  { q: "Ha difficoltà a guidare?", pts: 1 },
  { q: "Ha problemi a usare elettrodomestici?", pts: 1 },
  { q: "Ha difficoltà a finire lavori domestici?", pts: 1 },
  { q: "Ha smesso o ridotto hobby?", pts: 1 },
  { q: "Si perde in dintorni familiari?", pts: 2 },
  { q: "Il suo senso di orientamento sta peggiorando?", pts: 1 },
  { q: "Ha problemi a trovare le parole?", pts: 1 },
  { q: "Confonde i nomi di familiari?", pts: 2 },
  { q: "Ha problemi a riconoscere persone familiari?", pts: 2 },
]

const COGNITIVO_QS: Question[] = [
  { q: "Che giorno della settimana è oggi?", opts: ["Lunedì", "Martedì", "Mercoledì", "Giovedì", "Venerdì", "Sabato", "Domenica"] },
  { q: "In che mese siamo?", opts: ["Gennaio", "Febbraio", "Marzo", "Aprile", "Maggio", "Giugno", "Luglio", "Agosto", "Settembre", "Ottobre", "Novembre", "Dicembre"] },
  { q: "In che stagione siamo?", opts: ["Primavera", "Estate", "Autunno", "Inverno"] },
  { q: "Quanto fa 7 × 8 ?", opts: ["42", "48", "56", "64"] },
  { q: "Quanto fa 93 − 27 ?", opts: ["56", "66", "76", "86"] },
  { q: "Conta all'indietro da 20 a 1. Dopo 15?", opts: ["13", "14", "16", "12"] },
  { q: "Quale NON era nella lista? BALL, BAND, CHIODO", opts: ["BALL", "BAND", "CHIODO", "CANE"] },
  { q: "Orologio 11:10. Angolo tra lancette?", opts: ["~30°", "~90°", "~120°", "~150°"] },
]

export class Valutazione extends BaseGame {
  phase: "info" | "playing" | "result" = "info"
  step: "caregiver" | "cognitivo" = "caregiver"
  currentQ = 0
  answers: Array<{ type: string; value?: boolean; idx?: number; correct?: boolean; punti?: number }> = []
  totalScore = 0
  maxScore = 0
  showFeedback = false
  feedbackText = ""
  feedbackTimer = 0

  constructor(difficulty: any, scoring: any) {
    super(difficulty, scoring)
    this.name = "valutazione"
    this.displayName = "Test di Valutazione"
  }

  start(): void {
    super.start()
    this.phase = "info"
    this.step = "caregiver"
    this.currentQ = 0
    this.answers = []
    this.totalScore = 0
    this.maxScore = 0
    this.showFeedback = false
    this.feedbackMessage = "Test di valutazione completo"
    setTimeout(() => { if (this.running) { this.phase = "playing"; this.feedbackMessage = "Rispondi alle domande del caregiver" } }, 2000)
  }

  update(_poseData?: any, dt = 0): void {
    if (!this.running || this.phase === "info") return
    if (this.showFeedback) {
      this.feedbackTimer -= dt
      if (this.feedbackTimer <= 0) { this.showFeedback = false; this._advance() }
    }
  }

  private _advance(): void {
    if (this.step === "caregiver") {
      this.currentQ++
      if (this.currentQ >= CAREGIVER_QS.length) {
        this.step = "cognitivo"
        this.currentQ = 0
        this.feedbackMessage = "Ora alcuni esercizi cognitivi"
      }
    } else {
      this.currentQ++
      if (this.currentQ >= COGNITIVO_QS.length) this._complete()
    }
  }

  answerCaregiver(value: boolean): void {
    if (this.phase !== "playing" || this.step !== "caregiver" || this.showFeedback || this.currentQ >= CAREGIVER_QS.length) return
    const pts = value ? CAREGIVER_QS[this.currentQ].pts : 0
    this.answers.push({ type: "caregiver", value, punti: pts })
    this.totalScore += pts
    this.maxScore += CAREGIVER_QS[this.currentQ].pts
    this.showFeedback = true
    this.feedbackTimer = 0.4
    this.feedbackText = value ? "Sì" : "No"
  }

  answerCognitivo(idx: number): void {
    if (this.phase !== "playing" || this.step !== "cognitivo" || this.showFeedback || this.currentQ >= COGNITIVO_QS.length) return
    const correct = idx === 0
    this.answers.push({ type: "cognitivo", idx, correct })
    if (correct) this.totalScore++
    this.maxScore++
    this.showFeedback = true
    this.feedbackTimer = 0.8
    this.feedbackText = correct ? "Corretto!" : `La risposta era: ${COGNITIVO_QS[this.currentQ].opts[0]}`
  }

  getCurrentCaregiver(): CaregiverQ | null {
    return this.step === "caregiver" && this.currentQ < CAREGIVER_QS.length ? CAREGIVER_QS[this.currentQ] : null
  }

  getCurrentCognitivo(): Question | null {
    return this.step === "cognitivo" && this.currentQ < COGNITIVO_QS.length ? COGNITIVO_QS[this.currentQ] : null
  }

  private _complete(): void {
    this.phase = "result"
    const pct = this.totalScore / Math.max(this.maxScore, 1)
    let livello: string, desc: string, colore: string
    if (pct >= 0.85) { livello = "Nessuna preoccupazione"; desc = "Il punteggio è nella norma."; colore = "#3cd25a" }
    else if (pct >= 0.60) { livello = "Lieve compromissione cognitiva"; desc = "Potrebbero esserci segni iniziali."; colore = "#e6be32" }
    else { livello = "Possibile decadimento cognitivo"; desc = "Si consiglia una visita specialistica."; colore = "#e63c3c" }
    this.result = { completed: true, accuracy: pct, totalScore: this.totalScore, maxScore: this.maxScore, livello, descrizione: desc, colore }
    this.stop()
    this.feedbackMessage = `${this.totalScore}/${this.maxScore} - ${livello}`
  }

  getProgress(): number {
    if (this.phase === "info") return 0
    const totalQ = CAREGIVER_QS.length + COGNITIVO_QS.length
    let done = this.currentQ
    if (this.step === "cognitivo") done += CAREGIVER_QS.length
    return Math.min(1, done / Math.max(totalQ, 1))
  }
}
