import pygame
import math


class MoodIndicator:
    def __init__(self, x, y, w=380, h=100):
        self.rect = pygame.Rect(x, y, w, h)
        self.mood = "neutro"
        self.icon = "\U0001F610"
        self.label = "Neutro"
        self.color = (180, 180, 200)
        self.confidence = 0.0
        self.smile = 0.0
        self.eyebrow = 0.0
        self.eye_open = 0.0
        self.bar_width = 0
        self.pulse = 0

    def update(self, expression_detector):
        if expression_detector is None:
            return
        self.mood = expression_detector.get_mood()
        self.icon = expression_detector.get_mood_icon()
        self.label = expression_detector.get_mood_label()
        self.color = expression_detector.get_mood_color()
        self.confidence = expression_detector.get_mood_confidence()
        details = expression_detector.get_details()
        self.smile = details["smile"]
        self.eyebrow = details["eyebrow"]
        self.eye_open = details["eye_openness"]
        self.bar_width = int(self.confidence * 140)

    def draw(self, surface, font_large, font_small):
        self.pulse = (self.pulse + 0.03) % (math.pi * 2)
        glow = 0.5 + 0.5 * math.sin(self.pulse)
        x, y, w, h = self.rect

        shadow = pygame.Rect(x + 3, y + 3, w, h)
        pygame.draw.rect(surface, (6, 6, 18), shadow, border_radius=16)

        for i in range(3, 0, -1):
            a = int(10 * glow / i)
            if a < 1:
                continue
            s = pygame.Surface((w + i * 4, h + i * 4), pygame.SRCALPHA)
            pygame.draw.rect(s, (*self.color, a),
                             (0, 0, s.get_width(), s.get_height()), border_radius=16 + i)
            surface.blit(s, (x - i * 2, y - i * 2))

        bg = pygame.Surface((w, h), pygame.SRCALPHA)
        for iy in range(h):
            t = iy / h
            alpha = int(210 + 45 * (1 - t))
            c = (18, 18, 38, alpha)
            pygame.draw.line(bg, c, (0, iy), (w, iy))
        surface.blit(bg, (x, y))
        pygame.draw.rect(surface, self.color, (x, y, w, h), 2, border_radius=16)

        icon_txt = font_large.render(self.icon, True, (255, 255, 255))
        icon_y = y + h // 2 - icon_txt.get_height() // 2
        bg_icon = pygame.Rect(x + 8, icon_y - 4,
                              icon_txt.get_width() + 16, icon_txt.get_height() + 8)
        s = pygame.Surface((bg_icon.w, bg_icon.h), pygame.SRCALPHA)
        s.fill((12, 12, 30, 200))
        surface.blit(s, (bg_icon.x, bg_icon.y))
        pygame.draw.rect(surface, (50, 50, 75), bg_icon, 1, border_radius=10)
        surface.blit(icon_txt, (x + 16, icon_y))

        label_txt = font_large.render(self.label, True, self.color)
        surface.blit(label_txt, (x + 85, y + 10))

        conf_label = font_small.render("Confidenza:", True, (140, 140, 160))
        surface.blit(conf_label, (x + 85, y + 52))

        bar_x = x + 210
        bar_y = y + 54
        bar_w = 140
        bar_h = 18
        pygame.draw.rect(surface, (28, 28, 48), (bar_x, bar_y, bar_w, bar_h), border_radius=9)

        if self.bar_width > 0:
            fill = pygame.Rect(bar_x, bar_y, self.bar_width, bar_h)
            for iy in range(bar_h):
                t = iy / bar_h
                c = tuple(int(v * (1 - t * 0.3)) for v in self.color)
                pygame.draw.line(surface, c, (bar_x, bar_y + iy),
                                 (bar_x + self.bar_width, bar_y + iy))
            pygame.draw.rect(surface, self.color, fill, 2, border_radius=9)

            if glow > 0.7:
                sh = pygame.Surface((20, bar_h), pygame.SRCALPHA)
                for ix in range(sh.get_width()):
                    a = int(80 * max(0, 1 - abs(ix - 10) / 10))
                    pygame.draw.line(sh, (255, 255, 255, a), (ix, 0), (ix, bar_h))
                sh_x = int((self.pulse / (math.pi * 2)) * bar_w)
                surface.blit(sh, (bar_x + sh_x, bar_y))

        pygame.draw.rect(surface, (75, 75, 95), (bar_x, bar_y, bar_w, bar_h), 1, border_radius=9)

        pct = int(self.confidence * 100)
        pct_txt = font_small.render(f"{pct}%", True, (200, 200, 200))
        surface.blit(pct_txt, (bar_x + bar_w + 10, bar_y - 1))
