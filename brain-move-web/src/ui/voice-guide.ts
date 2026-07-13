export class VoiceGuide {
  private synth: SpeechSynthesis | null = null
  private currentUtterance: SpeechSynthesisUtterance | null = null
  private enabled = false
  private lastText = ''
  private repeatTimer: ReturnType<typeof setInterval> | null = null
  private voices: SpeechSynthesisVoice[] = []

  constructor() {
    if ('speechSynthesis' in window) {
      this.synth = window.speechSynthesis
      this.enabled = true
      this.voices = this.synth.getVoices()
      this.synth.addEventListener('voiceschanged', () => {
        this.voices = this.synth?.getVoices() ?? []
      })
    }
  }

  private _pickVoice(): SpeechSynthesisVoice | undefined {
    return this.voices.find(v => v.lang.toLowerCase().startsWith('it')) ?? this.voices[0]
  }

  speak(text: string, priority = false): void {
    if (!this.enabled || !this.synth) return
    if (!priority && text === this.lastText) return
    this.lastText = text
    if (this.synth.speaking) {
      this.synth.cancel()
    }
    const utterance = new SpeechSynthesisUtterance(text)
    utterance.lang = 'it-IT'
    utterance.rate = 0.75
    utterance.pitch = 1.1
    utterance.volume = 1.0
    const voice = this._pickVoice()
    if (voice) utterance.voice = voice
    this.currentUtterance = utterance
    this.synth.speak(utterance)
  }

  repeat(): void {
    if (this.lastText) {
      this.speak(this.lastText, true)
    }
  }

  startAutoRepeat(text: string, intervalMs = 15000): void {
    this.speak(text, true)
    this.stopAutoRepeat()
    this.repeatTimer = setInterval(() => {
      this.speak(text, true)
    }, intervalMs)
  }

  stopAutoRepeat(): void {
    if (this.repeatTimer) {
      clearInterval(this.repeatTimer)
      this.repeatTimer = null
    }
  }

  stop(): void {
    this.stopAutoRepeat()
    if (this.synth) {
      this.synth.cancel()
    }
    this.currentUtterance = null
  }

  isEnabled(): boolean { return this.enabled }

  destroy(): void {
    this.stop()
    this.synth = null
  }
}
