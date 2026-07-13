import { Session } from '../engine/session'
import { Scoring } from '../engine/scoring'
import { Difficulty } from '../engine/difficulty'
import { SafetyEngine } from '../engine/safety'
import { Profile } from '../engine/profile'
import { createAllGames, GAME_MENU_DATA } from '../games/game-registry'
import { PoseDetector } from '../vision/pose-detector'
import { MovementRules } from '../vision/movement-rules'
import { FatigueDetector } from '../vision/fatigue-detector'
import { FallRiskDetector } from '../vision/fall-risk'
import { FacialExpressionDetector } from '../vision/facial-expression'
import type { BaseGame } from '../games/base-game'
import type { PoseData } from '../types'

export class App {
  private container: HTMLElement
  private canvas: HTMLCanvasElement
  private ctx: CanvasRenderingContext2D
  private overlay: HTMLElement

  private profile = new Profile()
  private scoring = new Scoring()
  private difficulty = new Difficulty()
  private safety = new SafetyEngine()
  private session = new Session(this.profile, this.scoring, this.difficulty, this.safety)
  private games: BaseGame[] = []
  private currentGame: BaseGame | null = null
  private gameIndex = -1

  private poseDetector = new PoseDetector()
  private movementRules = new MovementRules()
  private fatigueDetector = new FatigueDetector()
  private fallRiskDetector = new FallRiskDetector()
  private facialExpression = new FacialExpressionDetector()

  private state: "menu" | "playing" | "finished" | "report" = "menu"
  private menuView: "main" | "games" = "main"
  private sessionMode = false
  private pallonciniHandler: ((e: MouseEvent) => void) | null = null
  private lastPhase: string | null = null
  private phaseCheckGames = new Set(['mappa_stanza', 'memory_carte', 'memory_immagini', 'cerca_parole'])
  private lastTime = 0
  private particles: Array<{ x: number; y: number; vx: number; vy: number; life: number; maxLife: number; size: number; color: string }> = []
  private confetti: Array<{ x: number; y: number; vx: number; vy: number; life: number; maxLife: number; size: number; color: string; rotation: number; rotSpeed: number }> = []
  private animFrameId = 0
  private progressAnim = 0
  private lastScore = 0

  constructor(container: HTMLElement) {
    this.container = container
    this.canvas = container.querySelector<HTMLCanvasElement>('#game-canvas')!
    this.ctx = this.canvas.getContext('2d')!
    this.overlay = container.querySelector<HTMLElement>('#ui-overlay')!

    this.games = createAllGames(this.difficulty, this.scoring)
    this._resize()
    this._initParticles()
    this._renderMenu()
    this._startLoop()
    window.addEventListener('resize', () => this._resize())
  }

  private _resize(): void {
    this.canvas.width = this.container.clientWidth
    this.canvas.height = this.container.clientHeight
  }

  private _initParticles(): void {
    for (let i = 0; i < 60; i++) {
      this.particles.push(this._createParticle())
    }
  }

  private _createParticle() {
    return {
      x: Math.random() * 1200, y: Math.random() * 800,
      vx: (Math.random() - 0.5) * 0.5, vy: (Math.random() - 0.5) * 0.3,
      life: 0, maxLife: 200 + Math.random() * 300,
      size: 2 + Math.random() * 4,
      color: ['rgba(100,180,255,', 'rgba(160,100,255,', 'rgba(100,255,200,'][Math.floor(Math.random() * 3)],
    }
  }

  private _startLoop(): void {
    this.lastTime = performance.now()
    const loop = (now: number) => {
      const dt = Math.min((now - this.lastTime) / 1000, 0.05)
      this.lastTime = now
      this._update(dt)
      this._draw()
      this.animFrameId = requestAnimationFrame(loop)
    }
    this.animFrameId = requestAnimationFrame(loop)
  }

  private _update(dt: number): void {
    this._updateParticles(dt)
    if (this.state === "playing" && this.currentGame) {
      const poseData = this.poseDetector.detect()
      this.movementRules.update(poseData)
      this.currentGame.update(poseData, dt)
      this.progressAnim += dt * 0.5
      this._updateFeedback(poseData)
      const curScore = this.scoring.getTotal()
      if (curScore > this.lastScore) {
        const scoreGain = curScore - this.lastScore
        const w = this.canvas.width
        const h = this.canvas.height
        this._burstConfetti(w * 0.5 + (Math.random() - 0.5) * 200, h * 0.3, 20)
        this._showScoreFloat(w * 0.5 - 40, h * 0.3, `+${scoreGain}`, true)
      }
      this.lastScore = curScore
      if (this.currentGame.isFinished()) { this._onGameEnd(); return }
      this._checkPhaseChange()
    }
  }

  private _checkPhaseChange(): void {
    if (!this.currentGame || !this.phaseCheckGames.has(this.currentGame.name)) return
    const phase = (this.currentGame as unknown as Record<string, unknown>).phase as string | undefined
    if (phase && phase !== this.lastPhase) {
      this.lastPhase = phase
      this._rebuildGameArea()
    }
  }

  private _rebuildGameArea(): void {
    const oldArea = this.overlay.querySelector('.game-area')
    if (!oldArea || !this.currentGame) return
    const newArea = document.createElement('div')
    newArea.className = 'game-area'
    const g = this.currentGame
    if (g.name === 'memory_carte') this._renderMemoryCarteUI(newArea)
    else if (g.name === 'memory_immagini') this._renderMemoryImmaginiUI(newArea)
    else if (g.name === 'mappa_stanza') this._renderMappaUI(newArea)
    else if (g.name === 'cerca_parole') this._renderCercaParoleUI(newArea)
    oldArea.parentNode?.replaceChild(newArea, oldArea)
  }

  private _burstConfetti(cx: number, cy: number, count: number, colors?: string[]): void {
    const palette = colors ?? ['#64b4ff', '#a060ff', '#40d9a0', '#ff6b6b', '#ffd93d', '#ff8a65']
    for (let i = 0; i < count; i++) {
      const angle = Math.random() * Math.PI * 2
      const speed = 80 + Math.random() * 200
      this.confetti.push({
        x: cx, y: cy,
        vx: Math.cos(angle) * speed, vy: Math.sin(angle) * speed - 100,
        life: 0, maxLife: 60 + Math.random() * 80,
        size: 4 + Math.random() * 6,
        color: palette[Math.floor(Math.random() * palette.length)],
        rotation: Math.random() * Math.PI * 2,
        rotSpeed: (Math.random() - 0.5) * 10,
      })
    }
  }

  private _showScoreFloat(x: number, y: number, text: string, isGood: boolean): void {
    const el = document.createElement('div')
    el.className = `score-float${isGood ? '' : ' wrong'}`
    el.textContent = text
    el.style.left = `${x}px`
    el.style.top = `${y}px`
    document.body.appendChild(el)
    el.addEventListener('animationend', () => el.remove())
  }

  private _updateParticles(dt: number): void {
    for (const p of this.particles) {
      p.life += dt * 60
      p.x += p.vx; p.y += p.vy
      if (p.life > p.maxLife || p.x < -20 || p.x > 1240 || p.y < -20 || p.y > 820) Object.assign(p, this._createParticle())
    }
    for (let i = this.confetti.length - 1; i >= 0; i--) {
      const c = this.confetti[i]
      c.life++
      c.x += c.vx * dt
      c.y += c.vy * dt
      c.vy += 400 * dt
      c.rotation += c.rotSpeed * dt
      if (c.life > c.maxLife || c.y > 1200) { this.confetti.splice(i, 1); continue }
    }
  }

  private _lastFeedbackMsg = ''

  private _updateFeedback(poseData: PoseData | null): void {
    const fbEl = this.overlay.querySelector('.feedback-bar')
    if (fbEl && this.currentGame) {
      const msg = this.currentGame.feedbackMessage
      if (msg !== this._lastFeedbackMsg) {
        fbEl.textContent = msg
        const isCorrect = msg.includes('Perfetto') || msg.includes('Corretto') || msg.includes('corretta') || msg.includes('Giusto') || msg.includes('Bravo') || msg.includes('Ottimo') || msg.includes('giusto')
        const isWrong = msg.includes('sbagliato') || msg.includes('riprova') || msg.includes('Riprova') || msg.includes('Non preoccuparti') || msg.includes('attenzione') || msg.includes('sbagliata') || msg.includes('errore')
        fbEl.classList.remove('correct', 'wrong')
        if (isCorrect) fbEl.classList.add('correct')
        else if (isWrong) fbEl.classList.add('wrong')
      }
      this._lastFeedbackMsg = msg
    }
    this._updateWidgets(poseData)
  }

  private _updateWidgets(poseData: PoseData | null): void {
    if (this.currentGame) {
      const progress = this.currentGame.getProgress()
      const bar = this.overlay.querySelector('.progress-fill') as HTMLElement
      if (bar) bar.style.width = `${progress * 100}%`
    }
    const moodData = this.facialExpression.getMoodData()
    const moodEl = this.overlay.querySelector('.mood-label')
    if (moodEl) moodEl.textContent = moodData.mood
    const scoreEl = this.overlay.querySelector('.score-display')
    if (scoreEl) scoreEl.textContent = `Punti: ${this.scoring.getTotal()}`
  }

