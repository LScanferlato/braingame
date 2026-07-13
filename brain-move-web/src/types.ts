export interface PoseData {
  nose?: [number, number]
  l_shoulder?: [number, number]
  r_shoulder?: [number, number]
  l_hip?: [number, number]
  r_hip?: [number, number]
  l_knee?: [number, number]
  r_knee?: [number, number]
  l_ankle?: [number, number]
  r_ankle?: [number, number]
  l_wrist?: [number, number]
  r_wrist?: [number, number]
  l_elbow?: [number, number]
  r_elbow?: [number, number]
  shoulder_center?: [number, number]
  hip_center?: [number, number]
  shoulder_width?: number
  trunk_angle?: number
  instability?: number
  knee_hip_ratio?: number
  in_frame?: boolean
}

export type GameState = "idle" | "playing" | "finished"
export type AppState = "menu" | "playing" | "finished" | "report"

export interface GameResult {
  completed: boolean
  accuracy: number
  [key: string]: unknown
}

export interface QuestionData {
  q: string
  opts: string[]
  ans: number
}

export type Mood = "felice" | "neutro" | "concentrato" | "stanco" | "preoccupato"
