import type { PoseData } from '../types'

export class PoseDetector {
  private syntheticTime = 0
  enabled = false
  webcamStream: MediaStream | null = null
  video: HTMLVideoElement | null = null

  async init(): Promise<boolean> {
    try {
      this.webcamStream = await navigator.mediaDevices.getUserMedia({ video: { width: 640, height: 480, facingMode: "user" } })
      this.video = document.createElement('video')
      this.video.srcObject = this.webcamStream
      this.video.width = 640
      this.video.height = 480
      await this.video.play()
      this.enabled = true
      return true
    } catch {
      this.enabled = false
      return false
    }
  }

  detect(): PoseData | null {
    if (!this.enabled) return this._syntheticPose()
    return this._syntheticPose()
  }

  private _syntheticPose(): PoseData {
    this.syntheticTime += 0.016
    const wobble = 5 * (Math.sin(this.syntheticTime * 2) + Math.sin(this.syntheticTime * 1.3))
    return {
      nose: [320 + wobble, 100],
      l_shoulder: [290 + wobble * 0.5, 180],
      r_shoulder: [350 + wobble * 0.5, 180],
      l_hip: [295, 300],
      r_hip: [345, 300],
      l_knee: [290, 380],
      r_knee: [350, 380],
      l_ankle: [300, 450],
      r_ankle: [340, 450],
      l_wrist: [260 + wobble, 220],
      r_wrist: [380 + wobble, 220],
      l_elbow: [275, 200],
      r_elbow: [365, 200],
      shoulder_center: [320, 180],
      hip_center: [320, 300],
      shoulder_width: 60,
      trunk_angle: 2 + Math.sin(this.syntheticTime) * 5,
      instability: 0.2 + Math.abs(Math.sin(this.syntheticTime * 0.5)) * 0.3,
      knee_hip_ratio: 0.6 + Math.sin(this.syntheticTime * 2) * 0.05,
      in_frame: true,
    }
  }

  stop(): void {
    if (this.webcamStream) {
      this.webcamStream.getTracks().forEach(t => t.stop())
      this.webcamStream = null
    }
  }
}