  private _draw(): void {
    const w = this.canvas.width, h = this.canvas.height
    if (!w || !h) return
    const ctx = this.ctx

    const gradient = ctx.createRadialGradient(w * 0.5, h * 0.5, 0, w * 0.5, h * 0.5, w * 0.8)
    gradient.addColorStop(0, '#0a0e27')
    gradient.addColorStop(0.5, '#0d1333')
    gradient.addColorStop(1, '#060918')
    ctx.fillStyle = gradient
    ctx.fillRect(0, 0, w, h)

    for (const p of this.particles) {
      const alpha = Math.sin((p.life / p.maxLife) * Math.PI) * 0.6
      ctx.beginPath()
      ctx.arc(p.x, p.y, p.size, 0, Math.PI * 2)
      ctx.fillStyle = `${p.color}${alpha})`
      ctx.fill()
    }

    for (const c of this.confetti) {
      const alpha = Math.min(1 - c.life / c.maxLife, 0.9)
      ctx.save()
      ctx.translate(c.x, c.y)
      ctx.rotate(c.rotation)
      ctx.fillStyle = c.color
      ctx.globalAlpha = alpha
      ctx.fillRect(-c.size / 2, -c.size / 2, c.size, c.size * 0.6)
      ctx.restore()
    }

    if (this.state === "playing" && this.currentGame) {
      this._drawGameContent(ctx, w, h)
    }
  }

  private _drawGameContent(ctx: CanvasRenderingContext2D, w: number, h: number): void {
    if (!this.currentGame) return
    const g = this.currentGame

    switch (g.name) {
      case "respiro_faro": this._drawRespiro(ctx, w, h); break
      case "passi_ricorda": this._drawPassiRicorda(ctx, w, h); break
      case "semaforo_esecutivo": this._drawSemaforo(ctx, w, h); break
      case "mappa_stanza": this._drawMappaStanza(ctx, w, h); break
      case "costruisci_modello": this._drawCostruisci(ctx, w, h); break
      case "diario_missioni": break
      case "memory_carte": this._drawMemoryCarte(ctx, w, h); break
      case "sequenza_simboli": this._drawSequenza(ctx, w, h); break
      case "parole_incrociate": break
      case "basket": this._drawBasket(ctx, w, h); break
      case "puzzle": this._drawPuzzle(ctx, w, h); break
      case "memory_immagini": this._drawMemoryImmagini(ctx, w, h); break
      case "brain_trainer": this._drawBrainTrainer(ctx, w, h); break
      case "musical_memory": this._drawMusicalMemory(ctx, w, h); break
      case "palloncini": this._drawPalloncini(ctx, w, h); break
      case "quiz": break
      case "cerca_parole": this._drawCercaParole(ctx, w, h); break
      case "valutazione": break
    }

    ctx.save()
    ctx.strokeStyle = 'rgba(100,180,255,0.15)'
    ctx.lineWidth = 1
    ctx.setLineDash([5, 5])
    ctx.strokeRect(20, 20, w - 40, h - 40)
    ctx.restore()
  }

  private _drawRespiro(ctx: CanvasRenderingContext2D, w: number, h: number): void {
    const faro = this.currentGame as import('../games/respiro-faro').RespiroFaro
    const cx = w / 2, cy = h / 2
    const maxR = Math.min(w, h) * 0.35
    const r = maxR * faro.getCircleScale()

    ctx.save()
    const glow = ctx.createRadialGradient(cx, cy, r * 0.5, cx, cy, r * 2)
    glow.addColorStop(0, 'rgba(100,180,255,0.3)')
    glow.addColorStop(0.5, 'rgba(100,180,255,0.1)')
    glow.addColorStop(1, 'rgba(100,180,255,0)')
    ctx.fillStyle = glow
    ctx.beginPath()
    ctx.arc(cx, cy, r * 2, 0, Math.PI * 2)
    ctx.fill()

    ctx.beginPath()
    ctx.arc(cx, cy, r, 0, Math.PI * 2)
    const grad = ctx.createRadialGradient(cx - r * 0.3, cy - r * 0.3, 0, cx, cy, r)
    grad.addColorStop(0, '#64b4ff')
    grad.addColorStop(0.5, '#3a7bd5')
    grad.addColorStop(1, '#1a3a6a')
    ctx.fillStyle = grad
    ctx.fill()

    ctx.strokeStyle = 'rgba(100,180,255,0.6)'
    ctx.lineWidth = 3
    ctx.stroke()

    for (let i = 0; i < 3; i++) {
      ctx.beginPath()
      ctx.arc(cx, cy, r + 10 + i * 8 + Math.sin(this.progressAnim * 2 + i) * 3, 0, Math.PI * 2)
      ctx.strokeStyle = `rgba(100,180,255,${0.2 - i * 0.05})`
      ctx.lineWidth = 1
      ctx.stroke()
    }

    ctx.fillStyle = 'white'
    ctx.font = 'bold 28px system-ui'
    ctx.textAlign = 'center'
    ctx.fillText(faro.phase === "inspira" ? "Inspira" : "Espira", cx, cy + 8)
    ctx.restore()
  }

  private _drawPassiRicorda(ctx: CanvasRenderingContext2D, w: number, h: number): void {
    const game = this.currentGame as import('../games/passi-ricorda').PassiRicorda
    ctx.save()
    if (game.phase === "showing") {
      const item = game.getCurrentItem()
      if (item) {
        ctx.fillStyle = 'white'
        ctx.font = '80px system-ui'
        ctx.textAlign = 'center'
        ctx.fillText(game.getItemIcon(item), w / 2, h / 2 + 30)
        ctx.font = 'bold 24px system-ui'
        ctx.fillText(item, w / 2, h / 2 + 120)
      }
    } else if (game.phase === "moving") {
      const elapsed = Math.min((Date.now() - game.movementTimer) / 8000, 1)
      ctx.fillStyle = 'white'
      ctx.font = 'bold 32px system-ui'
      ctx.textAlign = 'center'
      ctx.fillText("Cammina sul posto...", w / 2, h / 2 - 40)
      ctx.font = '28px system-ui'
      ctx.fillText(`${Math.ceil(8 - elapsed * 8)}s`, w / 2, h / 2 + 20)
      const cx = w / 2, cy = h / 2 + 60
      ctx.beginPath()
      ctx.arc(cx, cy, 40, 0, Math.PI * 2 * elapsed)
      ctx.strokeStyle = '#64b4ff'
      ctx.lineWidth = 4
      ctx.stroke()
      ctx.beginPath()
      ctx.arc(cx, cy, 40, 0, Math.PI * 2)
      ctx.strokeStyle = 'rgba(100,180,255,0.2)'
      ctx.lineWidth = 2
      ctx.stroke()
    } else if (game.phase === "recall" || game.phase === "feedback") {
      const answerLen = game.userAnswer.length
      const answerBoxesY = 40
      const boxSize = 50
      const totalBoxW = game.sequence.length * (boxSize + 8) - 8
      const boxStartX = (w - totalBoxW) / 2
      for (let i = 0; i < game.sequence.length; i++) {
        const bx = boxStartX + i * (boxSize + 8)
        ctx.fillStyle = i < answerLen
          ? (game.getItemResult(i) === 'correct' ? 'rgba(60,200,60,0.35)' : 'rgba(220,60,60,0.35)')
          : 'rgba(255,255,255,0.08)'
        ctx.beginPath()
        ctx.roundRect(bx, answerBoxesY, boxSize, boxSize, 8)
        ctx.fill()
        if (i < answerLen) {
          const borderColor = game.getItemResult(i) === 'correct' ? '#3cc83c' : '#dc3c3c'
          ctx.strokeStyle = borderColor
          ctx.lineWidth = 2
          ctx.stroke()
          ctx.fillStyle = 'white'
          ctx.font = '24px system-ui'
          ctx.textAlign = 'center'
          ctx.fillText(game.getItemIcon(game.userAnswer[i]), bx + boxSize / 2, answerBoxesY + boxSize / 2 + 8)
        }
      }

      const opts = game.getOptions()
      const selectedSet = new Set(game.userAnswer)
      const cols = 4
      const size = Math.min(80, (w - 80) / cols - 16)
      const startX = (w - cols * (size + 16)) / 2
      const startY = answerBoxesY + boxSize + 40
      opts.forEach((opt, i) => {
        const col = i % cols, row = Math.floor(i / cols)
        const x = startX + col * (size + 16)
        const y = startY + row * (size + 16)
        const isUsed = selectedSet.has(opt) && !game.userAnswer.slice(answerLen - 1).includes(opt)
        ctx.fillStyle = isUsed ? 'rgba(60,60,60,0.6)' : 'rgba(20,30,60,0.8)'
        ctx.beginPath()
        ctx.roundRect(x, y, size, size, 12)
        ctx.fill()
        ctx.strokeStyle = isUsed ? 'rgba(100,100,100,0.3)' : 'rgba(100,180,255,0.4)'
        ctx.lineWidth = 1
        ctx.stroke()
        ctx.fillStyle = isUsed ? '#666' : 'white'
        ctx.font = '32px system-ui'
        ctx.textAlign = 'center'
        ctx.fillText(game.getItemIcon(opt), x + size / 2, y + size / 2 + 12)
      })
    }
    ctx.restore()
  }

