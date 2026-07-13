import pygame
import sys
import time
import math
import random
from pathlib import Path

from ui.widgets import Button, ProgressBar, WebcamView, FeedbackBar
from ui.mood_indicator import MoodIndicator


class Layout:
    W = 1900
    H = 1000

    SIDEBAR_X = 30
    SIDEBAR_W = 380
    SIDEBAR_R = SIDEBAR_X + SIDEBAR_W

    GAME_PANEL_X = SIDEBAR_R + 30
    GAME_PANEL_W = W - GAME_PANEL_X - 30
    GAME_PANEL_Y = 90
    GAME_PANEL_H = H - GAME_PANEL_Y - 30

    GC_X = GAME_PANEL_X + 30
    GC_Y = GAME_PANEL_Y + 10
    GC_W = GAME_PANEL_W - 60
    GC_CX = GAME_PANEL_X + GAME_PANEL_W // 2

    WEB_X, WEB_Y, WEB_W, WEB_H = SIDEBAR_X, 20, SIDEBAR_W, 280
    MOOD_X, MOOD_Y, MOOD_W, MOOD_H = SIDEBAR_X, 315, SIDEBAR_W, 90
    BACK_X, BACK_Y = SIDEBAR_X, H - 70


class MainWindow:
    BG = (8, 8, 18)
    ACCENT = (70, 170, 240)
    ACCENT2 = (160, 90, 210)
    PANEL_BG = (14, 14, 30)
    PANEL_BORDER = (30, 30, 55)
    TEXT = (240, 240, 245)
    TEXT_MUTED = (150, 150, 175)
    SUCCESS = (60, 210, 90)
    WARN = (230, 190, 50)

    def __init__(self, session, games_list, pose_detector=None,
                 fatigue_detector=None, fall_risk_detector=None, movement_rules=None,
                 facial_expression=None):
        pygame.init()
        pygame.display.set_caption("Brain-Move — Stimolazione Cognitiva e Motoria")
        self.screen = pygame.display.set_mode((Layout.W, Layout.H), pygame.HWSURFACE | pygame.DOUBLEBUF)
        self.clock = pygame.time.Clock()

        self.font_title = pygame.font.Font(None, 62)
        self.font_large = pygame.font.Font(None, 44)
        self.font_medium = pygame.font.Font(None, 34)
        self.font_small = pygame.font.Font(None, 26)
        self.font_tiny = pygame.font.Font(None, 22)

        self.session = session
        self.games_list = games_list
        self.pose_detector = pose_detector
        self.fatigue_detector = fatigue_detector
        self.fall_risk_detector = fall_risk_detector
        self.movement_rules = movement_rules
        self.facial_expression = facial_expression
        self.current_game_index = -1
        self.current_game = None
        self.running = True
        self.state = "menu"

        self.webcam_view = WebcamView(Layout.WEB_X, Layout.WEB_Y, Layout.WEB_W, Layout.WEB_H)
        self.mood_indicator = MoodIndicator(Layout.MOOD_X, Layout.MOOD_Y, Layout.MOOD_W, Layout.MOOD_H)

        pb_x = Layout.GAME_PANEL_X
        pb_w = min(500, Layout.GAME_PANEL_W // 3)
        self.progress_bar = ProgressBar(pb_x, 20, pb_w, 26)
        self.feedback_bar = FeedbackBar(pb_x + pb_w + 20, 20, Layout.GAME_PANEL_W - pb_w - 40, 26 + 8)

        self.menu_buttons = self._create_menu_buttons()
        self.game_buttons = []
        self.back_button = Button(Layout.BACK_X, Layout.BACK_Y, 180, 55, "← Indietro", (160, 50, 50))

        self.last_frame_rgb = None
        self.prev_pose = None
        self.poses_window = []

        self.session_summary = None
        self.report_data = None
        self.session.start()

        self.bg_time = 0
        self._init_particles()

    def _init_particles(self):
        self.particles = []
        for _ in range(60):
            self.particles.append({
                "x": random.uniform(0, Layout.W),
                "y": random.uniform(0, Layout.H),
                "vx": random.uniform(-0.4, 0.4),
                "vy": random.uniform(-0.3, -0.8),
                "r": random.uniform(1.5, 4),
                "alpha": random.uniform(25, 100),
                "speed": random.uniform(0.1, 0.3),
            })

    def _create_menu_buttons(self):
        buttons = []
        labels = [
            ("\U0001F31E Respiro del Faro", self.ACCENT),
            ("\U0001F9B4 Passi e Ricorda", self.ACCENT),
            ("\U0001F6A6 Semaforo Esecutivo", self.ACCENT),
            ("\U0001F5FA Mappa della Stanza", self.ACCENT),
            ("\U0001F3D7 Costruisci il Modello", self.ACCENT),
            ("\U0001F4D3 Diario delle Missioni", self.ACCENT),
            ("\U0001F0CF Memory Carte", self.ACCENT),
            ("\U0001F3B2 Sequenza Simboli", self.ACCENT),
            ("\U0001F5EA Parole Incrociate", self.ACCENT),
            ("\U0001F3C0 Basket", self.ACCENT),
            ("\U0001F9E9 Puzzle", self.ACCENT),
            ("\U0001F5BC Memory Immagini", self.ACCENT),
            ("\U0001F9E0 Brain Trainer", self.ACCENT),
            ("\U0001F3B5 Musical Memory", self.ACCENT),
            ("\u25B6 Avvia Sessione Completa", (40, 170, 60)),
            ("\U0001F4CA Report e Progressi", self.ACCENT2),
        ]
        cols, rows = 2, 8
        col_w = (Layout.GC_W - 40) // 2
        btn_w = col_w - 20
        btn_h = 76
        gap_y = 10
        total_h = rows * btn_h + (rows - 1) * gap_y
        start_y = Layout.GC_Y + (Layout.GAME_PANEL_H - 120 - total_h) // 2

        for i, (label, color) in enumerate(labels):
            col = i // rows
            row = i % rows
            x = Layout.GC_X + col * col_w + 10
            y = start_y + row * (btn_h + gap_y)
            if i >= 14:
                y = Layout.GAME_PANEL_Y + Layout.GAME_PANEL_H - 100 + 60 * (i - 14)
                x = Layout.GC_X + 10
                if i == 15:
                    x = Layout.GC_X + col_w + 10
                btn_w2 = col_w - 20
                buttons.append(Button(x, y, btn_w2, 60, label, color))
            else:
                buttons.append(Button(x, y, btn_w, btn_h, label, color))
        return buttons

    # ── Main loop ─────────────────────────────────────────────────

    def run(self):
        while self.running:
            dt = self.clock.tick(60) / 1000.0
            self._handle_events()
            self._update(dt)
            self._draw()
            pygame.display.flip()
        self._cleanup()

    # ── Events ────────────────────────────────────────────────────

    def _handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                self._on_click(event.pos)
            elif event.type == pygame.MOUSEMOTION:
                self._on_hover(event.pos)
            elif event.type == pygame.KEYDOWN:
                self._on_key(event.key)
            elif event.type == pygame.FINGERDOWN:
                self._on_click((int(event.x * Layout.W), int(event.y * Layout.H)))
            elif event.type == pygame.FINGERMOTION:
                self._on_hover((int(event.x * Layout.W), int(event.y * Layout.H)))

    def _on_click(self, pos):
        if self.state == "menu":
            for i, btn in enumerate(self.menu_buttons):
                if btn.is_clicked(pos):
                    if i < 14:
                        self._start_single_game(i)
                    elif i == 14:
                        self._start_full_session()
                    elif i == 15:
                        self._load_report()
        elif self.state == "playing":
            if self.back_button.is_clicked(pos):
                self._stop_current_game()
            elif self.current_game:
                self._handle_game_click(pos)
        elif self.state == "finished":
            for btn in self.game_buttons:
                if btn.is_clicked(pos):
                    if btn.text in ("Torna al Menu", "Torna al Menu  "):
                        self.state = "menu"
                    elif btn.text == "Guarda Report":
                        self._load_report()
        elif self.state == "report":
            for btn in self.game_buttons:
                if btn.is_clicked(pos):
                    self.state = "menu"

    def _on_hover(self, pos):
        if self.state == "menu":
            for btn in self.menu_buttons:
                btn.check_hover(pos)
        self.back_button.check_hover(pos)

    def _on_key(self, key):
        if key == pygame.K_ESCAPE:
            if self.state == "playing":
                self._stop_current_game()
            else:
                self.running = False
        elif self.state == "playing" and self.current_game:
            game = self.current_game
            if game.name == "parole_incrociate":
                if key == pygame.K_RETURN:
                    game.check_word()
                elif key == pygame.K_BACKSPACE:
                    game.delete_letter()
                elif key == pygame.K_LEFT:
                    game.move_cursor("left")
                elif key == pygame.K_RIGHT:
                    game.move_cursor("right")
                elif pygame.K_a <= key <= pygame.K_z:
                    game.set_cell_letter(chr(key).upper())

    def _handle_game_click(self, pos):
        game = self.current_game
        if not game:
            return
        gx, gy = Layout.GC_X, Layout.GC_Y
        cx = Layout.GC_CX
        name = game.name

        if name == "passi_ricorda" and game.phase == "recall":
            options = game.get_options()
            cols = min(len(options), 4)
            btn_w, btn_h = 140, 110
            total_w = cols * (btn_w + 18) - 18
            start_x = cx - total_w // 2
            start_y = gy + 260
            for i, opt in enumerate(options):
                bx = start_x + (i % cols) * (btn_w + 18)
                by = start_y + (i // cols) * (btn_h + 18)
                if pygame.Rect(bx, by, btn_w, btn_h).collidepoint(pos):
                    game.select_item(opt)

        elif name == "memory_carte" and game.phase == "playing":
            rows, cols = game.get_grid_size()
            card_w, card_h = 130, 130
            gap = 16
            total_w = cols * (card_w + gap) - gap
            start_x = cx - total_w // 2
            start_y = gy + 140
            for r in range(rows):
                for c in range(cols):
                    idx = r * cols + c
                    bx = start_x + c * (card_w + gap)
                    by = start_y + r * (card_h + gap)
                    if pygame.Rect(bx, by, card_w, card_h).collidepoint(pos):
                        game.select_card(idx)

        elif name == "sequenza_simboli" and game.phase == "input":
            symbols = game.get_available_symbols()
            btn_w, btn_h = 120, 120
            gap = 16
            cols = min(len(symbols), 4)
            total_w = cols * (btn_w + gap) - gap
            start_x = cx - total_w // 2
            start_y = gy + 260
            for i, (sym_key, sym_icon) in enumerate(symbols):
                bx = start_x + (i % cols) * (btn_w + gap)
                by = start_y + (i // cols) * (btn_h + gap)
                if pygame.Rect(bx, by, btn_w, btn_h).collidepoint(pos):
                    game.select_symbol(sym_key)

        elif name == "semaforo_esecutivo":
            pass

        elif name == "mappa_stanza" and game.phase == "recall":
            objects = game.get_objects_to_place()
            if objects:
                cell_size = 150
                grid_w = game.grid_size * cell_size
                grid_x = cx - grid_w // 2
                grid_y = gy + 240
                for r in range(game.grid_size):
                    for c in range(game.grid_size):
                        rect = pygame.Rect(grid_x + c * cell_size, grid_y + r * cell_size,
                                           cell_size - 4, cell_size - 4)
                        if rect.collidepoint(pos):
                            game.place_object(objects[0], r, c)

        elif name == "costruisci_modello" and game.phase == "building":
            pieces = game.get_available_pieces()
            piece_w, piece_h = 140, 90
            gap = 16
            total_w = len(pieces) * (piece_w + gap) - gap
            start_x = cx - total_w // 2
            for i, piece in enumerate(pieces):
                rect = pygame.Rect(start_x + i * (piece_w + gap), gy + 300, piece_w, piece_h)
                if rect.collidepoint(pos):
                    game.place_piece(piece)

        elif name == "diario_missioni":
            if game.phase == "questions":
                answers = ["Molto", "Abbastanza", "Poco"]
                btn_w = 180
                total_w = 3 * btn_w + 2 * 24
                start_x = cx - total_w // 2
                for i, ans in enumerate(answers):
                    rect = pygame.Rect(start_x + i * (btn_w + 24), gy + 280, btn_w, 70)
                    if rect.collidepoint(pos):
                        game.answer_question(ans)
            elif game.phase == "caregiver":
                notes = game.get_caregiver_options()
                cols = min(3, len(notes))
                btn_w, btn_h = 200, 65
                gap = 16
                total_w = cols * (btn_w + gap) - gap
                start_x = cx - total_w // 2
                for i, note in enumerate(notes):
                    rect = pygame.Rect(start_x + (i % cols) * (btn_w + gap),
                                       gy + 280 + (i // cols) * (btn_h + gap), btn_w, btn_h)
                    if rect.collidepoint(pos):
                        game.add_caregiver_note(note)
                done_rect = pygame.Rect(cx - 130, gy + 500, 260, 65)
                if done_rect.collidepoint(pos):
                    game.complete()

        elif name == "parole_incrociate":
            word_info = game.get_current_word()
            if word_info and not word_info["solved"]:
                cell_size = 74
                grid_w = game.grid_size * cell_size
                grid_x = cx - grid_w // 2
                grid_y = gy + 150
                r, c = word_info["row"], word_info["col"]
                for i in range(len(word_info["word"])):
                    if word_info["direction"] == "across":
                        cr, cc = r, c + i
                    else:
                        cr, cc = r + i, c
                    bx = grid_x + cc * cell_size
                    by = grid_y + cr * cell_size
                    if pygame.Rect(bx, by, cell_size, cell_size).collidepoint(pos):
                        game.select_cell(cr, cc)
                        break
                check_rect = pygame.Rect(cx + grid_w // 2 + 30, grid_y + game.grid_size * cell_size + 20, 200, 55)
                if check_rect.collidepoint(pos):
                    game.check_word()

        elif name == "puzzle" and game.phase == "playing":
            cell_size = min(100, int(Layout.GC_W * 0.5 // game.grid_size))
            grid_w = cell_size * game.grid_size
            start_x = cx - grid_w // 2
            start_y = gy + 140
            for r in range(game.grid_size):
                for c in range(game.grid_size):
                    rect = pygame.Rect(start_x + c * cell_size, start_y + r * cell_size,
                                       cell_size - 2, cell_size - 2)
                    if rect.collidepoint(pos):
                        game.select_piece(r, c)
                        return
            hint_btn = pygame.Rect(cx - 90, start_y + grid_w + 30, 180, 50)
            if hint_btn.collidepoint(pos):
                game.use_hint()

        elif name == "memory_immagini" and game.phase == "playing":
            cols = game.grid_cols
            card_w, card_h = 110, 110
            gap = 12
            total_w = cols * (card_w + gap) - gap
            start_x = cx - total_w // 2
            start_y = gy + 150
            for idx in range(len(game.cards)):
                r = idx // cols
                c = idx % cols
                bx = start_x + c * (card_w + gap)
                by = start_y + r * (card_h + gap)
                if pygame.Rect(bx, by, card_w, card_h).collidepoint(pos):
                    game.select_card(idx)
                    return

        elif name == "brain_trainer" and game.phase == "playing":
            q = game.current_question
            if not q:
                return
            opts = game.get_question_options()
            if q["type"] == "math":
                for i, opt in enumerate(opts):
                    bx = cx - 200 + (i % 2) * 210
                    by = gy + 260 + (i // 2) * 95
                    if pygame.Rect(bx, by, 190, 75).collidepoint(pos):
                        game.answer(opt)
                        return
            elif q["type"] == "recall":
                for i, opt in enumerate(opts):
                    bx = cx - len(opts) * 40 + i * 80
                    by = gy + 280
                    if pygame.Rect(bx, by, 70, 70).collidepoint(pos):
                        game.answer(opt)
                        return
            elif q["type"] == "count":
                for i, opt in enumerate(opts):
                    bx = cx - 200 + (i % 2) * 210
                    by = gy + 320 + (i // 2) * 85
                    if pygame.Rect(bx, by, 190, 70).collidepoint(pos):
                        game.answer(opt)
                        return

        elif name == "musical_memory" and game.phase == "input":
            btn_w, btn_h = 150, 130
            positions = [
                (cx - btn_w - 110, gy + 170),
                (cx + 110, gy + 170),
                (cx - btn_w - 110, gy + 170 + btn_h + 30),
                (cx + 110, gy + 170 + btn_h + 30),
            ]
            for i, (bx, by) in enumerate(positions):
                if pygame.Rect(bx, by, btn_w, btn_h).collidepoint(pos):
                    game.press_button(i)
                    return

    def _start_single_game(self, index):
        self.current_game_index = index
        self.current_game = self.games_list[index]
        self.current_game.start()
        self.state = "playing"
        self.poses_window = []
        if self.current_game.name == "basket" and self.webcam_view:
            self.webcam_view.set_camera_mode(True)
        elif self.webcam_view:
            self.webcam_view.set_camera_mode(False)

    def _start_full_session(self):
        self.current_game_index = 0
        self.current_game = self.games_list[0]
        self.current_game.start()
        self.state = "playing"
        self.poses_window = []

    def _stop_current_game(self):
        if self.current_game:
            self.current_game.stop()
            result = self.current_game.get_result()
            self.session.log_game(self.current_game.name, result)
            if self.webcam_view:
                self.webcam_view.set_camera_mode(False)

        self.current_game_index += 1
        if self.current_game_index < len(self.games_list):
            self.current_game = self.games_list[self.current_game_index]
            self.current_game.start()
            self.poses_window = []
        else:
            self.current_game = None
            self.state = "finished"

    # ── Update ────────────────────────────────────────────────────

    def _update(self, dt):
        if self.state == "playing" and self.current_game:
            prev = self.prev_pose
            pose_data = self._get_pose()

            if self.fatigue_detector and pose_data:
                self.fatigue_detector.update(pose_data, True)
            if self.fall_risk_detector and pose_data:
                self.fall_risk_detector.evaluate(pose_data, prev)
            if self.facial_expression and self.last_frame_rgb is not None:
                self.facial_expression.update(self.last_frame_rgb)
                self.mood_indicator.update(self.facial_expression)

            self.current_game.update(pose_data, dt)

            if self.current_game.is_finished():
                self._stop_current_game()
                return

            if self.current_game:
                fb = self.current_game.feedback_message
                if fb:
                    self.feedback_bar.set_message(fb)
            self.feedback_bar.update(dt)

    def _get_pose(self):
        if self.pose_detector is None:
            return self._synthetic_pose()

        frame = self.pose_detector.read_frame()
        if frame is not None:
            import cv2
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            self.last_frame_rgb = rgb

        pose_data = self.pose_detector.detect(frame)
        if pose_data:
            self.prev_pose = pose_data
            self.poses_window.append(pose_data)
            if len(self.poses_window) > 30:
                self.poses_window.pop(0)
            frame_shape = frame.shape if frame is not None else None
            if self.current_game and self.current_game.name == "basket":
                self.webcam_view.update_pose(pose_data, frame_shape, rgb)
            else:
                self.webcam_view.update_pose(pose_data, frame_shape)
        return pose_data

    def _synthetic_pose(self):
        t = time.time()
        wobble_x = int(5 * (1 if int(t * 2) % 2 == 0 else -1))
        pose = {
            "in_frame": True,
            "nose": (512 + wobble_x, 200),
            "l_shoulder": (450 + wobble_x, 260),
            "r_shoulder": (574 + wobble_x, 260),
            "l_hip": (470 + wobble_x, 400),
            "r_hip": (554 + wobble_x, 400),
            "l_knee": (465 + wobble_x, 500),
            "r_knee": (559 + wobble_x, 500),
            "l_ankle": (460 + wobble_x, 600),
            "r_ankle": (564 + wobble_x, 600),
            "l_wrist": (390 + wobble_x, 330),
            "r_wrist": (634 + wobble_x, 330),
            "l_elbow": (420 + wobble_x, 300),
            "r_elbow": (604 + wobble_x, 300),
            "shoulder_center": (512 + wobble_x, 260),
            "hip_center": (512 + wobble_x, 400),
            "shoulder_width": 124,
            "trunk_angle": 3.0,
            "instability": 0.05,
            "knee_hip_ratio": 1.5,
            "lm_visibility": [0.99] * 9,
        }
        self.prev_pose = pose
        self.poses_window.append(pose)
        if len(self.poses_window) > 30:
            self.poses_window.pop(0)
        self.webcam_view.update_pose(pose, (480, 640, 3))
        return pose

    # ── Drawing ───────────────────────────────────────────────────

    def _draw_background(self):
        self.bg_time += 0.002
        t = self.bg_time

        for y in range(Layout.H):
            fy = y / Layout.H
            wave = math.sin(t * 2 + fy * 5) * 2
            r = max(0, min(255, 8 + int(wave * fy * 0.8) + int(fy * 6)))
            g = max(0, min(255, 8 + int(wave * fy * 0.4) + int(fy * 4)))
            b = max(0, min(255, 18 + int(wave * 1.2) + int(fy * 10)))
            pygame.draw.line(self.screen, (r, g, b), (0, y), (Layout.W, y))

        for p in self.particles:
            p["x"] += p["vx"]
            p["y"] += p["vy"]
            p["alpha"] += random.uniform(-2, 2)
            p["alpha"] = max(15, min(100, p["alpha"]))
            if p["y"] < -10:
                p["y"] = Layout.H + 10
                p["x"] = random.uniform(0, Layout.W)
            s = pygame.Surface((int(p["r"] * 2), int(p["r"] * 2)), pygame.SRCALPHA)
            pygame.draw.circle(s, (160, 190, 240, int(p["alpha"])),
                               (int(p["r"]), int(p["r"])), int(p["r"]))
            self.screen.blit(s, (int(p["x"]), int(p["y"])))

    def _draw_panel(self, x, y, w, h):
        rect = pygame.Rect(x, y, w, h)
        s = pygame.Surface((w, h), pygame.SRCALPHA)
        for i in range(h):
            t = i / h
            alpha = 200 + int(55 * (1 - t))
            c = (12, 12, 28, alpha)
            pygame.draw.line(s, c, (0, i), (w, i))
        self.screen.blit(s, (x, y))
        pygame.draw.rect(self.screen, self.PANEL_BORDER, rect, 2, border_radius=20)
        pygame.draw.rect(self.screen, (60, 60, 90), rect, 1, border_radius=20)

    def _draw(self):
        self._draw_background()

        if self.state == "menu":
            self._draw_menu()
        elif self.state == "playing":
            self._draw_game()
        elif self.state == "finished":
            self._draw_finished()
        elif self.state == "report":
            self._draw_report()

    # ── Menu ──────────────────────────────────────────────────────

    def _draw_menu(self):
        t = time.time()
        glow = 0.5 + 0.5 * math.sin(t * 1.2)

        self._draw_panel(Layout.GAME_PANEL_X, Layout.GAME_PANEL_Y,
                         Layout.GAME_PANEL_W, Layout.GAME_PANEL_H)

        title_y = Layout.GAME_PANEL_Y + 18
        title_gc = tuple(int(50 + 35 * glow) for _ in range(3))
        title = self.font_title.render("Brain-Move", True, self.ACCENT)
        self.screen.blit(title, (Layout.GC_CX - title.get_width() // 2, title_y))

        subtitle = self.font_small.render(
            "Stimolazione cognitiva e motoria", True, self.TEXT_MUTED)
        self.screen.blit(subtitle, (Layout.GC_CX - subtitle.get_width() // 2, title_y + 55))

        for btn in self.menu_buttons:
            btn.draw(self.screen, self.font_medium)

        if self.pose_detector:
            status = "Webcam: attiva"
            sc = self.SUCCESS
        else:
            status = "Webcam: non disponibile"
            sc = self.WARN
        stxt = self.font_tiny.render(status, True, sc)
        self.screen.blit(stxt, (Layout.SIDEBAR_X, Layout.H - 28))

        name = self.session.profile.get("name", "Utente")
        ntxt = self.font_tiny.render(f"Giocatore: {name}", True, self.TEXT_MUTED)
        self.screen.blit(ntxt, (Layout.W - ntxt.get_width() - 30, Layout.H - 28))

    # ── Game ──────────────────────────────────────────────────────

    def _draw_game(self):
        if self.current_game is None:
            return

        self._draw_panel(Layout.GAME_PANEL_X, Layout.GAME_PANEL_Y,
                         Layout.GAME_PANEL_W, Layout.GAME_PANEL_H)

        self.webcam_view.draw(self.screen)
        self.mood_indicator.draw(self.screen, self.font_large, self.font_small)

        game = self.current_game
        progress = game.get_progress() if hasattr(game, 'get_progress') else 0
        self.progress_bar.progress = progress
        self.progress_bar.draw(self.screen)

        self.feedback_bar.draw(self.screen, self.font_medium)

        title = self.font_large.render(game.display_name, True, self.ACCENT)
        self.screen.blit(title, (Layout.GC_X, Layout.GAME_PANEL_Y + 20))

        self._draw_game_content(game)
        self.back_button.draw(self.screen, self.font_medium)

        level = self.session.difficulty.get_level()
        lvl = self.font_medium.render(f"Livello: {level}", True, self.TEXT_MUTED)
        self.screen.blit(lvl, (Layout.GAME_PANEL_X + Layout.GAME_PANEL_W - 130,
                               Layout.GAME_PANEL_Y + Layout.GAME_PANEL_H - 35))

    def _draw_game_content(self, game):
        name = game.name
        if name == "respiro_faro":
            self._draw_respiro(game)
        elif name == "passi_ricorda":
            self._draw_passi(game)
        elif name == "semaforo_esecutivo":
            self._draw_semaforo(game)
        elif name == "mappa_stanza":
            self._draw_mappa(game)
        elif name == "costruisci_modello":
            self._draw_costruisci(game)
        elif name == "diario_missioni":
            self._draw_diario(game)
        elif name == "memory_carte":
            self._draw_memory(game)
        elif name == "sequenza_simboli":
            self._draw_sequenza(game)
        elif name == "parole_incrociate":
            self._draw_parole(game)
        elif name == "basket":
            self._draw_basket(game)
        elif name == "puzzle":
            self._draw_puzzle(game)
        elif name == "memory_immagini":
            self._draw_memory_immagini(game)
        elif name == "brain_trainer":
            self._draw_brain_trainer(game)
        elif name == "musical_memory":
            self._draw_musical_memory(game)

    def _draw_respiro(self, game):
        scale = game.get_circle_scale()
        max_r = 200
        r = int(max_r * scale)
        cx, cy = Layout.GC_CX, Layout.GC_Y + 360
        t = time.time()
        pulse = 0.5 + 0.5 * math.sin(t * 2)

        for i in range(6, 0, -1):
            cr = r + i * 24 + int(pulse * 10)
            a = max(0, 40 - i * 6)
            c = (40 + i * 5, 90 + a + i * 5, 210 - i * 12)
            pygame.draw.circle(self.screen, c, (cx, cy), cr, max(1, 5 - i // 2))

        color = (60, 210, 120) if game.phase == "inspira" else (220, 160, 60)
        glow_c = tuple(min(v + 60, 255) for v in color)
        for i in range(6, 0, -1):
            a = int(50 / (i + 1))
            s = pygame.Surface((r * 2 + i * 10, r * 2 + i * 10), pygame.SRCALPHA)
            pygame.draw.circle(s, (*glow_c, a), (r + i * 5, r + i * 5), r + i * 5)
            self.screen.blit(s, (cx - r - i * 5, cy - r - i * 5))

        pygame.draw.circle(self.screen, color, (cx, cy), r)
        pygame.draw.circle(self.screen, tuple(min(v + 50, 255) for v in color), (cx, cy), r, 4)

        phase_label = "INSPIRA" if game.phase == "inspira" else "ESPIRA"
        lbl = self.font_large.render(phase_label, True, (255, 255, 255))
        self.screen.blit(lbl, (cx - lbl.get_width() // 2, cy - 25))

        pg = game.get_progress()
        self._draw_progress_ring(cx + 280, Layout.GC_Y + 360, 50, pg)

    def _draw_passi(self, game):
        cx = Layout.GC_CX
        gy = Layout.GC_Y

        if game.phase == "showing":
            item = game.get_current_item()
            if item and item in game.ITEM_ICONS:
                icon = game.ITEM_ICONS[item]
                icon_bg = pygame.Rect(cx - 160, gy + 160, 320, 180)
                s = pygame.Surface((icon_bg.w, icon_bg.h), pygame.SRCALPHA)
                for i in range(icon_bg.h):
                    t = i / icon_bg.h
                    c = (20 + int(15 * t), 20 + int(15 * t), 40 + int(20 * t), 200)
                    pygame.draw.line(s, c, (0, i), (icon_bg.w, i))
                self.screen.blit(s, (icon_bg.x, icon_bg.y))
                pygame.draw.rect(self.screen, (55, 55, 80), icon_bg, 2, border_radius=24)
                txt = self.font_title.render(icon, True, (255, 255, 255))
                self.screen.blit(txt, (cx - txt.get_width() // 2, gy + 200))
        elif game.phase == "moving":
            move_bg = pygame.Rect(cx - 160, gy + 180, 320, 80)
            s = pygame.Surface((move_bg.w, move_bg.h), pygame.SRCALPHA)
            s.fill((15, 25, 15, 200))
            self.screen.blit(s, (move_bg.x, move_bg.y))
            pygame.draw.rect(self.screen, (40, 80, 40), move_bg, 2, border_radius=18)
            txt = self.font_large.render("Cammina sul posto...", True, self.SUCCESS)
            self.screen.blit(txt, (cx - txt.get_width() // 2, gy + 205))

            knee_data = None
            if self.poses_window and self.movement_rules:
                knee_data = self.movement_rules.detect_knee_raise(self.poses_window[-1])
            if knee_data:
                for side, raised in [("Sx", knee_data["left_raised"]), ("Dx", knee_data["right_raised"])]:
                    color = self.SUCCESS if raised else (120, 120, 120)
                    stxt = self.font_medium.render(
                        f"Ginocchio {side}: {'Alzato' if raised else 'Basso'}", True, color)
                    self.screen.blit(stxt, (cx - stxt.get_width() // 2,
                                            gy + 280 + (0 if side == "Sx" else 40)))
        elif game.phase == "recall":
            options = game.get_options()
            cols = min(len(options), 4)
            btn_w, btn_h = 140, 110
            gap = 16
            total_w = cols * (btn_w + gap) - gap
            start_x = cx - total_w // 2
            start_y = gy + 230
            for i, opt in enumerate(options):
                bx = start_x + (i % cols) * (btn_w + gap)
                by = start_y + (i // cols) * (btn_h + gap)
                icon = game.ITEM_ICONS.get(opt, opt)
                rect = pygame.Rect(bx, by, btn_w, btn_h)
                self._draw_card_button(rect, color_bg=(65, 120, 170) if opt not in game.user_answer else (160, 100, 50))
                txt = self.font_large.render(icon, True, (255, 255, 255))
                self.screen.blit(txt, (bx + btn_w // 2 - txt.get_width() // 2,
                                       by + btn_h // 2 - txt.get_height() // 2))

    def _draw_semaforo(self, game):
        cx = Layout.GC_CX
        gy = Layout.GC_Y
        color_data = game.get_color_display()

        score_txt = self.font_medium.render(
            f"Corretti: {game.correct_count}  Errori: {game.inhibition_errors}", True, self.TEXT_MUTED)
        self.screen.blit(score_txt, (Layout.GC_X, gy + 110))

        if color_data:
            cy = gy + 300
            c_map = {"verde": (50, 220, 50), "rosso": (230, 50, 50),
                     "blu": (50, 120, 230), "giallo": (230, 210, 50)}

            t = time.time()
            pulse = 0.5 + 0.5 * math.sin(t * 3)
            color_rgb = c_map.get(game.current_color, (200, 200, 200))

            pygame.draw.circle(self.screen, (25, 25, 40), (cx, cy), 175)
            for i in range(8, 0, -1):
                a = int(25 * pulse / (i + 1))
                s = pygame.Surface((260 + i * 12, 260 + i * 12), pygame.SRCALPHA)
                pygame.draw.circle(s, (*color_rgb, a), (130 + i * 6, 130 + i * 6), 130 + i * 6)
                self.screen.blit(s, (cx - 130 - i * 6, cy - 130 - i * 6))

            pygame.draw.circle(self.screen, (40, 40, 55), (cx, cy), 155)
            pygame.draw.circle(self.screen, color_rgb, (cx, cy), 130)
            pygame.draw.circle(self.screen, tuple(min(v + 60, 255) for v in color_rgb), (cx, cy), 130, 5)

            lbl = self.font_large.render(color_data["label"], True, (255, 255, 255))
            self.screen.blit(lbl, (cx - lbl.get_width() // 2, cy + 170))

            action_hint = {
                "verde": "Fai un passo avanti",
                "rosso": "Resta fermo!",
                "blu": "Passo a sinistra",
                "giallo": "Passo a destra",
            }
            hint = self.font_medium.render(action_hint.get(game.current_color, ""), True, self.TEXT_MUTED)
            self.screen.blit(hint, (cx - hint.get_width() // 2, cy + 220))

    def _draw_mappa(self, game):
        cx = Layout.GC_CX
        gy = Layout.GC_Y
        cell_size = 150
        grid_w = game.grid_size * cell_size
        grid_x = cx - grid_w // 2
        grid_y = gy + 200

        for r in range(game.grid_size):
            for c in range(game.grid_size):
                rect = pygame.Rect(grid_x + c * cell_size, grid_y + r * cell_size,
                                   cell_size - 4, cell_size - 4)
                self._draw_card_button(rect, (35, 35, 60), (80, 80, 110), False)

        if game.phase == "showing":
            for obj, (r, c) in game.object_positions.items():
                icon = game.OBJECTS.get(obj, "?")
                txt = self.font_large.render(icon, True, (255, 255, 255))
                rx = grid_x + c * cell_size + cell_size // 2 - txt.get_width() // 2
                ry = grid_y + r * cell_size + cell_size // 2 - txt.get_height() // 2
                bg = pygame.Rect(rx - 10, ry - 6, txt.get_width() + 20, txt.get_height() + 12)
                s = pygame.Surface((bg.w, bg.h), pygame.SRCALPHA)
                s.fill((40, 40, 70, 200))
                self.screen.blit(s, (bg.x, bg.y))
                pygame.draw.rect(self.screen, (90, 90, 130), bg, 2, border_radius=10)
                self.screen.blit(txt, (rx, ry))
        elif game.phase == "recall":
            objs = game.get_objects_to_place()
            if objs:
                hint = self.font_large.render(
                    f"Posiziona: {game.OBJECTS.get(objs[0], objs[0])}", True, self.WARN)
                self.screen.blit(hint, (cx - hint.get_width() // 2, gy + 140))

            for obj, (r, c) in game.user_positions.items():
                icon = game.OBJECTS.get(obj, "?")
                txt = self.font_medium.render(icon, True, self.SUCCESS)
                rx = grid_x + c * cell_size + cell_size // 2 - txt.get_width() // 2
                ry = grid_y + r * cell_size + cell_size // 2 - txt.get_height() // 2
                bg = pygame.Rect(rx - 8, ry - 4, txt.get_width() + 16, txt.get_height() + 8)
                s = pygame.Surface((bg.w, bg.h), pygame.SRCALPHA)
                s.fill((25, 55, 25, 200))
                self.screen.blit(s, (bg.x, bg.y))
                pygame.draw.rect(self.screen, (60, 180, 60), bg, 2, border_radius=8)
                self.screen.blit(txt, (rx, ry))

    def _draw_costruisci(self, game):
        cx = Layout.GC_CX
        gy = Layout.GC_Y

        if game.phase == "showing":
            model = game.get_model_preview()
            if model:
                txt = self.font_large.render("Ricorda il modello:", True, self.TEXT_MUTED)
                self.screen.blit(txt, (cx - txt.get_width() // 2, gy + 170))
                piece_w, piece_h = 140, 90
                gap = 16
                total_w = len(model) * (piece_w + gap) - gap
                start_x = cx - total_w // 2
                for i, piece in enumerate(model):
                    info = game.SHAPES.get(piece, {})
                    color = info.get("color", (200, 200, 200))
                    rect = pygame.Rect(start_x + i * (piece_w + gap), gy + 230, piece_w, piece_h)
                    self._draw_card_button(rect, color, tuple(min(v + 50, 255) for v in color))
                    lbl = self.font_medium.render(info.get("label", piece)[:10], True, (255, 255, 255))
                    self.screen.blit(lbl, (rect.centerx - lbl.get_width() // 2,
                                            rect.centery - lbl.get_height() // 2))
        elif game.phase == "building":
            txt = self.font_large.render("Seleziona i pezzi:", True, self.TEXT_MUTED)
            self.screen.blit(txt, (cx - txt.get_width() // 2, gy + 170))
            pieces = game.get_available_pieces()
            piece_w, piece_h = 140, 90
            gap = 16
            total_w = len(pieces) * (piece_w + gap) - gap
            start_x = cx - total_w // 2
            for i, piece in enumerate(pieces):
                info = game.SHAPES.get(piece, {})
                color = info.get("color", (200, 200, 200))
                rect = pygame.Rect(start_x + i * (piece_w + gap), gy + 250, piece_w, piece_h)
                self._draw_card_button(rect, color, tuple(min(v + 50, 255) for v in color))
                lbl = self.font_medium.render(info.get("label", piece)[:10], True, (255, 255, 255))
                self.screen.blit(lbl, (rect.centerx - lbl.get_width() // 2,
                                        rect.centery - lbl.get_height() // 2))

            if game.user_pieces:
                txt2 = self.font_medium.render(
                    f"Pezzi piazzati: {len(game.user_pieces)}/{len(game.model_pieces)}",
                    True, self.SUCCESS)
                self.screen.blit(txt2, (cx - txt2.get_width() // 2, gy + 380))

    def _draw_diario(self, game):
        cx = Layout.GC_CX
        gy = Layout.GC_Y

        if game.phase == "questions":
            q = game.get_current_question()
            if q:
                bg_q = pygame.Rect(cx - 360, gy + 170, 720, 60)
                s = pygame.Surface((bg_q.w, bg_q.h), pygame.SRCALPHA)
                s.fill((20, 20, 40, 220))
                self.screen.blit(s, (bg_q.x, bg_q.y))
                pygame.draw.rect(self.screen, (50, 50, 80), bg_q, 2, border_radius=14)
                txt = self.font_large.render(q, True, self.TEXT)
                self.screen.blit(txt, (cx - txt.get_width() // 2, gy + 180))

                answers = ["Molto", "Abbastanza", "Poco"]
                btn_w = 180
                total_w = 3 * btn_w + 2 * 24
                start_x = cx - total_w // 2
                colors = [self.SUCCESS, self.ACCENT, self.WARN]
                for i, ans in enumerate(answers):
                    rect = pygame.Rect(start_x + i * (btn_w + 24), gy + 280, btn_w, 70)
                    self._draw_card_button(rect, colors[i], tuple(min(v + 50, 255) for v in colors[i]))
                    atxt = self.font_large.render(ans, True, (255, 255, 255))
                    self.screen.blit(atxt, (rect.centerx - atxt.get_width() // 2,
                                             rect.centery - atxt.get_height() // 2))

        elif game.phase == "caregiver":
            txt = self.font_large.render("Osservazioni caregiver:", True, self.TEXT_MUTED)
            self.screen.blit(txt, (cx - txt.get_width() // 2, gy + 190))
            notes = game.get_caregiver_options()
            cols = min(3, len(notes))
            btn_w, btn_h = 200, 65
            gap = 16
            total_w = cols * (btn_w + gap) - gap
            start_x = cx - total_w // 2
            for i, note in enumerate(notes):
                rect = pygame.Rect(start_x + (i % cols) * (btn_w + gap),
                                   gy + 250 + (i // cols) * (btn_h + gap), btn_w, btn_h)
                selected = note in game.caregiver_notes
                c = (40, 140, 40) if selected else (50, 50, 80)
                self._draw_card_button(rect, c, (80, 200, 80) if selected else (90, 90, 130))
                lbl = self.font_medium.render(note.replace("_", " "), True, self.TEXT)
                self.screen.blit(lbl, (rect.centerx - lbl.get_width() // 2,
                                        rect.centery - lbl.get_height() // 2))

            done_rect = pygame.Rect(cx - 130, gy + 500, 260, 65)
            self._draw_card_button(done_rect, (40, 160, 40), (80, 220, 80))
            dtxt = self.font_large.render("Completa", True, self.TEXT)
            self.screen.blit(dtxt, (done_rect.centerx - dtxt.get_width() // 2,
                                     done_rect.centery - dtxt.get_height() // 2))

    def _draw_parole(self, game):
        cx = Layout.GC_CX
        gy = Layout.GC_Y
        cell_size = 74
        grid_w = game.grid_size * cell_size
        grid_x = cx - grid_w // 2
        grid_y = gy + 130

        grid_bg = pygame.Rect(grid_x - 8, grid_y - 8, grid_w + 16, grid_w + 16)
        s = pygame.Surface((grid_bg.w, grid_bg.h), pygame.SRCALPHA)
        s.fill((15, 15, 30, 220))
        self.screen.blit(s, (grid_bg.x, grid_bg.y))
        pygame.draw.rect(self.screen, (40, 40, 65), grid_bg, 2, border_radius=14)

        for r in range(game.grid_size):
            for c in range(game.grid_size):
                bx = grid_x + c * cell_size
                by = grid_y + r * cell_size
                rect = pygame.Rect(bx, by, cell_size - 2, cell_size - 2)

                is_current = False
                word_info = game.get_current_word()
                if word_info and not word_info["solved"]:
                    wr, wc = word_info["row"], word_info["col"]
                    for i in range(len(word_info["word"])):
                        if word_info["direction"] == "across":
                            if (wr, wc + i) == (r, c):
                                is_current = True
                        else:
                            if (wr + i, wc) == (r, c):
                                is_current = True

                if game.get_grid()[r][c]:
                    if is_current:
                        self._draw_card_button(rect, (50, 100, 180), (100, 180, 240))
                    else:
                        self._draw_card_button(rect, (45, 45, 80), (90, 90, 140))
                    txt = self.font_large.render(game.get_grid()[r][c], True, self.TEXT)
                    self.screen.blit(txt, (bx + cell_size // 2 - txt.get_width() // 2,
                                            by + cell_size // 2 - txt.get_height() // 2))
                else:
                    pygame.draw.rect(self.screen, (20, 20, 35), rect, border_radius=8)

        word_info = game.get_current_word()
        if word_info and not word_info["solved"]:
            user_input, sel = game.get_current_word_display()
            word_display = "".join(user_input).strip()
            hint_y = grid_y + grid_w + 20
            word_bg = pygame.Rect(cx - 240, hint_y - 8, 480, 50)
            s = pygame.Surface((word_bg.w, word_bg.h), pygame.SRCALPHA)
            s.fill((20, 20, 40, 220))
            self.screen.blit(s, (word_bg.x, word_bg.y))
            pygame.draw.rect(self.screen, (50, 50, 80), word_bg, 2, border_radius=10)
            hint_txt = self.font_large.render(f"Parola: {word_display}_", True, self.WARN)
            self.screen.blit(hint_txt, (cx - hint_txt.get_width() // 2, hint_y))

            check_btn = pygame.Rect(cx + grid_w // 2 + 30, grid_y + grid_w + 20, 200, 55)
            self._draw_card_button(check_btn, (45, 140, 45), (90, 210, 90))
            btn_txt = self.font_large.render("Verifica", True, self.TEXT)
            self.screen.blit(btn_txt, (check_btn.centerx - btn_txt.get_width() // 2,
                                        check_btn.centery - btn_txt.get_height() // 2))

        hints = game.get_hints()
        hints_x = grid_x + grid_w + 30
        hints_y = grid_y
        ht = self.font_medium.render("Indizi:", True, self.ACCENT)
        self.screen.blit(ht, (hints_x, hints_y))
        hints_y += 40
        for hint in hints:
            solved = "✓" in hint
            color = self.SUCCESS if solved else self.TEXT_MUTED
            ht2 = self.font_small.render(hint, True, color)
            self.screen.blit(ht2, (hints_x, hints_y))
            hints_y += 35

        info = self.font_medium.render(
            f"Parole: {game.correct_words}/{game.total_words}", True, self.TEXT_MUTED)
        self.screen.blit(info, (Layout.GC_X, gy + 110))

    def _draw_basket(self, game):
        cx = Layout.GC_CX
        gy = Layout.GC_Y
        hoop_x, hoop_y, hoop_r = game.get_hoop_pos()
        hx = int(cx - 200 + hoop_x * 400)
        hy = int(gy + 100 + hoop_y * 400)

        pole_rect = pygame.Rect(hx - 3, hy + 12, 6, 250)
        pygame.draw.rect(self.screen, (120, 120, 130), pole_rect, border_radius=2)
        for glow_r in range(hoop_r + 8, hoop_r + 25, 4):
            a = max(5, 40 - (glow_r - hoop_r) * 5)
            s = pygame.Surface((glow_r * 2, glow_r * 2), pygame.SRCALPHA)
            pygame.draw.circle(s, (200, 100, 50, a), (glow_r, glow_r), glow_r, 3)
            self.screen.blit(s, (hx - glow_r, hy - glow_r))
        pygame.draw.circle(self.screen, (220, 120, 60), (hx, hy), hoop_r, 4)
        pygame.draw.ellipse(self.screen, (220, 120, 60),
                           (hx - hoop_r, hy - 6, hoop_r * 2, 12), 3)

        ball_pos = game.get_ball_pos()
        if ball_pos and game.phase != "instruction":
            bx, by = int(ball_pos[0]), int(ball_pos[1])
            for glow_r in range(25, 35, 4):
                a = max(5, 30 - (glow_r - 25) * 5)
                s = pygame.Surface((glow_r * 2, glow_r * 2), pygame.SRCALPHA)
                pygame.draw.circle(s, (230, 120, 30, a), (glow_r, glow_r), glow_r)
                self.screen.blit(s, (bx - glow_r, by - glow_r))
            pygame.draw.circle(self.screen, (240, 130, 40), (bx, by), 20)
            pygame.draw.circle(self.screen, (200, 90, 20), (bx, by), 20, 3)
            pygame.draw.line(self.screen, (180, 80, 20), (bx - 14, by), (bx + 14, by), 2)
            pygame.draw.arc(self.screen, (180, 80, 20),
                           (bx - 20, by - 20, 40, 40), 0.5, 2.5, 2)

        trail = game.get_ball_trail()
        if len(trail) > 1:
            for i in range(1, len(trail)):
                alpha = i / len(trail)
                c = (int(200 * alpha), int(100 * alpha), int(30 * alpha))
                p1 = (int(trail[i-1][0]), int(trail[i-1][1]))
                p2 = (int(trail[i][0]), int(trail[i][1]))
                pygame.draw.line(self.screen, c, p1, p2, max(1, int(3 * alpha)))

        hand_label = "DESTRA" if game.throw_hand == "right" else "SINISTRA"
        hand_color = (100, 200, 255) if game.throw_hand == "right" else (255, 200, 100)
        hand_bg = pygame.Rect(Layout.GC_X, gy + 110, 300, 45)
        s = pygame.Surface((hand_bg.w, hand_bg.h), pygame.SRCALPHA)
        s.fill((20, 20, 40, 220))
        self.screen.blit(s, (hand_bg.x, hand_bg.y))
        pygame.draw.rect(self.screen, (50, 50, 80), hand_bg, 2, border_radius=10)
        ht = self.font_large.render(f"Mano: {hand_label}", True, hand_color)
        self.screen.blit(ht, (hand_bg.x + 10, hand_bg.y + 6))

        stats = self.font_medium.render(
            f"Tiri: {game.correct_count}/{game.total_attempts}", True, self.TEXT_MUTED)
        self.screen.blit(stats, (Layout.GC_X, gy + 170))

        if game.score_display:
            st = self.font_large.render(game.score_display, True, self.WARN)
            self.screen.blit(st, (cx - st.get_width() // 2, gy + 600))

    def _draw_puzzle(self, game):
        cx = Layout.GC_CX
        gy = Layout.GC_Y
        if game.phase == "instruction" or not game.current_grid or not game.target_grid:
            txt = self.font_large.render("Preparazione del puzzle...", True, self.ACCENT)
            self.screen.blit(txt, (cx - txt.get_width() // 2, gy + 200))
            return
        cell_size = min(100, int(Layout.GC_W * 0.5 // game.grid_size))
        grid_w = cell_size * game.grid_size
        start_x = cx - grid_w // 2
        start_y = gy + 140

        target_x = start_x + grid_w + 40
        target_y = start_y
        tg = self.font_small.render("Modello:", True, self.ACCENT)
        self.screen.blit(tg, (target_x, target_y))

        for r in range(game.grid_size):
            for c in range(game.grid_size):
                bx = start_x + c * cell_size
                by = start_y + r * cell_size
                rect = pygame.Rect(bx, by, cell_size - 2, cell_size - 2)

                if game.is_selected(r, c):
                    self._draw_card_button(rect, (60, 140, 200), (120, 210, 250))
                elif game.current_grid[r][c] == game.target_grid[r][c]:
                    self._draw_card_button(rect, (25, 45, 25), (50, 130, 50))
                else:
                    self._draw_card_button(rect, (35, 35, 60), (70, 70, 100))

                txt = self.font_large.render(game.current_grid[r][c], True, self.TEXT)
                self.screen.blit(txt, (bx + cell_size // 2 - txt.get_width() // 2,
                                        by + cell_size // 2 - txt.get_height() // 2))

                tr = pygame.Rect(target_x, target_y + (r + 1) * 5 + r * cell_size,
                                 cell_size - 2, cell_size - 2)
                pygame.draw.rect(self.screen, (25, 25, 45), tr, border_radius=6)
                pygame.draw.rect(self.screen, (70, 70, 100), tr, 1, border_radius=6)
                tt = self.font_medium.render(game.target_grid[r][c], True, self.TEXT_MUTED)
                self.screen.blit(tt, (tr.centerx - tt.get_width() // 2,
                                       tr.centery - tt.get_height() // 2))

        hint_btn = pygame.Rect(cx - 90, start_y + grid_w + 30, 180, 50)
        self._draw_card_button(hint_btn, (110, 90, 35), (170, 150, 70))
        ht = self.font_small.render(f"Indizio ({game.max_hints - game.hint_count})", True, self.TEXT)
        self.screen.blit(ht, (hint_btn.centerx - ht.get_width() // 2,
                               hint_btn.centery - ht.get_height() // 2))

        info = self.font_small.render(f"Mosse: {game.total_moves}", True, self.TEXT_MUTED)
        self.screen.blit(info, (Layout.GC_X, start_y + grid_w + 80))

    def _draw_memory_immagini(self, game):
        if game.phase == "instruction":
            txt = self.font_large.render("Preparati a memorizzare le immagini!", True, self.ACCENT)
            self.screen.blit(txt, (Layout.GC_CX - txt.get_width() // 2, Layout.GC_Y + 200))
        elif game.phase == "study":
            self._draw_memory_immagini_study(game)
        elif game.phase == "playing":
            self._draw_memory_immagini_game(game)

    def _draw_memory_immagini_study(self, game):
        cx = Layout.GC_CX
        gy = Layout.GC_Y
        txt = self.font_large.render("Memorizza le immagini!", True, self.WARN)
        self.screen.blit(txt, (cx - txt.get_width() // 2, gy + 110))

        cols = game.grid_cols
        card_w, card_h = 110, 110
        gap = 12
        total_w = cols * (card_w + gap) - gap
        start_x = cx - total_w // 2
        start_y = gy + 160

        for idx in range(len(game.cards)):
            r = idx // cols
            c = idx % cols
            bx = start_x + c * (card_w + gap)
            by = start_y + r * (card_h + gap)
            rect = pygame.Rect(bx, by, card_w, card_h)
            self._draw_card_button(rect, (70, 50, 90), (130, 110, 160))
            txt = self.font_large.render(game.get_card_icon(idx), True, self.TEXT)
            self.screen.blit(txt, (bx + card_w // 2 - txt.get_width() // 2,
                                    by + card_h // 2 - txt.get_height() // 2))

    def _draw_memory_immagini_game(self, game):
        cx = Layout.GC_CX
        gy = Layout.GC_Y
        cols = game.grid_cols
        card_w, card_h = 110, 110
        gap = 12
        total_w = cols * (card_w + gap) - gap
        start_x = cx - total_w // 2
        start_y = gy + 150

        for idx in range(len(game.cards)):
            r = idx // cols
            c = idx % cols
            bx = start_x + c * (card_w + gap)
            by = start_y + r * (card_h + gap)
            rect = pygame.Rect(bx, by, card_w, card_h)

            if game.is_card_matched(idx):
                self._draw_card_button(rect, (35, 90, 35), (60, 190, 60))
                txt = self.font_large.render(game.get_card_icon(idx), True, self.TEXT)
                self.screen.blit(txt, (bx + card_w // 2 - txt.get_width() // 2,
                                        by + card_h // 2 - txt.get_height() // 2))
            elif game.is_card_revealed(idx):
                self._draw_card_button(rect, (150, 100, 40), (210, 170, 90))
                txt = self.font_large.render(game.get_card_icon(idx), True, self.TEXT)
                self.screen.blit(txt, (bx + card_w // 2 - txt.get_width() // 2,
                                        by + card_h // 2 - txt.get_height() // 2))
            else:
                self._draw_card_button(rect, (40, 40, 70), (80, 80, 130))
                txt = self.font_large.render("?", True, self.TEXT_MUTED)
                self.screen.blit(txt, (bx + card_w // 2 - txt.get_width() // 2,
                                        by + card_h // 2 - txt.get_height() // 2))

        info = self.font_medium.render(
            f"Coppie: {game.pairs_found}/{game.total_pairs}  Tentativi: {game.attempts}",
            True, self.TEXT_MUTED)
        self.screen.blit(info, (Layout.GC_X, gy + 110))

    def _draw_brain_trainer(self, game):
        cx = Layout.GC_CX
        gy = Layout.GC_Y

        if game.phase == "instruction":
            txt = self.font_large.render("Preparati per le sfide mentali!", True, self.ACCENT)
            self.screen.blit(txt, (cx - txt.get_width() // 2, gy + 200))
            return

        if game.phase == "result":
            res = self.font_large.render(game.show_result, True, self.WARN)
            self.screen.blit(res, (cx - res.get_width() // 2, gy + 200))
            return

        q = game.current_question
        if not q:
            return

        if q["type"] == "math":
            txt = self.font_large.render(q["text"], True, self.TEXT)
            self.screen.blit(txt, (cx - txt.get_width() // 2, gy + 170))
            opts = game.get_question_options()
            for i, opt in enumerate(opts):
                bx = cx - 200 + (i % 2) * 210
                by = gy + 260 + (i // 2) * 95
                rect = pygame.Rect(bx, by, 190, 75)
                self._draw_card_button(rect, (50, 90, 150), (100, 150, 210))
                ot = self.font_large.render(str(opt), True, self.TEXT)
                self.screen.blit(ot, (bx + 95 - ot.get_width() // 2,
                                       by + 37 - ot.get_height() // 2))

        elif q["type"] == "recall":
            txt = self.font_large.render(q["text"], True, self.TEXT)
            self.screen.blit(txt, (cx - txt.get_width() // 2, gy + 120))

            for i, item in enumerate(q["items"]):
                bx = cx - len(q["items"]) * 40 + i * 80
                by = gy + 180
                rect = pygame.Rect(bx, by, 70, 70)
                self._draw_card_button(rect, (45, 45, 75), (90, 90, 140))
                if item == q["highlight"]:
                    pygame.draw.rect(self.screen, (200, 200, 80), rect, 3, border_radius=12)
                it = self.font_large.render(item, True, self.TEXT)
                self.screen.blit(it, (bx + 35 - it.get_width() // 2,
                                       by + 35 - it.get_height() // 2))

            opts = game.get_question_options()
            for i, opt in enumerate(opts):
                bx = cx - len(opts) * 40 + i * 80
                by = gy + 280
                rect = pygame.Rect(bx, by, 70, 70)
                self._draw_card_button(rect, (50, 90, 150), (100, 150, 210))
                ot = self.font_large.render(opt, True, self.TEXT)
                self.screen.blit(ot, (bx + 35 - ot.get_width() // 2,
                                       by + 35 - ot.get_height() // 2))

        elif q["type"] == "count":
            txt = self.font_large.render(q["text"], True, self.TEXT)
            self.screen.blit(txt, (cx - txt.get_width() // 2, gy + 130))
            for i, sym in enumerate(q["symbols"]):
                sx = cx - len(q["symbols"]) * 25 + (i % 10) * 55
                sy = gy + 190 + (i // 10) * 60
                st = self.font_large.render(sym, True, self.TEXT)
                self.screen.blit(st, (sx, sy))
            opts = game.get_question_options()
            for i, opt in enumerate(opts):
                bx = cx - 200 + (i % 2) * 210
                by = gy + 320 + (i // 2) * 85
                rect = pygame.Rect(bx, by, 190, 70)
                self._draw_card_button(rect, (50, 90, 150), (100, 150, 210))
                ot = self.font_large.render(str(opt), True, self.TEXT)
                self.screen.blit(ot, (bx + 95 - ot.get_width() // 2,
                                       by + 35 - ot.get_height() // 2))

        score = self.font_medium.render(
            f"Round {game.round}/{game.total_rounds}  Corretti: {game.correct_count}",
            True, self.TEXT_MUTED)
        self.screen.blit(score, (Layout.GC_X, gy + 110))

    def _draw_musical_memory(self, game):
        cx = Layout.GC_CX
        gy = Layout.GC_Y

        if game.phase == "instruction":
            txt = self.font_large.render("Ripeti la sequenza musicale!", True, self.ACCENT)
            self.screen.blit(txt, (cx - txt.get_width() // 2, gy + 200))
            return

        colors = [(230, 60, 60), (60, 130, 230), (60, 200, 60), (230, 210, 50)]
        labels = ["Do", "Mi", "Sol", "Do'"]
        btn_w, btn_h = 150, 130
        gap = 30
        positions = [
            (cx - btn_w // 2 - gap - btn_w // 2, gy + 170),
            (cx + gap + btn_w // 2 - btn_w // 2, gy + 170),
            (cx - btn_w // 2 - gap - btn_w // 2, gy + 170 + btn_h + gap),
            (cx + gap + btn_w // 2 - btn_w // 2, gy + 170 + btn_h + gap),
        ]

        for i in range(4):
            bx, by = positions[i]
            rect = pygame.Rect(bx, by, btn_w, btn_h)

            if game.get_flash_note() == i:
                c = tuple(min(v + 80, 255) for v in colors[i])
                for g in range(6, 0, -1):
                    a = int(70 / (g + 1))
                    s = pygame.Surface((btn_w + g * 8, btn_h + g * 8), pygame.SRCALPHA)
                    pygame.draw.rect(s, (*c, a), (0, 0, s.get_width(), s.get_height()),
                                     border_radius=22 + g)
                    self.screen.blit(s, (bx - g * 4, by - g * 4))
                self._draw_card_button(rect, c, (255, 255, 255))
            else:
                self._draw_card_button(rect, colors[i], tuple(min(v + 50, 255) for v in colors[i]))

            lb = self.font_medium.render(labels[i], True, (255, 255, 255))
            self.screen.blit(lb, (bx + btn_w // 2 - lb.get_width() // 2,
                                   by + btn_h // 2 - lb.get_height() // 2))

        if game.phase == "input":
            inp = self.font_medium.render(
                f"Ripeti: {game.input_index + 1}/{len(game.sequence)}", True, self.TEXT_MUTED)
            self.screen.blit(inp, (Layout.GC_X, gy + 110))

        rnd = self.font_medium.render(
            f"Round: {game.round}/{game.max_rounds}", True, self.TEXT_MUTED)
        self.screen.blit(rnd, (cx - rnd.get_width() // 2, gy + 500))

    def _draw_progress_ring(self, x, y, radius, progress):
        for angle in range(0, 360, 3):
            rad = math.radians(angle - 90)
            fill_angle = progress * 360
            if angle <= fill_angle:
                color = self.SUCCESS
                r = 6
            else:
                color = (30, 30, 45)
                r = 5
            ex = x + int(radius * math.cos(rad))
            ey = y + int(radius * math.sin(rad))
            pygame.draw.circle(self.screen, color, (ex, ey), r)

    def _draw_memory(self, game):
        cx = Layout.GC_CX
        gy = Layout.GC_Y
        rows, cols = game.get_grid_size()
        card_w, card_h = 130, 130
        gap = 16
        total_w = cols * (card_w + gap) - gap
        start_x = cx - total_w // 2
        start_y = gy + 140

        for r in range(rows):
            for c in range(cols):
                idx = r * cols + c
                bx = start_x + c * (card_w + gap)
                by = start_y + r * (card_h + gap)
                rect = pygame.Rect(bx, by, card_w, card_h)

                if game.is_card_matched(idx):
                    self._draw_card_button(rect, (30, 110, 30), (70, 200, 70))
                    symbol = game.get_card_symbol(idx)
                    txt = self.font_large.render(symbol, True, self.TEXT)
                    self.screen.blit(txt, (bx + card_w // 2 - txt.get_width() // 2,
                                            by + card_h // 2 - txt.get_height() // 2))
                elif game.is_card_revealed(idx):
                    self._draw_card_button(rect, (160, 110, 40), (210, 170, 90))
                    symbol = game.get_card_symbol(idx)
                    txt = self.font_large.render(symbol, True, self.TEXT)
                    self.screen.blit(txt, (bx + card_w // 2 - txt.get_width() // 2,
                                            by + card_h // 2 - txt.get_height() // 2))
                else:
                    self._draw_card_button(rect, (40, 40, 75), (80, 80, 130))
                    txt = self.font_large.render("?", True, self.TEXT_MUTED)
                    self.screen.blit(txt, (bx + card_w // 2 - txt.get_width() // 2,
                                            by + card_h // 2 - txt.get_height() // 2))

        info = self.font_medium.render(
            f"Coppie: {game.pairs_found}/{game.total_pairs}  Tentativi: {game.attempts}",
            True, self.TEXT_MUTED)
        self.screen.blit(info, (Layout.GC_X, gy + 110))

    def _draw_sequenza(self, game):
        cx = Layout.GC_CX
        gy = Layout.GC_Y

        if game.phase == "showing":
            item = game.get_current_show_item()
            if item:
                icon_bg = pygame.Rect(cx - 150, gy + 170, 300, 200)
                s = pygame.Surface((icon_bg.w, icon_bg.h), pygame.SRCALPHA)
                s.fill((18, 18, 38, 220))
                self.screen.blit(s, (icon_bg.x, icon_bg.y))
                pygame.draw.rect(self.screen, (50, 50, 80), icon_bg, 2, border_radius=24)
                txt = self.font_title.render(item, True, self.TEXT)
                self.screen.blit(txt, (cx - txt.get_width() // 2, gy + 230))

                progress_txt = self.font_medium.render(
                    f"Mostra: {game.show_index + 1}/{len(game.sequence)}", True, self.TEXT_MUTED)
                self.screen.blit(progress_txt, (cx - progress_txt.get_width() // 2, gy + 400))

        elif game.phase == "input":
            symbols = game.get_available_symbols()
            btn_w, btn_h = 120, 120
            gap = 16
            cols = min(len(symbols), 4)
            total_w = cols * (btn_w + gap) - gap
            start_x = cx - total_w // 2
            start_y = gy + 250
            for i, (sym_key, sym_icon) in enumerate(symbols):
                bx = start_x + (i % cols) * (btn_w + gap)
                by = start_y + (i // cols) * (btn_h + gap)
                rect = pygame.Rect(bx, by, btn_w, btn_h)
                self._draw_card_button(rect, (55, 110, 160), (100, 160, 210))
                txt = self.font_large.render(sym_icon, True, self.TEXT)
                self.screen.blit(txt, (bx + btn_w // 2 - txt.get_width() // 2,
                                        by + btn_h // 2 - txt.get_height() // 2))

            seq_len = len(game.sequence)
            done = len(game.user_sequence)
            progress_txt = self.font_medium.render(
                f"Ripeti: {done}/{seq_len}", True, self.SUCCESS)
            self.screen.blit(progress_txt, (cx - progress_txt.get_width() // 2, gy + 210))

        elif game.phase == "correct_flash":
            fb = pygame.Rect(cx - 160, gy + 200, 320, 150)
            s = pygame.Surface((fb.w, fb.h), pygame.SRCALPHA)
            s.fill((15, 45, 15, 220))
            self.screen.blit(s, (fb.x, fb.y))
            pygame.draw.rect(self.screen, self.SUCCESS, fb, 3, border_radius=22)
            txt = self.font_title.render("Corretto!", True, self.SUCCESS)
            self.screen.blit(txt, (cx - txt.get_width() // 2, gy + 250))

        elif game.phase == "wrong_flash":
            fb = pygame.Rect(cx - 160, gy + 200, 320, 150)
            s = pygame.Surface((fb.w, fb.h), pygame.SRCALPHA)
            s.fill((45, 15, 15, 220))
            self.screen.blit(s, (fb.x, fb.y))
            pygame.draw.rect(self.screen, (200, 60, 60), fb, 3, border_radius=22)
            txt = self.font_title.render("Sbagliato!", True, (230, 80, 80))
            self.screen.blit(txt, (cx - txt.get_width() // 2, gy + 250))

        rnd, total = game.get_round_info()
        round_txt = self.font_medium.render(f"Round: {rnd}/{total}", True, self.TEXT_MUTED)
        self.screen.blit(round_txt, (Layout.GC_X, gy + 110))

    # ── Helper ────────────────────────────────────────────────────

    def _draw_card_button(self, rect, color_bg, color_border=None, shadow=True):
        if color_border is None:
            color_border = tuple(min(v + 50, 255) for v in color_bg)
        if shadow:
            s = pygame.Surface((rect.w + 4, rect.h + 4), pygame.SRCALPHA)
            pygame.draw.rect(s, (0, 0, 0, 60), (4, 4, rect.w, rect.h), border_radius=14)
            self.screen.blit(s, (rect.x - 2, rect.y - 2))
        s = pygame.Surface((rect.w, rect.h), pygame.SRCALPHA)
        for i in range(rect.h):
            t = i / rect.h if rect.h > 0 else 1
            c = tuple(min(255, int(a + (b - a) * t)) for a, b in zip(
                tuple(min(v + 30, 255) for v in color_bg), color_bg))
            pygame.draw.line(s, c, (0, i), (rect.w, i))
        self.screen.blit(s, (rect.x, rect.y))
        pygame.draw.rect(self.screen, color_border, rect, 2, border_radius=14)

    # ── Finished ──────────────────────────────────────────────────

    def _draw_finished(self):
        if self.session_summary is None:
            self.session_summary = self.session.end()

        summary = self.session_summary
        t = time.time()
        glow = 0.5 + 0.5 * math.sin(t * 1.5)

        title = self.font_title.render("Sessione Completata!", True, self.SUCCESS)
        self.screen.blit(title, (Layout.GC_CX - title.get_width() // 2, 60))

        stats_panel = pygame.Rect(100, 130, Layout.W - 200, 140)
        self._draw_panel(stats_panel.x, stats_panel.y, stats_panel.w, stats_panel.h)

        y = 150
        duration = summary.get("duration_seconds", 0)
        mins = int(duration // 60)
        secs = int(duration % 60)
        info_lines = [
            f"Durata: {mins} min {secs} sec",
            f"Punteggio totale: {summary.get('total_score', 0)}",
            f"Difficolta finale: {summary.get('final_difficulty', 1)}",
        ]
        for line in info_lines:
            txt = self.font_large.render(line, True, self.TEXT)
            self.screen.blit(txt, (140, y))
            y += 45

        games_panel = pygame.Rect(100, 290, Layout.W - 200, 560)
        self._draw_panel(games_panel.x, games_panel.y, games_panel.w, games_panel.h)

        y2 = 305
        txt = self.font_large.render("Risultati giochi:", True, self.ACCENT)
        self.screen.blit(txt, (140, y2))
        y2 += 50

        game_names = {
            "respiro_faro": "Respiro del Faro",
            "passi_ricorda": "Passi e Ricorda",
            "semaforo_esecutivo": "Semaforo Esecutivo",
            "mappa_stanza": "Mappa della Stanza",
            "costruisci_modello": "Costruisci il Modello",
            "diario_missioni": "Diario delle Missioni",
            "memory_carte": "Memory Carte",
            "sequenza_simboli": "Sequenza Simboli",
            "parole_incrociate": "Parole Incrociate",
            "basket": "Basket",
            "puzzle": "Puzzle",
            "memory_immagini": "Memory Immagini",
            "brain_trainer": "Brain Trainer",
            "musical_memory": "Musical Memory",
        }
        for g in summary.get("games", []):
            game_key = g.get("game", "")
            game_label = game_names.get(game_key, game_key)
            result = g.get("result", {})
            acc = result.get("accuracy", None)
            if isinstance(acc, float):
                acc_str = f"{acc:.0%}"
            elif acc is not None:
                acc_str = str(acc)
            else:
                acc_str = "completato"
            line = f"  {game_label}: livello {g.get('difficulty', '?')}, accuratezza {acc_str}"
            txt = self.font_medium.render(line, True, self.TEXT_MUTED)
            self.screen.blit(txt, (160, y2))
            y2 += 42

        btn_menu = Button(Layout.GC_CX - 260, Layout.H - 85, 230, 60,
                          "Torna al Menu", (100, 100, 140))
        btn_report = Button(Layout.GC_CX + 30, Layout.H - 85, 230, 60,
                            "Guarda Report", self.ACCENT2)
        btn_menu.draw(self.screen, self.font_medium)
        btn_report.draw(self.screen, self.font_medium)
        self.game_buttons = [btn_menu, btn_report]

    def _cleanup(self):
        if self.pose_detector:
            self.pose_detector.close()
        if self.facial_expression:
            self.facial_expression.close()
        pygame.quit()

    def _load_report(self):
        data_dir = Path(__file__).parent.parent / "data"
        sessions = []
        if data_dir.exists():
            for f in sorted(data_dir.glob("session_*.json")):
                try:
                    import json
                    with open(f) as fh:
                        data = json.load(fh)
                    sessions.append(data)
                except Exception:
                    pass
        self.report_data = sessions
        self.state = "report"
        self.game_buttons = []

    def _draw_report(self):
        title = self.font_title.render("Report e Progressi", True, self.ACCENT2)
        self.screen.blit(title, (Layout.GC_CX - title.get_width() // 2, 30))

        sessions = self.report_data or []

        if not sessions:
            txt = self.font_large.render("Nessuna sessione trovata", True, self.TEXT_MUTED)
            self.screen.blit(txt, (Layout.GC_CX - txt.get_width() // 2, 200))
            btn = Button(Layout.GC_CX - 120, Layout.H - 80, 240, 60,
                         "Torna al Menu", (100, 100, 140))
            btn.draw(self.screen, self.font_medium)
            self.game_buttons = [btn]
            return

        total_sessions = len(sessions)
        total_score = sum(s.get("total_score", 0) for s in sessions)
        total_duration = sum(s.get("duration_seconds", 0) for s in sessions)
        total_mins = int(total_duration // 60)

        panel1 = pygame.Rect(80, 85, Layout.W - 160, 110)
        self._draw_panel(panel1.x, panel1.y, panel1.w, panel1.h)

        y = 100
        stats = [
            f"Sessioni totali: {total_sessions}",
            f"Punteggio cumulativo: {total_score}",
            f"Tempo totale di gioco: {total_mins} minuti",
        ]
        for line in stats:
            txt = self.font_large.render(line, True, self.TEXT)
            self.screen.blit(txt, (120, y))
            y += 42

        panel2 = pygame.Rect(80, 210, Layout.W - 160, 340)
        self._draw_panel(panel2.x, panel2.y, panel2.w, panel2.h)

        y = 225
        txt = self.font_large.render("Andamento difficolta:", True, self.ACCENT)
        self.screen.blit(txt, (120, y))
        y += 45

        game_names = {
            "respiro_faro": "Respiro", "passi_ricorda": "Passi",
            "semaforo_esecutivo": "Semaforo", "mappa_stanza": "Mappa",
            "costruisci_modello": "Modello", "diario_missioni": "Diario",
            "memory_carte": "Memory", "sequenza_simboli": "Sequenza",
            "parole_incrociate": "Parole", "basket": "Basket",
            "puzzle": "Puzzle", "memory_immagini": "Immagini",
            "brain_trainer": "Trainer", "musical_memory": "Musica",
        }

        game_stats = {}
        for s in sessions:
            for g in s.get("games", []):
                name = g.get("game", "")
                if name not in game_stats:
                    game_stats[name] = {"plays": 0, "total_acc": 0, "count_acc": 0, "best_level": 1}
                game_stats[name]["plays"] += 1
                acc = g.get("result", {}).get("accuracy")
                if isinstance(acc, (int, float)):
                    game_stats[name]["total_acc"] += acc
                    game_stats[name]["count_acc"] += 1
                lvl = g.get("difficulty", 1)
                if lvl > game_stats[name]["best_level"]:
                    game_stats[name]["best_level"] = lvl

        for name, stats in game_stats.items():
            label = game_names.get(name, name)
            plays = stats["plays"]
            avg_acc = (stats["total_acc"] / stats["count_acc"]) if stats["count_acc"] > 0 else 0
            best = stats["best_level"]
            line = f"  {label}: {plays} volte, media {avg_acc:.0%}, livello max {best}"
            txt = self.font_medium.render(line, True, self.TEXT_MUTED)
            self.screen.blit(txt, (120, y))
            y += 38

        panel3 = pygame.Rect(80, 565, Layout.W - 160, 280)
        self._draw_panel(panel3.x, panel3.y, panel3.w, panel3.h)

        y = 580
        txt = self.font_large.render("Ultime sessioni:", True, self.ACCENT)
        self.screen.blit(txt, (120, y))
        y += 48

        for s in sessions[-5:]:
            sid = s.get("session_id", "?")
            sc = s.get("total_score", 0)
            dur = int(s.get("duration_seconds", 0))
            games_count = len(s.get("games", []))
            line = f"  {sid}: {games_count} giochi, {sc} punti, {dur}s"
            txt = self.font_medium.render(line, True, self.TEXT_MUTED)
            self.screen.blit(txt, (120, y))
            y += 38

        btn = Button(Layout.GC_CX - 120, Layout.H - 60, 240, 50,
                     "Torna al Menu", (100, 100, 140))
        btn.draw(self.screen, self.font_medium)
        self.game_buttons = [btn]
