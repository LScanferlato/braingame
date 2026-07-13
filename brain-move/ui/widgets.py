import pygame
import math


def _shadow_rect(surface, rect, offset=4, color=(0, 0, 0, 80), radius=16):
    s = pygame.Surface((rect.w, rect.h), pygame.SRCALPHA)
    pygame.draw.rect(s, color, (offset, offset, rect.w, rect.h), border_radius=radius)
    surface.blit(s, (rect.x, rect.y))


def _glow_rect(surface, rect, color, radius=16, glow_width=6):
    for i in range(glow_width, 0, -1):
        a = max(1, int(80 / (glow_width - i + 1)))
        c = (color[0], color[1], color[2], a)
        s = pygame.Surface((rect.w + i * 2, rect.h + i * 2), pygame.SRCALPHA)
        pygame.draw.rect(s, c, (0, 0, s.get_width(), s.get_height()),
                         border_radius=radius + i)
        surface.blit(s, (rect.x - i, rect.y - i))


def _gradient_rect(surface, rect, color_top, color_bottom, radius=0):
    h = rect.h
    w = rect.w
    cx, cy = rect.x, rect.y
    for y in range(h):
        t = y / max(h - 1, 1)
        c = tuple(int(a + (b - a) * t) for a, b in zip(color_top, color_bottom))
        if radius and (y < radius or y > h - radius):
            s = pygame.Surface((w, 1))
            s.fill(c)
            surface.blit(s, (cx, cy + y))
        else:
            pygame.draw.line(surface, c, (cx, cy + y), (cx + w - 1, cy + y))