  private _drawSemaforo(ctx: CanvasRenderingContext2D, w: number, h: number): void {
    const game = this.currentGame as import('../games/semaforo-esecutivo').SemaforoEsecutivo
    ctx.save()
    const color = game.getColorDisplay()
    if (color) {
      const colorMap: Record<string, string> = { rosso: '#e63c3c', giallo: '#e6d232', verde: '#3cc83c', blu: '#3282e6' }
      const arrowMap: Record<string, string> = { passo_avanti: '\u2191', fermo: '\u270B', passo_sinistra: '\u2190', passo_destra: '\u2192' }
      const col = game.getCurrentColor() ?? ''
      const action = color.action
      const arrow = arrowMap[action] ?? '?'

      ctx.beginPath()
      ctx.arc(w / 2, h / 2 - 30, 90, 0, Math.PI * 2)
      ctx.fillStyle = colorMap[col] ?? '#555'
      ctx.fill()
      ctx.shadowColor = colorMap[col] ?? '#555'
      ctx.shadowBlur = 40
      ctx.fill()
      ctx.shadowBlur = 0

      ctx.fillStyle = 'white'
      ctx.font = '64px system-ui'
      ctx.textAlign = 'center'
      ctx.textBaseline = 'middle'
      ctx.fillText(arrow, w / 2, h / 2 - 30)

      ctx.fillStyle = 'rgba(255,255,255,0.9)'
      ctx.font = 'bold 22px system-ui'
      ctx.textBaseline = 'alphabetic'
      ctx.fillText(color.label, w / 2, h / 2 + 80)

      if (action === 'fermo') {
        ctx.fillStyle = '#ff4444'
        ctx.font = 'bold 36px system-ui'
        ctx.textBaseline = 'alphabetic'
        ctx.fillText('STOP', w / 2, h / 2 + 125)
      }

      if (game.inhibitionMode) {
        ctx.fillStyle = '#ff6b6b'
        ctx.font = 'bold 20px system-ui'
        ctx.fillText("REGOLA SPECIALE: Resta fermo!", w / 2, h / 2 + 165)
      }
    }
    ctx.restore()
  }

  private _drawMappaStanza(ctx: CanvasRenderingContext2D, w: number, h: number): void {
    const game = this.currentGame as import('../games/mappa-stanza').MappaStanza
    ctx.save()
    const gs = game.gridSize
    const cellSize = Math.min(80, (w - 100) / gs)
    const startX = (w - gs * cellSize) / 2
    const startY = (h - gs * cellSize) / 2
    for (let r = 0; r < gs; r++) {
      for (let c = 0; c < gs; c++) {
        const x = startX + c * cellSize, y = startY + r * cellSize
        ctx.fillStyle = 'rgba(20,30,60,0.7)'
        ctx.beginPath()
        ctx.roundRect(x, y, cellSize - 4, cellSize - 4, 8)
        ctx.fill()
        ctx.strokeStyle = 'rgba(100,180,255,0.2)'
        ctx.lineWidth = 1
        ctx.stroke()
        if (game.phase === "showing") {
          for (const [obj, pos] of Object.entries(game.objectPositions)) {
            if (pos[0] === r && pos[1] === c) {
              ctx.fillStyle = 'white'
              ctx.font = '28px system-ui'
              ctx.textAlign = 'center'
              ctx.fillText(game.getObjectIcon(obj), x + cellSize / 2, y + cellSize / 2 + 10)
            }
          }
        }
      }
    }
    ctx.restore()
  }

  private _drawCostruisci(ctx: CanvasRenderingContext2D, w: number, h: number): void {
    const game = this.currentGame as import('../games/costruisci-modello').CostruisciModello
    ctx.save()
    if (game.phase === "showing") {
      const preview = game.getModelPreview()
      const size = Math.min(70, (w - 80) / Math.max(preview.length, 1) - 16)
      const startX = (w - preview.length * (size + 16)) / 2
      preview.forEach((piece, i) => {
        const info = game.getShapeInfo(piece)
        if (!info) return
        const x = startX + i * (size + 16), y = h / 2 - size / 2
        ctx.fillStyle = info.color + '40'
        ctx.beginPath()
        ctx.roundRect(x, y, size, size, 10)
        ctx.fill()
        ctx.strokeStyle = info.color
        ctx.lineWidth = 2
        ctx.stroke()
        ctx.fillStyle = 'white'
        ctx.font = '14px system-ui'
        ctx.textAlign = 'center'
        ctx.fillText(info.label, x + size / 2, y + size + 24)
      })
    }
    ctx.restore()
  }

  private _drawMemoryCarte(ctx: CanvasRenderingContext2D, w: number, h: number): void {
    const game = this.currentGame as import('../games/memory-carte').MemoryCarte
    ctx.save()
    const [rows, cols] = game.getGridSize()
    const size = Math.min(70, (w - 80) / cols - 8)
    const startX = (w - cols * (size + 8)) / 2
    const startY = (h - rows * (size + 8)) / 2
    for (let r = 0; r < rows; r++) {
      for (let c = 0; c < cols; c++) {
        const idx = r * cols + c
        const x = startX + c * (size + 8), y = startY + r * (size + 8)
        if (game.isCardMatched(idx)) {
          ctx.fillStyle = 'rgba(60,200,60,0.2)'
        } else if (game.isCardRevealed(idx)) {
          ctx.fillStyle = 'rgba(40,60,100,0.9)'
        } else {
          ctx.fillStyle = 'rgba(20,30,60,0.8)'
        }
        ctx.beginPath()
        ctx.roundRect(x, y, size, size, 8)
        ctx.fill()
        if (game.isCardRevealed(idx) || game.isCardMatched(idx)) {
          ctx.fillStyle = 'white'
          ctx.font = '30px system-ui'
          ctx.textAlign = 'center'
          ctx.fillText(game.getCardSymbol(idx), x + size / 2, y + size / 2 + 10)
        } else {
          ctx.fillStyle = 'rgba(100,180,255,0.3)'
          ctx.font = '24px system-ui'
          ctx.textAlign = 'center'
          ctx.fillText('?', x + size / 2, y + size / 2 + 8)
        }
      }
    }
    ctx.restore()
  }

  private _drawSequenza(ctx: CanvasRenderingContext2D, w: number, h: number): void {
    const game = this.currentGame as import('../games/sequenza-simboli').SequenzaSimboli
    ctx.save()
    if (game.phase === "showing") {
      const item = game.getCurrentShowItem()
      if (item) {
        ctx.fillStyle = 'white'
        ctx.font = '80px system-ui'
        ctx.textAlign = 'center'
        ctx.fillText(item, w / 2, h / 2 + 30)
      }
    } else {
      const symbols = game.getAvailableSymbols()
      const size = Math.min(70, (w - 80) / Math.max(symbols.length, 1) - 16)
      const startX = (w - symbols.length * (size + 16)) / 2
      symbols.forEach(([, icon], i) => {
        const x = startX + i * (size + 16), y = h / 2 - size / 2
        ctx.fillStyle = 'rgba(20,30,60,0.8)'
        ctx.beginPath()
        ctx.roundRect(x, y, size, size, 12)
        ctx.fill()
        ctx.fillStyle = 'white'
        ctx.font = '32px system-ui'
        ctx.textAlign = 'center'
        ctx.fillText(icon, x + size / 2, y + size / 2 + 12)
      })
    }
    ctx.restore()
  }

  private _drawBasket(ctx: CanvasRenderingContext2D, w: number, h: number): void {
    const game = this.currentGame as import('../games/basket').Basket
    ctx.save()
    const [hx, hy, hr] = game.getHoopPos()
    const hoopX = hx * w, hoopY = hy * h
    ctx.strokeStyle = '#ff6b35'
    ctx.lineWidth = 4
    ctx.beginPath()
    ctx.ellipse(hoopX, hoopY, hr + 10, hr / 2, 0, 0, Math.PI * 2)
    ctx.stroke()
    ctx.fillStyle = 'rgba(255,107,53,0.1)'
    ctx.fill()
    const ballPos = game.getBallPos()
    if (ballPos) {
      const trail = game.getBallTrail()
      trail.forEach((p, i) => {
        const alpha = i / trail.length
        ctx.beginPath()
        ctx.arc(p[0], p[1], 5 + alpha * 5, 0, Math.PI * 2)
        ctx.fillStyle = `rgba(255,150,50,${alpha * 0.5})`
        ctx.fill()
      })
      ctx.beginPath()
      ctx.arc(ballPos[0], ballPos[1], 18, 0, Math.PI * 2)
      ctx.fillStyle = '#ff9632'
      ctx.fill()
      ctx.strokeStyle = '#cc6a1a'
      ctx.lineWidth = 2
      ctx.stroke()
    }
    ctx.fillStyle = 'white'
    ctx.font = '24px system-ui'
    ctx.textAlign = 'center'
    ctx.fillText(`Mano: ${game.throwHand === 'right' ? 'DESTRA' : 'SINISTRA'}`, w / 2, 40)
    ctx.restore()
  }

