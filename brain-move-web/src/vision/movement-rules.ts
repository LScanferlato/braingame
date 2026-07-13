import type { PoseData } from '../types'

export class MovementRules {
  private prevPose: PoseData | null = null
  private recentPoses: PoseData[] = []
  private calibrated = false
  private baseHipX = 0
  private baseShoulderWidth = 0

  calibrate(poseData: PoseData): void {
    if (poseData.hip_center) this.baseHipX = poseData.hip_center[0]
    if (poseData.shoulder_width) this.baseShoulderWidth = poseData.shoulder_width
    this.calibrated = true
  }

  update(poseData: PoseData | null): string {
    if (!poseData || !this.prevPose) {
      this.prevPose = poseData
      return "center"
    }

    this.recentPoses.push(poseData)
    if (this.recentPoses.length > 10) this.recentPoses.shift()

    if (!this.calibrated) this.calibrate(poseData)

    const movement = this.detectStepDirection(this.prevPose, poseData)
    this.prevPose = poseData
    return movement
  }

  detectStepDirection(prev: PoseData, curr: PoseData): string {
    const prevHip = prev.hip_center
    const currHip = curr.hip_center
    if (!prevHip || !currHip) return "center"
    const dx = currHip[0] - prevHip[0]
    if (Math.abs(dx) > 15) return dx > 0 ? "right" : "left"
    const prevSW = prev.shoulder_width ?? 60
    const currSW = curr.shoulder_width ?? 60
    const swDelta = (currSW - prevSW) / prevSW
    if (Math.abs(swDelta) > 0.03) return swDelta > 0 ? "forward" : "backward"
    return "center"
  }

  detectKneeRaise(pose: PoseData): { leftRaised: boolean; rightRaised: boolean } {
    const lKnee = pose.l_knee; const rKnee = pose.r_knee
    const lHip = pose.l_hip; const rHip = pose.r_hip
    const lAnkle = pose.l_ankle; const rAnkle = pose.r_ankle
    if (!lKnee || !rKnee || !lHip || !rHip || !lAnkle || !rAnkle) return { leftRaised: false, rightRaised: false }
    const lKneeHip = (lHip[1] - lKnee[1]) / (lHip[1] - lAnkle[1])
    const rKneeHip = (rHip[1] - rKnee[1]) / (rHip[1] - rAnkle[1])
    return { leftRaised: lKneeHip > 0.5, rightRaised: rKneeHip > 0.5 }
  }

  detectArmRaise(prev: PoseData, curr: PoseData): { left: boolean; right: boolean } {
    const left = curr.l_wrist && prev.l_wrist ? (prev.l_wrist[1] - curr.l_wrist[1]) > 20 : false
    const right = curr.r_wrist && prev.r_wrist ? (prev.r_wrist[1] - curr.r_wrist[1]) > 20 : false
    return { left, right }
  }

  resetCalibration(): void {
    this.calibrated = false
    this.prevPose = null
    this.recentPoses = []
  }
}
