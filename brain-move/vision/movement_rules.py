import math


class MovementRules:
    """Regole per interpretare i movimenti del corpo dalla pose."""

    def __init__(self):
        self.prev_pose = None
        self.step_threshold_x = 30
        self.step_threshold_scale = 0.03
        self.calibrated = False
        self.calibration_data = []

    def calibrate(self, pose_data, n_frames=30):
        if len(self.calibration_data) < n_frames:
            self.calibration_data.append(pose_data)
            if len(self.calibration_data) >= n_frames:
                self.calibrated = True
                self._compute_baselines()
            return False
        return True

    def _compute_baselines(self):
        hip_xs = [p["hip_center"][0] for p in self.calibration_data]
        shoulders = [p["shoulder_width"] for p in self.calibration_data]
        self.baseline_hip_x = sum(hip_xs) / len(hip_xs)
        self.baseline_shoulder_width = sum(shoulders) / len(shoulders)

    def detect_step_direction(self, prev_pose, curr_pose):
        if prev_pose is None or curr_pose is None:
            return "center"
        prev_hip_x = prev_pose["hip_center"][0]
        curr_hip_x = curr_pose["hip_center"][0]
        delta_x = curr_hip_x - prev_hip_x

        if delta_x > self.step_threshold_x:
            return "right"
        elif delta_x < -self.step_threshold_x:
            return "left"
        return "center"

    def detect_forward_backward(self, prev_pose, curr_pose):
        if prev_pose is None or curr_pose is None:
            return "center"
        prev_scale = prev_pose["shoulder_width"]
        curr_scale = curr_pose["shoulder_width"]
        if prev_scale == 0:
            return "center"
        delta_scale = (curr_scale - prev_scale) / prev_scale

        if delta_scale > self.step_threshold_scale:
            return "forward"
        elif delta_scale < -self.step_threshold_scale:
            return "backward"
        return "center"

    def detect_knee_raise(self, pose_data):
        lk = pose_data.get("l_knee", (0, 0))
        rk = pose_data.get("r_knee", (0, 0))
        la = pose_data.get("l_ankle", (0, 0))
        ra = pose_data.get("r_ankle", (0, 0))
        lh = pose_data.get("l_hip", (0, 0))
        rh = pose_data.get("r_hip", (0, 0))

        left_raised = (lh[1] - lk[1]) > (lh[1] - la[1]) * 0.3 if la[1] > lh[1] else False
        right_raised = (rh[1] - rk[1]) > (rh[1] - ra[1]) * 0.3 if ra[1] > rh[1] else False

        return {"left_raised": left_raised, "right_raised": right_raised}

    def detect_alternating_legs(self, poses_window):
        if len(poses_window) < 3:
            return "undetected"

        left_raised_count = 0
        right_raised_count = 0
        for p in poses_window[-10:]:
            knees = self.detect_knee_raise(p)
            if knees["left_raised"]:
                left_raised_count += 1
            if knees["right_raised"]:
                right_raised_count += 1

        total = left_raised_count + right_raised_count
        if total < 2:
            return "stationary"
        if left_raised_count > 0 and right_raised_count > 0:
            ratio = min(left_raised_count, right_raised_count) / max(left_raised_count, right_raised_count)
            if ratio > 0.3:
                return "alternating"
        return "one_side"

    def detect_arm_raise(self, prev_pose, curr_pose):
        if prev_pose is None or curr_pose is None:
            return {"left": False, "right": False}
        l_diff = prev_pose["l_shoulder"][1] - curr_pose["l_shoulder"][1]
        r_diff = prev_pose["r_shoulder"][1] - curr_pose["r_shoulder"][1]
        return {"left": l_diff > 20, "right": r_diff > 20}

    def detect_seated_movement(self, prev_pose, curr_pose):
        direction = self.detect_step_direction(prev_pose, curr_pose)
        arms = self.detect_arm_raise(prev_pose, curr_pose)
        return {"lateral": direction, "arms": arms}