  private _drawPuzzle(ctx: CanvasRenderingContext2D, w: number, h: number): void {
    const game = this.currentGame as import('../games/puzzle').Puzzle
    ctx.save()
    const gs = game.gridSize
    const size = Math.min(70, (w - 80) / gs)
    const startX = (w - gs * size) / 2
    const startY = (h - gs * size) / 2
    for (let r = 0; r < gs; r++) {
      for (let c = 0; c < gs; c++) {
        const x = startX + c * size, y = startY + r * size
        if (game.isSelected(r, c)) {
          ctx.fillStyle = 'rgba(100,180,255,0.3)'
        } else if (game.currentGrid[r]?.[c] === game.targetGrid[r]?.[c]) {
          ctx.fillStyle = 'rgba(60,200,60,0.15)'
        } else {
          ctx.fillStyle = 'rgba(20,30,60,0.8)'
        }
        ctx.beginPath()
        ctx.roundRect(x, y, size - 4, size - 4, 8)
        ctx.fill()
        ctx.strokeStyle = game.isSelected(r, c) ? 'rgba(100,180,255,0.6)' : 'rgba(100,180,255,0.15)'
        ctx.lineWidth = game.isSelected(r, c) ? 2 : 1
        ctx.stroke()
        ctx.fillStyle = 'white'
        ctx.font = '28px system-ui'
        ctx.textAlign = 'center'
        ctx.fillText(game.currentGrid[r]?.[c] ?? '', x + size / 2, y + size / 2 + 10)
      }
    }
    ctx.restore()
  }

  private _drawMemoryImmagini(ctx: CanvasRenderingContext2D, w: number, h: number): void {
    const game = this.currentGame as import('../games/memory-immagini').MemoryImmagini
    ctx.save()
    if (game.phase === "instruction") {
      ctx.fillStyle = 'white'
      ctx.font = 'bold 28px system-ui'
      ctx.textAlign = 'center'
      ctx.fillText("Preparati a memorizzare le immagini!", w / 2, h / 2 - 40)
      ctx.font = '20px system-ui'
      ctx.fillStyle = 'var(--accent,#64b4ff)'
      ctx.fillText("Tra poco tutte le carte saranno visibili", w / 2, h / 2 + 10)
      ctx.restore()
      return
    }
    if (game.phase === "study") {
      const elapsed = Math.min((Date.now() - game.studyTimer) / 1000, game.studyDuration)
      const remaining = Math.ceil(game.studyDuration - elapsed)
      ctx.fillStyle = 'rgba(100,180,255,0.8)'
      ctx.font = 'bold 22px system-ui'
      ctx.textAlign = 'center'
      ctx.fillText(`Memorizza... ${remaining}s`, w / 2, 40)
    }
    const [rows, cols] = game.getGridSize()
    const size = Math.min(64, (w - 60) / cols - 6)
    const startX = (w - cols * (size + 6)) / 2
    const startY = Math.max(game.phase === "study" ? 60 : 20, (h - rows * (size + 6)) / 2)
    for (let r = 0; r < rows; r++) {
      for (let c = 0; c < cols; c++) {
        const idx = r * cols + c
        const x = startX + c * (size + 6), y = startY + r * (size + 6)
        const wrong = game.isCardWrong(idx)
        if (game.isCardMatched(idx)) {
          ctx.fillStyle = 'rgba(60,200,60,0.25)'
        } else if (wrong) {
          ctx.fillStyle = 'rgba(220,60,60,0.35)'
        } else if (game.isCardRevealed(idx)) {
          ctx.fillStyle = 'rgba(40,60,100,0.9)'
        } else {
          ctx.fillStyle = 'rgba(20,30,60,0.8)'
        }
        ctx.beginPath()
        ctx.roundRect(x, y, size, size, 8)
        ctx.fill()
        if (wrong) {
          ctx.strokeStyle = '#ff4444'
          ctx.lineWidth = 2
          ctx.stroke()
        }
        if (game.isCardRevealed(idx) || game.isCardMatched(idx)) {
          ctx.fillStyle = 'white'
          ctx.font = `${Math.min(28, size - 8)}px system-ui`
          ctx.textAlign = 'center'
          ctx.fillText(game.getCardIcon(idx), x + size / 2, y + size / 2 + 8)
        } else {
          ctx.fillStyle = 'rgba(100,180,255,0.3)'
          ctx.font = `${Math.min(22, size - 8)}px system-ui`
          ctx.textAlign = 'center'
          ctx.fillText('?', x + size / 2, y + size / 2 + 6)
        }
      }
    }
    ctx.restore()
  }

  private _drawBrainTrainer(ctx: CanvasRenderingContext2D, w: number, h: number): void {
    const game = this.currentGame as import('../games/brain-trainer').BrainTrainer
    ctx.save()
    const q = game.getCurrentQuestion()
    if (!q || game.phase !== "playing") return
    ctx.fillStyle = 'white'
    ctx.font = 'bold 28px system-ui'
    ctx.textAlign = 'center'
    ctx.fillText(q.text as string, w / 2, h / 2 - 80)
    if (q.type === "count" && q.symbols) {
      const symbols = q.symbols as string[]
      const sChar = q.symbolChar as string
      const cols = Math.min(6, symbols.length)
      const startX = (w - cols * 50) / 2
      symbols.forEach((_, i) => {
        ctx.font = '36px system-ui'
        ctx.textAlign = 'center'
        ctx.fillText(sChar, startX + (i % cols) * 50, h / 2 - 20 + Math.floor(i / cols) * 50)
      })
    }
    if (q.type === "recall" && q.items) {
      const items = q.items as string[]
      const hl = q.highlight as string
      const startX = (w - items.length * 60) / 2
      items.forEach((item: string, i: number) => {
        ctx.font = item === hl ? '44px system-ui' : '36px system-ui'
        ctx.textAlign = 'center'
        if (item === hl) {
          ctx.beginPath()
          ctx.arc(startX + i * 60 + 30, h / 2 - 10, 30, 0, Math.PI * 2)
          ctx.fillStyle = 'rgba(255,200,50,0.2)'
          ctx.fill()
        }
        ctx.fillStyle = item === hl ? '#ffc832' : 'white'
        ctx.fillText(item, startX + i * 60 + 30, h / 2 + 12)
      })
    }
    ctx.restore()
  }

  private _drawMusicalMemory(ctx: CanvasRenderingContext2D, w: number, h: number): void {
    const game = this.currentGame as import('../games/musical-memory').MusicalMemory
    ctx.save()
    const notes = [
      { label: "Do", color: "#e63c3c" },
      { label: "Mi", color: "#3c82e6" },
      { label: "Sol", color: "#3cc83c" },
      { label: "Do'", color: "#e6d232" },
    ]
    const radius = 50
    const totalW = notes.length * (radius * 2 + 20) - 20
    const startX = (w - totalW) / 2 + radius
    const y = h / 2
    const flash = game.getFlashNote()
    notes.forEach((note, i) => {
      const x = startX + i * (radius * 2 + 20)
      ctx.beginPath()
      ctx.arc(x, y, radius, 0, Math.PI * 2)
      if (flash === i) {
        ctx.fillStyle = note.color
        ctx.shadowColor = note.color
        ctx.shadowBlur = 30
      } else {
        ctx.fillStyle = note.color + '60'
        ctx.shadowBlur = 0
      }
      ctx.fill()
      ctx.shadowBlur = 0
      ctx.fillStyle = 'white'
      ctx.font = 'bold 20px system-ui'
      ctx.textAlign = 'center'
      ctx.fillText(note.label, x, y + 7)
    })
    ctx.restore()
  }

