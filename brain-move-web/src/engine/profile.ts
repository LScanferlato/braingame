export interface ProfileData {
  userId: string
  name: string
  mobilityLevel: string
  requiresSupport: boolean
  preferredMode: string
  webcam: { enabled: boolean; saveVideo: boolean; poseOnly: boolean }
  safety: { maxSessionMinutes: number; seatedFallback: boolean }
  seniorMode: boolean
  fontSizeMultiplier: number
}

const DEFAULT_PROFILE: ProfileData = {
  userId: "default",
  name: "Utente",
  mobilityLevel: "medio",
  requiresSupport: true,
  preferredMode: "standing_with_support",
  webcam: { enabled: true, saveVideo: false, poseOnly: true },
  safety: { maxSessionMinutes: 24, seatedFallback: true },
  seniorMode: true,
  fontSizeMultiplier: 1.0,
}

export class Profile {
  data: ProfileData

  constructor() {
    try {
      const stored = localStorage.getItem('brainmove_profile')
      this.data = stored ? JSON.parse(stored) : { ...DEFAULT_PROFILE }
    } catch {
      this.data = { ...DEFAULT_PROFILE }
    }
  }

  save(): void {
    localStorage.setItem('brainmove_profile', JSON.stringify(this.data))
  }

  get<T>(key: string, defaultValue?: T): T {
    return ((this.data as unknown as Record<string, unknown>)[key] as T) ?? (defaultValue as T)
  }

  set<T>(key: string, value: T): void {
    (this.data as unknown as Record<string, unknown>)[key] = value
  }

  get seniorMode(): boolean {
    return this.data.seniorMode
  }

  set seniorMode(v: boolean) {
    this.data.seniorMode = v
    this.save()
  }

  get fontScale(): number {
    return this.seniorMode ? 1.5 : this.data.fontSizeMultiplier
  }
}