class Button:
    SHADOW_OFF = 4

    def __init__(self, x, y, w, h, text, color=(70, 130, 180), text_color=(255, 255, 255)):
        self.rect = pygame.Rect(x, y, w, h)
        self.text = text
        self.base_color = color
        self.text_color = text_color
        self.hover = False
        self.enabled = True
        self.pulse = 0

    def draw(self, surface, font):
        self.pulse = (self.pulse + 0.025) % (math.pi * 2)
        glow = 0.5 + 0.5 * math.sin(self.pulse)

        if not self.enabled:
            c = (80, 80, 80)
            _shadow_rect(surface, self.rect, 2, (0, 0, 0, 40), 18)
            pygame.draw.rect(surface, c, self.rect, border_radius=18)
            pygame.draw.rect(surface, (100, 100, 100), self.rect, 2, border_radius=18)
            txt = font.render(self.text, True, (120, 120, 120))
            surface.blit(txt, (self.rect.centerx - txt.get_width() // 2,
                               self.rect.centery - txt.get_height() // 2))
            return

        _shadow_rect(surface, self.rect, self.SHADOW_OFF, (0, 0, 0, 60), 18)

        if self.hover:
            bright = tuple(min(v + 60, 255) for v in self.base_color)
            glow_color = tuple(min(v + 40, 255) for v in self.base_color)
            _glow_rect(surface, self.rect, glow_color, 18, 8)
            c = bright
            border_c = tuple(min(v + 80, 255) for v in self.base_color)
        else:
            c = self.base_color
            border_c = tuple(min(v + 40, 255) for v in self.base_color)

        top = tuple(min(v + 35, 255) for v in c)
        bot = tuple(max(v - 15, 0) for v in c)
        _gradient_rect(surface, self.rect, top, bot, 18)
        pygame.draw.rect(surface, border_c, self.rect, 3, border_radius=18)

        if self.hover:
            shine = pygame.Surface((self.rect.w, self.rect.h // 3), pygame.SRCALPHA)
            for y in range(shine.get_height()):
                a = max(0, 40 - int(40 * y / shine.get_height()))
                pygame.draw.line(shine, (255, 255, 255, a),
                                 (0, y), (shine.get_width(), y))
            surface.blit(shine, self.rect.topleft)

        txt = font.render(self.text, True, self.text_color)
        tx = self.rect.centerx - txt.get_width() // 2
        ty = self.rect.centery - txt.get_height() // 2
        surface.blit(txt, (tx, ty))

    def is_clicked(self, pos):
        return self.rect.collidepoint(pos) and self.enabled

    def check_hover(self, pos):
        self.hover = self.rect.collidepoint(pos)


class ProgressBar:
    def __init__(self, x, y, w, h, color=(50, 190, 50)):
        self.rect = pygame.Rect(x, y, w, h)
        self.color = color
        self.progress = 0
        self.shimmer = 0

    def draw(self, surface):
        self.shimmer = (self.shimmer + 0.05) % (math.pi * 2)
        shimmer = 0.5 + 0.5 * math.sin(self.shimmer)

        _shadow_rect(surface, self.rect, 2, (0, 0, 0, 50), 12)

        pygame.draw.rect(surface, (18, 18, 32), self.rect, border_radius=12)

        if self.progress > 0:
            fill_w = max(4, int(self.rect.width * self.progress))
            fill = pygame.Rect(self.rect.x, self.rect.y, fill_w, self.rect.height)

            top = tuple(min(v + 50, 255) for v in self.color)
            bot = tuple(max(v - 20, 0) for v in self.color)
            _gradient_rect(surface, fill, top, bot, 12)
            pygame.draw.rect(surface, self.color, fill, 2, border_radius=12)

            if shimmer > 0.6:
                sh = pygame.Surface((fill_w // 3, self.rect.h), pygame.SRCALPHA)
                for x in range(sh.get_width()):
                    a = int(70 * max(0, 1 - abs(x - sh.get_width() / 2) / (sh.get_width() / 2)))
                    pygame.draw.line(sh, (255, 255, 255, a), (x, 0), (x, sh.get_height()))
                sh_x = int((self.shimmer / (math.pi * 2)) * self.rect.w)
                surface.blit(sh, (self.rect.x + sh_x, self.rect.y))

        pygame.draw.rect(surface, (55, 55, 75), self.rect, 2, border_radius=12)


class WebcamView:
    BONES = [
        ("l_shoulder", "r_shoulder"),
        ("l_shoulder", "l_hip"),
        ("r_shoulder", "r_hip"),
        ("l_hip", "r_hip"),
        ("l_hip", "l_knee"),
        ("r_hip", "r_knee"),
        ("l_knee", "l_ankle"),
        ("r_knee", "r_ankle"),
        ("l_shoulder", "l_elbow"),
        ("r_shoulder", "r_elbow"),
        ("l_elbow", "l_wrist"),
        ("r_elbow", "r_wrist"),
    ]

    JOINT_COLOR = (80, 220, 80)
    BONE_COLOR = (60, 180, 220)
    BONE_WIDTH = 3
    JOINT_RADIUS = 5

    def __init__(self, x, y, w, h):
        self.rect = pygame.Rect(x, y, w, h)
        self.surface = pygame.Surface((w, h))
        self.pose_data = None
        self.show_camera = False
        self.camera_surface = None
        self.glow_timer = 0

    def update_pose(self, pose_data, frame_shape=None, frame_rgb=None):
        self.pose_data = pose_data
        self.frame_shape = frame_shape
        if self.show_camera and frame_rgb is not None:
            self._render_camera(frame_rgb)
        else:
            self._render_skeleton()

    def _mirror_x(self, x):
        return self.rect.w - x

    def _to_screen(self, point):
        if self.frame_shape is None:
            return (int(self._mirror_x(point[0])), int(point[1]))
        fh, fw = self.frame_shape[:2]
        sx = point[0] / max(fw, 1) * self.rect.w
        sy = point[1] / max(fh, 1) * self.rect.h
        return (int(self._mirror_x(sx)), int(sy))

    def _render_skeleton(self):
        self.surface.fill((8, 8, 20))
        border_rect = pygame.Rect(2, 2, self.rect.w - 4, self.rect.h - 4)
        pygame.draw.rect(self.surface, (18, 18, 38), border_rect, border_radius=10)

        if self.pose_data is None:
            return

        joints = {}
        all_keys = ["nose", "l_shoulder", "r_shoulder", "l_hip", "r_hip",
                     "l_knee", "r_knee", "l_ankle", "r_ankle",
                     "l_wrist", "r_wrist", "l_elbow", "r_elbow"]
        for key in all_keys:
            if key in self.pose_data and self.pose_data[key] is not None:
                joints[key] = self._to_screen(self.pose_data[key])

        overlay = pygame.Surface(self.surface.get_size(), pygame.SRCALPHA)
        for a, b in self.BONES:
            if a in joints and b in joints:
                bw = int(self.BONE_WIDTH * (1.2 if self.pose_data.get("in_frame", True) else 0.6))
                pygame.draw.line(overlay, (*self.BONE_COLOR, 180),
                                 joints[a], joints[b], bw)

        for key, pos in joints.items():
            r = self.JOINT_RADIUS
            pygame.draw.circle(overlay, (*self.JOINT_COLOR, 200), pos, r + 2)
            pygame.draw.circle(overlay, (*self.JOINT_COLOR, 255), pos, r)

        self.surface.blit(overlay, (0, 0))

        cx, cy = self.rect.w // 2, self.rect.h // 2
        pygame.draw.circle(self.surface, (30, 30, 50), (cx, cy),
                           min(self.rect.w, self.rect.h) // 2 - 10, 1)

    def _render_camera(self, frame_rgb):
        import numpy as np
        h, w = self.rect.h, self.rect.w
        frame_resized = np.flip(np.rot90(frame_rgb, 3), axis=1)
        frame_scaled = np.array(
            __import__("cv2").resize(frame_resized, (w, h))
        )
        self.camera_surface = pygame.surfarray.make_surface(frame_scaled)
        self._render_skeleton_on_camera()

    def _render_skeleton_on_camera(self):
        if self.camera_surface is None:
            return
        self.surface.blit(self.camera_surface, (0, 0))

        joints = {}
        all_keys = ["nose", "l_shoulder", "r_shoulder", "l_hip", "r_hip",
                     "l_knee", "r_knee", "l_ankle", "r_ankle",
                     "l_wrist", "r_wrist", "l_elbow", "r_elbow"]
        for key in all_keys:
            if key in self.pose_data and self.pose_data[key] is not None:
                joints[key] = self._to_screen(self.pose_data[key])

        overlay = pygame.Surface(self.surface.get_size(), pygame.SRCALPHA)
        for a, b in self.BONES:
            if a in joints and b in joints:
                pygame.draw.line(overlay, (*self.BONE_COLOR, 160),
                                 joints[a], joints[b], self.BONE_WIDTH)

        for key, pos in joints.items():
            pygame.draw.circle(overlay, (*self.JOINT_COLOR, 200), pos, self.JOINT_RADIUS + 2)
            pygame.draw.circle(overlay, (*self.JOINT_COLOR, 255), pos, self.JOINT_RADIUS)

        self.surface.blit(overlay, (0, 0))

    def set_camera_mode(self, enabled):
        self.show_camera = enabled

    def update(self, frame_rgb):
        pass

    def draw(self, surface):
        self.glow_timer = (self.glow_timer + 0.03) % (math.pi * 2)
        glow = 0.5 + 0.5 * math.sin(self.glow_timer)

        surface.blit(self.surface, self.rect.topleft)
        c = tuple(int(40 + 25 * glow) for _ in range(3))
        pygame.draw.rect(surface, (50 + int(25 * glow), 50 + int(25 * glow), 75),
                         self.rect, 3, border_radius=10)
        pygame.draw.rect(surface, c, self.rect, 1, border_radius=10)


class FeedbackBar:
    def __init__(self, x, y, w, h):
        self.rect = pygame.Rect(x, y, w, h)
        self.text = ""
        self.color = (50, 150, 50)
        self.timer = 0
        self.max_timer = 0

    def set_message(self, text, color=(50, 150, 50)):
        self.text = text
        self.color = color
        self.timer = 3.5
        self.max_timer = 3.5

    def update(self, dt):
        if self.timer > 0:
            self.timer -= dt

    def draw(self, surface, font):
        if self.timer <= 0 and not self.text:
            return
        t = min(self.timer, 1.0) / 1.0 if self.timer < 1 else 1.0
        alpha = t

        c = tuple(int(v * alpha) for v in self.color)
        bg_color = tuple(int(22 * alpha) for _ in range(3))

        rect = self.rect.copy()
        if alpha < 1:
            offset = int((1 - alpha) * 30)
            rect.y += offset

        _shadow_rect(surface, rect, 3, (0, 0, 0, int(60 * alpha)), 14)
        pygame.draw.rect(surface, bg_color, rect, border_radius=14)
        pygame.draw.rect(surface, c, rect, 3, border_radius=14)

        txt = font.render(self.text, True, (255, 255, 255))
        tx = rect.centerx - txt.get_width() // 2
        ty = rect.centery - txt.get_height() // 2
        surface.blit(txt, (tx, ty))