  private _drawCercaParole(ctx: CanvasRenderingContext2D, w: number, h: number): void {
    const game = this.currentGame as import('../games/cerca-parole').CercaParole
    ctx.save()
    const gs = game.getGridSize()
    const cellSize = Math.min(36, (w - 60) / gs, (h - 80) / gs)
    const startX = (w - gs * cellSize) / 2
    const startY = (h - gs * cellSize) / 2 + 10
    for (let r = 0; r < gs; r++) {
      for (let c = 0; c < gs; c++) {
        const x = startX + c * cellSize
        const y = startY + r * cellSize
        if (game.isFound(r, c)) {
          ctx.fillStyle = 'rgba(60,200,60,0.2)'
        } else if (game.isSelected(r, c)) {
          ctx.fillStyle = 'rgba(100,180,255,0.3)'
        } else {
          ctx.fillStyle = 'rgba(20,30,60,0.7)'
        }
        ctx.beginPath()
        ctx.roundRect(x, y, cellSize - 2, cellSize - 2, 4)
        ctx.fill()
        if (game.isFound(r, c)) {
          ctx.strokeStyle = 'rgba(60,200,60,0.5)'
          ctx.lineWidth = 1
          ctx.stroke()
        }
        ctx.fillStyle = game.isFound(r, c) ? '#80d880' : '#eee'
        ctx.font = `${Math.max(12, cellSize - 10)}px system-ui`
        ctx.textAlign = 'center'
        ctx.textBaseline = 'middle'
        ctx.fillText(game.grid[r][c], x + cellSize / 2, y + cellSize / 2)
      }
    }
    ctx.restore()
  }

  private _drawPalloncini(ctx: CanvasRenderingContext2D, w: number, h: number): void {
    const game = this.currentGame as import('../games/palloncini').Palloncini
    ctx.save()

    if (game.phase === "instruction") {
      ctx.fillStyle = 'white'
      ctx.font = 'bold 30px system-ui'
      ctx.textAlign = 'center'
      ctx.textBaseline = 'middle'
      ctx.fillText("Scoppia i palloncini!", w / 2, h / 2 - 30)
      ctx.fillStyle = '#64b4ff'
      ctx.font = '20px system-ui'
      ctx.fillText("Clicca sui palloncini per scoppiarli", w / 2, h / 2 + 15)
      ctx.restore()
      return
    }

    for (const b of game.balloons) {
      const r = b.radius
      const bw = r * 1.6
      const bh = r * 2.4
      const wobX = Math.sin(b.wobbleT * 1.5) * 3
      const cx = b.x + wobX
      const cy = b.y
      const topY = cy - bh * 0.45
      const botY = cy + bh * 0.45

      // glow
      ctx.beginPath()
      ctx.arc(cx, cy, r * 1.1, 0, Math.PI * 2)
      ctx.fillStyle = b.color + '20'
      ctx.fill()

      // balloon teardrop shape
      ctx.beginPath()
      ctx.moveTo(cx, topY)
      ctx.bezierCurveTo(cx + bw * 0.45, topY, cx + bw * 0.7, cy - bh * 0.1, cx + bw * 0.6, cy)
      ctx.bezierCurveTo(cx + bw * 0.52, cy + bh * 0.15, cx + bw * 0.2, botY - bh * 0.05, cx, botY)
      ctx.bezierCurveTo(cx - bw * 0.2, botY - bh * 0.05, cx - bw * 0.52, cy + bh * 0.15, cx - bw * 0.6, cy)
      ctx.bezierCurveTo(cx - bw * 0.7, cy - bh * 0.1, cx - bw * 0.45, topY, cx, topY)
      ctx.closePath()

      // gradient fill
      const grad = ctx.createRadialGradient(cx - bw * 0.15, cy - bh * 0.15, 0, cx, cy, bw * 0.6)
      grad.addColorStop(0, '#ffffff')
      grad.addColorStop(0.15, b.color)
      grad.addColorStop(0.7, b.color)
      grad.addColorStop(1, '#000000')
      ctx.fillStyle = grad
      ctx.fill()

      // inner glow / highlight overlay
      ctx.beginPath()
      ctx.moveTo(cx, topY + bh * 0.08)
      ctx.bezierCurveTo(cx + bw * 0.25, topY + bh * 0.1, cx + bw * 0.35, cy - bh * 0.05, cx + bw * 0.3, cy - bh * 0.1)
      ctx.bezierCurveTo(cx + bw * 0.2, cy - bh * 0.2, cx - bw * 0.15, cy - bh * 0.2, cx - bw * 0.25, cy - bh * 0.1)
      ctx.bezierCurveTo(cx - bw * 0.3, cy - bh * 0.05, cx - bw * 0.2, topY + bh * 0.1, cx, topY + bh * 0.08)
      ctx.closePath()
      ctx.fillStyle = 'rgba(255,255,255,0.15)'
      ctx.fill()

      // specular highlight 1 (upper left)
      ctx.save()
      ctx.beginPath()
      ctx.ellipse(cx - bw * 0.2, cy - bh * 0.2, bw * 0.12, bh * 0.08, -0.4, 0, Math.PI * 2)
      ctx.fillStyle = 'rgba(255,255,255,0.5)'
      ctx.fill()

      // specular highlight 2 (upper right, smaller)
      ctx.beginPath()
      ctx.ellipse(cx + bw * 0.15, cy - bh * 0.25, bw * 0.06, bh * 0.04, 0.3, 0, Math.PI * 2)
      ctx.fillStyle = 'rgba(255,255,255,0.25)'
      ctx.fill()
      ctx.restore()

      // knot
      const knotY = botY + 2
      ctx.beginPath()
      ctx.moveTo(cx - 5, knotY)
      ctx.lineTo(cx + 5, knotY)
      ctx.lineTo(cx + 3, knotY + 7)
      ctx.lineTo(cx - 3, knotY + 7)
      ctx.closePath()
      ctx.fillStyle = b.color
      ctx.fill()
      ctx.strokeStyle = b.color
      ctx.lineWidth = 1
      ctx.stroke()

      // string
      const stringEnd = knotY + 26
      ctx.beginPath()
      ctx.moveTo(cx, knotY + 5)
      const sway = Math.sin(b.wobbleT * 2.5) * 8
      ctx.quadraticCurveTo(cx - 8 + sway, knotY + 12, cx - 3 + sway * 0.6, stringEnd)
      ctx.strokeStyle = 'rgba(200,200,200,0.35)'
      ctx.lineWidth = 1.5
      ctx.stroke()
    }

    ctx.restore()
  }

  private _renderMenu(): void {
    this.state = "menu"
    this.currentGame = null
    this.overlay.innerHTML = ''
    const h = this.container.clientHeight

    const header = document.createElement('div')
    header.className = 'menu-header'
    header.innerHTML = `<div class="logo-icon">\u{1F9E0}</div>
      <h1>Brain-Move</h1>
      <p>Piattaforma di stimolazione cognitiva e motoria</p>`
    this.overlay.appendChild(header)

    const grid = document.createElement('div')
    grid.className = 'game-grid'

    GAME_MENU_DATA.forEach((g, i) => {
      if (g.name === 'valutazione') return
      const card = document.createElement('div')
      card.className = 'game-card'
      card.innerHTML = `
        <div class="card-icon">${g.icon}</div>
        <div class="card-title">${g.displayName}</div>
        <div class="card-desc">${g.description}</div>
        <div class="card-cog">${g.cognitive}</div>`
      card.addEventListener('click', () => this._startGame(i))
      grid.appendChild(card)
    })
    this.overlay.appendChild(grid)

    const bottomRow = document.createElement('div')
    bottomRow.className = 'bottom-actions'

    const sessionBtn = document.createElement('button')
    sessionBtn.className = 'btn btn-primary btn-session'
    sessionBtn.textContent = 'Sessione Completa (6 giochi)'
    sessionBtn.addEventListener('click', () => this._startSession())
    bottomRow.appendChild(sessionBtn)

    const reportBtn = document.createElement('button')
    reportBtn.className = 'btn btn-secondary'
    reportBtn.textContent = 'Report Sessioni'
    reportBtn.addEventListener('click', () => this._showReport())
    bottomRow.appendChild(reportBtn)

    this.overlay.appendChild(bottomRow)

    const scoreBadge = document.createElement('div')
    scoreBadge.className = 'score-badge'
    scoreBadge.textContent = `Punti: ${this.scoring.getTotal()}`
    this.overlay.appendChild(scoreBadge)
  }

  private _startGame(index: number): void {
    this.sessionMode = false
    this.gameIndex = index
    this.currentGame = this.games[index]
    this.session.currentGame = this.currentGame.name
    this.currentGame.start()
    this.state = "playing"
    this.progressAnim = 0
    this.lastScore = 0
    this.lastPhase = (this.currentGame as unknown as Record<string, unknown>).phase as string ?? null
    this._renderGameUI()
  }

  private _startSession(): void {
    this.sessionMode = true
    this.scoring.reset()
    this.lastScore = 0
    this.difficulty = new Difficulty()
    this.games.forEach(g => { g.running = false; g.state = "idle" })
    this.games = createAllGames(this.difficulty, this.scoring)
    this.session = new Session(this.profile, this.scoring, this.difficulty, this.safety)
    this.session.start()
    this.gameIndex = 0
    this.currentGame = this.games[0]
    this.session.currentGame = this.currentGame.name
    this.currentGame.start()
    this.state = "playing"
    this.progressAnim = 0
    this._renderGameUI()
  }

  private _renderGameUI(): void {
    const g = this.currentGame
    if (!g) return
    this.overlay.innerHTML = ''

    const topBar = document.createElement('div')
    topBar.className = 'game-top-bar'
    topBar.innerHTML = `
      <button class="btn btn-back" id="btn-back">← Torna al Menu</button>
      <div class="game-title-display">${g.displayName}</div>
      <div class="score-display">Punti: ${this.scoring.getTotal()}</div>`
    this.overlay.appendChild(topBar)

    const feedback = document.createElement('div')
    feedback.className = 'feedback-bar'
    feedback.textContent = g.feedbackMessage
    this.overlay.appendChild(feedback)

    const progressContainer = document.createElement('div')
    progressContainer.className = 'progress-container'
    progressContainer.innerHTML = '<div class="progress-fill" style="width:0%"></div>'
    this.overlay.appendChild(progressContainer)

    const gameArea = document.createElement('div')
    gameArea.className = 'game-area'

    if (g.name === 'diario_missioni') this._renderDiarioUI(gameArea)
    else if (g.name === 'parole_incrociate') this._renderParoleUI(gameArea)
    else if (g.name === 'quiz') this._renderQuizUI(gameArea)
    else if (g.name === 'valutazione') this._renderValutazioneUI(gameArea)
    else if (g.name === 'passi_ricorda') this._renderPassiRicordaUI(gameArea)
    else if (g.name === 'brain_trainer') this._renderBrainTrainerUI(gameArea)
    else if (g.name === 'costruisci_modello') this._renderCostruisciUI(gameArea)
    else if (g.name === 'mappa_stanza') this._renderMappaUI(gameArea)
    else if (g.name === 'musical_memory') this._renderMusicalUI(gameArea)
    else if (g.name === 'memory_carte') this._renderMemoryCarteUI(gameArea)
    else if (g.name === 'memory_immagini') this._renderMemoryImmaginiUI(gameArea)
    else if (g.name === 'puzzle') this._renderPuzzleUI(gameArea)
    else if (g.name === 'sequenza_simboli') this._renderSequenzaUI(gameArea)
    else if (g.name === 'basket') this._renderBasketUI(gameArea)
    else if (g.name === 'palloncini') this._renderPallonciniUI(gameArea)
    else if (g.name === 'semaforo_esecutivo') this._renderSemaforoUI(gameArea)
    else if (g.name === 'cerca_parole') this._renderCercaParoleUI(gameArea)

    this.overlay.appendChild(gameArea)

    document.getElementById('btn-back')?.addEventListener('click', () => this._backToMenu())
  }

  private _renderDiarioUI(area: HTMLElement): void {
    const game = this.currentGame as import('../games/diario-missioni').DiarioMissioni
    const container = document.createElement('div')
    container.className = 'diario-container'
    const render = () => {
      container.innerHTML = ''
      if (game.phase === "questions") {
        const q = game.getCurrentQuestion()
        if (q) {
          const qEl = document.createElement('div')
          qEl.className = 'diario-question'
          qEl.textContent = q
          container.appendChild(qEl)
          const options = ["Molto", "Abbastanza", "Poco"]
          options.forEach(o => {
            const btn = document.createElement('button')
            btn.className = 'btn btn-option'
            btn.textContent = o
            btn.addEventListener('click', () => { game.answerQuestion(o); render() })
            container.appendChild(btn)
          })
        }
      } else if (game.phase === "caregiver") {
        const title = document.createElement('div')
        title.className = 'diario-title'
        title.textContent = 'Osservazioni Caregiver'
        container.appendChild(title)
        game.getCaregiverOptions().forEach(n => {
          const btn = document.createElement('button')
          btn.className = `btn btn-option ${game.caregiverNotes.includes(n) ? 'selected' : ''}`
          btn.textContent = game.getCaregiverLabel(n)
          btn.addEventListener('click', () => {
            game.caregiverNotes.includes(n) ? game.removeCaregiverNote(n) : game.addCaregiverNote(n)
            render()
          })
          container.appendChild(btn)
        })
        const completeBtn = document.createElement('button')
        completeBtn.className = 'btn btn-primary'
        completeBtn.textContent = 'Completa Sessione'
        completeBtn.addEventListener('click', () => { game.complete() })
        container.appendChild(completeBtn)
      }
    }
    render()
    area.appendChild(container)
  }

  private _renderParoleUI(area: HTMLElement): void {
    const game = this.currentGame as import('../games/parole-incrociate').ParoleIncrociate
    const container = document.createElement('div')
    container.className = 'parole-container'
    const renderGrid = () => {
      container.innerHTML = ''
      const gs = game.gridSize
      const gridEl = document.createElement('div')
      gridEl.className = 'parole-grid'
      gridEl.style.gridTemplateColumns = `repeat(${gs}, 48px)`
      const display = game.getGrid()
      for (let r = 0; r < gs; r++) {
        for (let c = 0; c < gs; c++) {
          const cell = document.createElement('div')
          cell.className = 'parole-cell'
          cell.textContent = display[r][c] || ''
          if (display[r][c]) cell.classList.add('filled')
          cell.addEventListener('click', () => game.selectCell(r, c))
          gridEl.appendChild(cell)
        }
      }
      container.appendChild(gridEl)
      const hints = game.getHints()
      const hintsEl = document.createElement('div')
      hintsEl.className = 'parole-hints'
      hintsEl.innerHTML = hints.map(h => `<div>${h}</div>`).join('')
      container.appendChild(hintsEl)
      const inputRow = document.createElement('div')
      inputRow.className = 'parole-input-row'
      const input = document.createElement('input')
      input.type = 'text'
      input.maxLength = 1
      input.placeholder = 'Lettera'
      input.className = 'parole-input'
      input.addEventListener('input', () => {
        if (input.value) { game.setCellLetter(input.value); input.value = ''; renderGrid() }
      })
      inputRow.appendChild(input)
      const checkBtn = document.createElement('button')
      checkBtn.className = 'btn btn-primary'
      checkBtn.textContent = 'Verifica'
      checkBtn.addEventListener('click', () => { game.checkWord(); renderGrid() })
      inputRow.appendChild(checkBtn)
      container.appendChild(inputRow)
    }
    renderGrid()
    area.appendChild(container)
  }

  private _renderQuizUI(area: HTMLElement): void {
    const game = this.currentGame as import('../games/quiz').Quiz
    const container = document.createElement('div')
    container.className = 'quiz-container'
    const render = () => {
      container.innerHTML = ''
      const q = game.getCurrentQuestion()
      if (!q) return
      const qEl = document.createElement('div')
      qEl.className = 'quiz-question'
      qEl.textContent = q.q
      container.appendChild(qEl)
      q.opts.forEach((opt, i) => {
        const btn = document.createElement('button')
        btn.className = 'btn btn-option'
        btn.textContent = opt
        btn.addEventListener('click', () => { game.selectAnswer(i); render() })
        container.appendChild(btn)
      })
    }
    render()
    area.appendChild(container)
  }

  private _renderValutazioneUI(area: HTMLElement): void {
    const game = this.currentGame as import('../games/valutazione').Valutazione
    const container = document.createElement('div')
    container.className = 'valutazione-container'
    const render = () => {
      container.innerHTML = ''
      if (game.phase === "info") {
        container.innerHTML = '<div class="val-info">Test di valutazione completo. Rispondi a tutte le domande.</div>'
      } else if (game.phase === "result") {
        container.innerHTML = `<div class="val-result">
          <h2>Risultato</h2>
          <p>Punteggio: ${game.totalScore}/${game.maxScore}</p>
          <p>${game.result.descrizione ?? ''}</p>
        </div>`
      } else if (game.step === "caregiver") {
        const q = game.getCurrentCaregiver()
        if (q) {
          const qEl = document.createElement('div')
          qEl.className = 'val-question'
          qEl.textContent = q.q
          container.appendChild(qEl)
          ;[true, false].forEach(v => {
            const btn = document.createElement('button')
            btn.className = 'btn btn-option'
            btn.textContent = v ? 'Sì' : 'No'
            btn.addEventListener('click', () => { game.answerCaregiver(v); render() })
            container.appendChild(btn)
          })
        }
      } else if (game.step === "cognitivo") {
        const q = game.getCurrentCognitivo()
        if (q) {
          const qEl = document.createElement('div')
          qEl.className = 'val-question'
          qEl.textContent = q.q
          container.appendChild(qEl)
          q.opts.forEach((_, i) => {
            const btn = document.createElement('button')
            btn.className = 'btn btn-option'
            btn.textContent = q.opts[i]
            btn.addEventListener('click', () => { game.answerCognitivo(i); render() })
            container.appendChild(btn)
          })
        }
      }
    }
    render()
    area.appendChild(container)
  }

  private _renderPassiRicordaUI(area: HTMLElement): void {
    const game = this.currentGame as import('../games/passi-ricorda').PassiRicorda
    const container = document.createElement('div')
    container.className = 'passi-container'
    const renderOpts = () => {
      container.innerHTML = ''
      if (game.phase === "recall" || game.phase === "feedback") {
        const answerDiv = document.createElement('div')
        answerDiv.className = 'passi-answer-row'
        answerDiv.style.cssText = 'display:flex;justify-content:center;gap:8px;margin-bottom:16px'
        for (let i = 0; i < game.sequence.length; i++) {
          const box = document.createElement('div')
          const done = i < game.userAnswer.length
          box.style.cssText = `
            width:48px;height:48px;border-radius:8px;display:flex;align-items:center;justify-content:center;
            font-size:22px;background:${done ? (game.getItemResult(i) === 'correct' ? 'rgba(60,200,60,0.3)' : 'rgba(220,60,60,0.3)') : 'rgba(255,255,255,0.06)'};
            border:2px solid ${done ? (game.getItemResult(i) === 'correct' ? '#3cc83c' : '#dc3c3c') : 'rgba(255,255,255,0.15)'}
          `
          if (done) box.textContent = game.getItemIcon(game.userAnswer[i])
          answerDiv.appendChild(box)
        }
        container.appendChild(answerDiv)
      }
      if (game.phase === "recall") {
        const opts = game.getOptions()
        const selected = new Set(game.userAnswer)
        opts.forEach(o => {
          const btn = document.createElement('button')
          btn.className = 'btn btn-option btn-icon'
          btn.innerHTML = `${game.getItemIcon(o)} ${o}`
          btn.disabled = selected.has(o)
          btn.addEventListener('click', () => { game.selectItem(o); renderOpts() })
          container.appendChild(btn)
        })
      }
    }
    renderOpts()
    area.appendChild(container)
  }

  private _renderBrainTrainerUI(area: HTMLElement): void {
    const game = this.currentGame as import('../games/brain-trainer').BrainTrainer
    const container = document.createElement('div')
    container.className = 'brain-trainer-container'
    const render = () => {
      container.innerHTML = ''
      const opts = game.getQuestionOptions() as (number | string)[]
      opts.forEach(o => {
        const btn = document.createElement('button')
        btn.className = 'btn btn-option'
        btn.textContent = String(o)
        btn.addEventListener('click', () => { game.answer(o); render() })
        container.appendChild(btn)
      })
    }
    render()
    area.appendChild(container)
  }

  private _renderCostruisciUI(area: HTMLElement): void {
    const game = this.currentGame as import('../games/costruisci-modello').CostruisciModello
    const container = document.createElement('div')
    container.className = 'costruisci-container'
    const render = () => {
      container.innerHTML = ''
      if (game.phase !== "building") return
      game.getAvailablePieces().forEach(p => {
        const info = game.getShapeInfo(p)
        if (!info) return
        const btn = document.createElement('button')
        btn.className = 'btn btn-option'
        btn.textContent = info.label
        btn.style.borderColor = info.color
        btn.addEventListener('click', () => { game.placePiece(p); render() })
        container.appendChild(btn)
      })
    }
    render()
    area.appendChild(container)
  }

  private _renderMappaUI(area: HTMLElement): void {
    const game = this.currentGame as import('../games/mappa-stanza').MappaStanza
    const container = document.createElement('div')
    container.className = 'mappa-container'
    const render = () => {
      container.innerHTML = ''
      const gs = game.gridSize
      const gridEl = document.createElement('div')
      gridEl.className = 'mappa-grid'
      gridEl.style.gridTemplateColumns = `repeat(${gs}, 70px)`
      for (let r = 0; r < gs; r++) {
        for (let c = 0; c < gs; c++) {
          const cell = document.createElement('div')
          cell.className = 'mappa-cell'
          let content = ''
          let isPlacedByUser = false
          for (const [obj, pos] of Object.entries(game.userPositions)) {
            if (pos[0] === r && pos[1] === c) { content = game.getObjectIcon(obj); isPlacedByUser = true }
          }
          if (!content && game.phase === "showing") {
            for (const [obj, pos] of Object.entries(game.objectPositions)) {
              if (pos[0] === r && pos[1] === c) content = game.getObjectIcon(obj)
            }
          }
          cell.textContent = content
          if (isPlacedByUser) cell.style.borderColor = '#3cc83c'
          if (game.phase === "recall" && !isPlacedByUser) {
            const objects = game.getObjectsToPlace()
            if (objects.length > 0) {
              cell.addEventListener('click', () => { game.placeObject(objects[0], r, c); render() })
            }
          }
          gridEl.appendChild(cell)
        }
      }
      container.appendChild(gridEl)
      if (game.phase === "recall") {
        const objects = game.getObjectsToPlace()
        if (objects.length > 0) {
          const title = document.createElement('div')
          title.className = 'mappa-title'
          title.textContent = `Posiziona: ${objects[0]} ${game.getObjectIcon(objects[0])}`
          container.insertBefore(title, gridEl)
        }
      }
    }
    render()
    area.appendChild(container)
  }

  private _renderMusicalUI(area: HTMLElement): void {
    const game = this.currentGame as import('../games/musical-memory').MusicalMemory
    const container = document.createElement('div')
    container.className = 'musical-container'
    const notes = ["Do", "Mi", "Sol", "Do'"]
    const colors = ["#e63c3c", "#3c82e6", "#3cc83c", "#e6d232"]
    notes.forEach((n, i) => {
      const btn = document.createElement('button')
      btn.className = 'btn musical-btn'
      btn.textContent = n
      btn.style.background = colors[i] + '40'
      btn.style.borderColor = colors[i]
      btn.addEventListener('click', () => game.pressButton(i))
      container.appendChild(btn)
    })
    area.appendChild(container)
  }

  private _renderMemoryCarteUI(area: HTMLElement): void {
    const game = this.currentGame as import('../games/memory-carte').MemoryCarte
    const container = document.createElement('div')
    container.className = 'memory-grid-container'
    const render = () => {
      container.innerHTML = ''
      if (game.phase !== "playing") return
      const [rows, cols] = game.getGridSize()
      const grid = document.createElement('div')
      grid.className = 'memory-grid'
      grid.style.gridTemplateColumns = `repeat(${cols}, 72px)`
      for (let i = 0; i < rows * cols; i++) {
        const card = document.createElement('div')
        card.className = `memory-card ${game.isCardMatched(i) ? 'matched' : ''} ${game.isCardRevealed(i) ? 'revealed' : ''}`
        card.textContent = game.isCardRevealed(i) || game.isCardMatched(i) ? game.getCardSymbol(i) : '?'
        card.addEventListener('click', () => { game.selectCard(i); render() })
        grid.appendChild(card)
      }
      container.appendChild(grid)
    }
    render()
    area.appendChild(container)
  }

  private _renderMemoryImmaginiUI(area: HTMLElement): void {
    const game = this.currentGame as import('../games/memory-immagini').MemoryImmagini
    const container = document.createElement('div')
    container.className = 'memory-grid-container'
    const render = () => {
      container.innerHTML = ''
      if (game.phase === "instruction") {
        const msg = document.createElement('div')
        msg.className = 'memory-instruction'
        msg.textContent = "Preparati a memorizzare le immagini!"
        container.appendChild(msg)
        return
      }
      if (game.phase === "study") {
        const elapsed = Math.min((Date.now() - game.studyTimer) / 1000, game.studyDuration)
        const remaining = Math.ceil(game.studyDuration - elapsed)
        const timer = document.createElement('div')
        timer.className = 'memory-study-timer'
        timer.textContent = `Memorizza... ${remaining}s`
        container.appendChild(timer)
      }
      const [rows, cols] = game.getGridSize()
      const size = Math.min(72, Math.floor((area.clientWidth - 48) / cols - 8))
      const grid = document.createElement('div')
      grid.className = 'memory-grid'
      grid.style.gridTemplateColumns = `repeat(${cols}, ${size}px)`
      for (let i = 0; i < rows * cols; i++) {
        const card = document.createElement('div')
        const wrong = game.isCardWrong(i)
        card.className = `memory-card ${game.isCardMatched(i) ? 'matched' : ''} ${game.isCardRevealed(i) && !wrong ? 'revealed' : ''} ${wrong ? 'wrong' : ''}`
        card.textContent = game.isCardRevealed(i) || game.isCardMatched(i) ? game.getCardIcon(i) : '?'
        card.style.width = `${size}px`
        card.style.height = `${size}px`
        card.style.fontSize = `${Math.max(16, size - 12)}px`
        card.addEventListener('click', () => { game.selectCard(i); render() })
        grid.appendChild(card)
      }
      container.appendChild(grid)
    }
    render()
    area.appendChild(container)
  }

  private _renderPuzzleUI(area: HTMLElement): void {
    const game = this.currentGame as import('../games/puzzle').Puzzle
    const container = document.createElement('div')
    container.className = 'puzzle-container'
    const render = () => {
      container.innerHTML = ''
      if (game.phase !== "playing") return
      const gs = game.gridSize
      const grid = document.createElement('div')
      grid.className = 'puzzle-grid'
      grid.style.gridTemplateColumns = `repeat(${gs}, 70px)`
      for (let r = 0; r < gs; r++) {
        for (let c = 0; c < gs; c++) {
          const cell = document.createElement('div')
          cell.className = `puzzle-cell ${game.isSelected(r, c) ? 'selected' : ''}`
          cell.textContent = game.currentGrid[r]?.[c] ?? ''
          cell.addEventListener('click', () => { game.selectPiece(r, c); render() })
          grid.appendChild(cell)
        }
      }
      container.appendChild(grid)
      const hintBtn = document.createElement('button')
      hintBtn.className = 'btn btn-secondary'
      hintBtn.textContent = `Indizio (${game.maxHints - game.hintCount} rimasti)`
      hintBtn.addEventListener('click', () => { game.useHint(); render() })
      container.appendChild(hintBtn)
    }
    render()
    area.appendChild(container)
  }

  private _renderSequenzaUI(area: HTMLElement): void {
    const game = this.currentGame as import('../games/sequenza-simboli').SequenzaSimboli
    const container = document.createElement('div')
    container.className = 'sequenza-container'
    const render = () => {
      container.innerHTML = ''
      if (game.phase !== "input") return
      const symbols = game.getAvailableSymbols()
      symbols.forEach(([key, icon]) => {
        const btn = document.createElement('button')
        btn.className = 'btn btn-option btn-icon'
        btn.textContent = icon
        btn.addEventListener('click', () => { game.selectSymbol(key); render() })
        container.appendChild(btn)
      })
    }
    render()
    area.appendChild(container)
  }

  private _renderBasketUI(area: HTMLElement): void {
    const container = document.createElement('div')
    container.className = 'basket-ui'
    const btn = document.createElement('button')
    btn.className = 'btn btn-primary btn-basket-throw'
    btn.textContent = 'LANCIA!'
    btn.addEventListener('click', () => {
      const game = this.currentGame as import('../games/basket').Basket
      game.launchBall(game.throwHand)
    })
    container.appendChild(btn)
    area.appendChild(container)
  }

  private _renderPallonciniUI(_area: HTMLElement): void {
    if (this.pallonciniHandler) {
      this.canvas.removeEventListener('click', this.pallonciniHandler)
    }
    this.pallonciniHandler = (e: MouseEvent) => {
      const rect = this.canvas.getBoundingClientRect()
      const x = e.clientX - rect.left
      const y = e.clientY - rect.top
      const game = this.currentGame as import('../games/palloncini').Palloncini
      if (!game) return
      for (let i = game.balloons.length - 1; i >= 0; i--) {
        const b = game.balloons[i]
        const dx = x - b.x, dy = y - b.y
        if (dx * dx + dy * dy < b.radius * b.radius) {
          game.popBalloon(i)
          this._burstConfetti(b.x, b.y, 12, [b.color, '#ffffff', '#ffd93d'])
          this._showScoreFloat(b.x - 20, b.y - 40, '+15', true)
          break
        }
      }
    }
    this.canvas.addEventListener('click', this.pallonciniHandler)
  }

  private _renderSemaforoUI(area: HTMLElement): void {
    const game = this.currentGame as import('../games/semaforo-esecutivo').SemaforoEsecutivo
    const container = document.createElement('div')
    container.className = 'semaforo-buttons'
    const arrowMap: Record<string, string> = { forward: '\u2191 Avanti', center: '\u270B STOP', left: '\u2190 Sinistra', right: '\u2192 Destra' }
    ;[
      { action: "forward" },
      { action: "center" },
      { action: "left" },
      { action: "right" },
    ].forEach(({ action }) => {
      const btn = document.createElement('button')
      btn.className = 'btn btn-option'
      btn.textContent = arrowMap[action] ?? action
        btn.addEventListener('click', () => {
          game.validateAction(action)
          btn.classList.add('correct-pulse')
          setTimeout(() => btn.classList.remove('correct-pulse'), 600)
        })
      container.appendChild(btn)
    })
    area.appendChild(container)
  }

  private _renderCercaParoleUI(area: HTMLElement): void {
    const game = this.currentGame as import('../games/cerca-parole').CercaParole
    const container = document.createElement('div')
    container.className = 'cerca-parole-container'
    const render = () => {
      container.innerHTML = ''
      const wordsDiv = document.createElement('div')
      wordsDiv.className = 'cerca-parole-words'
      game.words.forEach(w => {
        const el = document.createElement('span')
        el.className = `cerca-parole-word ${w.found ? 'found' : ''}`
        el.textContent = w.word
        wordsDiv.appendChild(el)
      })
      container.appendChild(wordsDiv)
      const grid = document.createElement('div')
      grid.className = 'cerca-parole-grid'
      const gs = game.getGridSize()
      grid.style.gridTemplateColumns = `repeat(${gs}, 36px)`
      for (let r = 0; r < gs; r++) {
        for (let c = 0; c < gs; c++) {
          const cell = document.createElement('div')
          cell.className = `cerca-parole-cell ${game.isFound(r, c) ? 'found' : ''} ${game.isSelected(r, c) ? 'selected' : ''}`
          cell.textContent = game.grid[r][c]
          cell.addEventListener('click', () => { game.selectCell(r, c); render() })
          grid.appendChild(cell)
        }
      }
      container.appendChild(grid)
    }
    render()
    area.appendChild(container)
  }

  private _onGameEnd(): void {
    if (!this.currentGame) return
    const g = this.currentGame
    this.session.logGame(g.name, g.result)
    if (this.sessionMode && this.gameIndex >= 0 && this.gameIndex < this.games.length - 1) {
      this.gameIndex++
      const nextGame = this.games[this.gameIndex]
      if (nextGame.state === "idle" || nextGame.state === "finished") {
        this.currentGame = nextGame
        this.session.currentGame = nextGame.name
        nextGame.start()
        this._renderGameUI()
        return
      }
    }
    this.state = "finished"
    this._renderFinished()
  }

  private _renderFinished(): void {
    this.overlay.innerHTML = ''
    const summary = this.session.end()
    const container = document.createElement('div')
    container.className = 'finished-container'
    container.innerHTML = `
      <div class="finished-icon">\u{1F389}</div>
      <h2>Sessione Completata!</h2>
      <div class="finished-stats">
        <div class="stat">
          <span class="stat-value">${summary.totalScore}</span>
          <span class="stat-label">Punti Totali</span>
        </div>
        <div class="stat">
          <span class="stat-value">${Math.round(summary.durationSeconds / 60)}</span>
          <span class="stat-label">Minuti</span>
        </div>
        <div class="stat">
          <span class="stat-value">${summary.finalDifficulty}</span>
          <span class="stat-label">Livello Finale</span>
        </div>
        <div class="stat">
          <span class="stat-value">${summary.games.length}</span>
          <span class="stat-label">Giochi</span>
        </div>
      </div>
      <div class="finished-actions">
        <button class="btn btn-primary" id="btn-menu">Torna al Menu</button>
        <button class="btn btn-secondary" id="btn-report">Guarda Report</button>
      </div>`
    this.overlay.appendChild(container)
    document.getElementById('btn-menu')?.addEventListener('click', () => this._backToMenu())
    document.getElementById('btn-report')?.addEventListener('click', () => this._showReport())
  }

  private _showReport(): void {
    this.state = "report"
    this.overlay.innerHTML = ''
    const container = document.createElement('div')
    container.className = 'report-container'
    let html = '<h2>Report Sessioni</h2><button class="btn btn-back" id="btn-back-report">← Torna al Menu</button>'
    try {
      const sessions = JSON.parse(localStorage.getItem('brainmove_sessions') ?? '[]')
      if (sessions.length === 0) {
        html += '<p class="report-empty">Nessuna sessione salvata</p>'
      } else {
        html += '<div class="report-list">'
        sessions.reverse().forEach((s: Record<string, unknown>) => {
          html += `<div class="report-item">
            <div class="report-date">${String(s.sessionId ?? '')}</div>
            <div class="report-score">Punti: ${String(s.totalScore ?? 0)}</div>
            <div class="report-duration">Durata: ${Math.round(Number(s.durationSeconds ?? 0) / 60)} min</div>
            <div class="report-games">Giochi: ${(s.games as Array<unknown>)?.length ?? 0}</div>
          </div>`
        })
        html += '</div>'
      }
    } catch {
      html += '<p class="report-empty">Errore nel caricamento dei dati</p>'
    }
    container.innerHTML = html
    this.overlay.appendChild(container)
    document.getElementById('btn-back-report')?.addEventListener('click', () => this._backToMenu())
  }

  private _backToMenu(): void {
    if (this.pallonciniHandler) {
      this.canvas.removeEventListener('click', this.pallonciniHandler)
      this.pallonciniHandler = null
    }
    this.currentGame = null
    this.gameIndex = -1
    this.sessionMode = false
    this._renderMenu()
  }

  destroy(): void {
    cancelAnimationFrame(this.animFrameId)
    this.poseDetector.stop()
  }
}
