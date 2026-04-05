"""
jarvis_login_ui.py — JARVIS Authentication UI
Pygame-based Login / Register / Start screen.
After successful auth → launches jarvis_ui.py (GIF viewer).
"""

import pygame
import sys
import os
import subprocess
import math
import time
import random

from jarvis_auth import is_logged_in, login_user, register_user, logout

# ─────────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────────
WIDTH, HEIGHT = 960, 660
FPS = 60
TITLE = "J.A.R.V.I.S — Access Control"

# ─────────────────────────────────────────────
# JARVIS COLOR PALETTE
# ─────────────────────────────────────────────
BG          = (4,  8, 18)
GRID_LINE   = (10, 25, 55)
PANEL       = (8, 16, 36)
PANEL_EDGE  = (18, 40, 80)
ACCENT      = (0,  190, 255)
ACCENT_DIM  = (0,  100, 170)
ACCENT_GLOW = (0,  210, 255, 60)
TEXT_MAIN   = (210, 230, 255)
TEXT_DIM    = (90,  120, 165)
TEXT_ERR    = (255, 85,  85)
TEXT_OK     = (80,  255, 160)
INPUT_BG    = (10, 20, 44)
INPUT_EDGE  = (28, 55, 100)
INPUT_ACT   = (0,  170, 230)
BTN_PRI     = (0,  110, 195)
BTN_HOV     = (0,  150, 230)
BTN_SEC     = (16, 35, 70)
BTN_SEC_HOV = (22, 50, 100)
WHITE       = (255, 255, 255)
GOLD        = (255, 200, 80)


# ─────────────────────────────────────────────
# FONT LOADER
# ─────────────────────────────────────────────
def get_font(size: int, bold: bool = False) -> pygame.font.Font:
    preferred = ["Consolas", "Courier New", "Liberation Mono", "monospace"]
    match = pygame.font.match_font(preferred)
    if match:
        f = pygame.font.Font(match, size)
        f.set_bold(bold)
        return f
    return pygame.font.SysFont("monospace", size, bold=bold)


# ─────────────────────────────────────────────
# BACKGROUND GRID (drawn once)
# ─────────────────────────────────────────────
def draw_grid(surface: pygame.Surface) -> None:
    """Draw a subtle perspective grid in the background."""
    for x in range(0, WIDTH, 40):
        pygame.draw.line(surface, GRID_LINE, (x, 0), (x, HEIGHT))
    for y in range(0, HEIGHT, 40):
        pygame.draw.line(surface, GRID_LINE, (0, y), (WIDTH, y))


# ─────────────────────────────────────────────
# SCAN LINE EFFECT
# ─────────────────────────────────────────────
class ScanLine:
    def __init__(self):
        self.y = 0
        self.speed = 2

    def update(self):
        self.y = (self.y + self.speed) % HEIGHT

    def draw(self, surface: pygame.Surface) -> None:
        s = pygame.Surface((WIDTH, 3), pygame.SRCALPHA)
        s.fill((0, 200, 255, 18))
        surface.blit(s, (0, self.y))


# ─────────────────────────────────────────────
# PARTICLE FIELD
# ─────────────────────────────────────────────
class Particle:
    def __init__(self):
        self.reset()

    def reset(self):
        self.x = random.uniform(0, WIDTH)
        self.y = random.uniform(0, HEIGHT)
        self.vx = random.uniform(-0.3, 0.3)
        self.vy = random.uniform(-0.6, -0.1)
        self.size = random.uniform(1, 2.5)
        self.alpha = random.randint(40, 140)
        self.life = 1.0

    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.alpha -= 0.5
        if self.alpha <= 0 or self.y < 0:
            self.reset()

    def draw(self, surface: pygame.Surface) -> None:
        s = pygame.Surface((int(self.size * 2) + 1, int(self.size * 2) + 1), pygame.SRCALPHA)
        pygame.draw.circle(s, (*ACCENT[:3], int(self.alpha)), (int(self.size), int(self.size)), int(self.size))
        surface.blit(s, (int(self.x - self.size), int(self.y - self.size)))


# ─────────────────────────────────────────────
# INPUT BOX
# ─────────────────────────────────────────────
class InputBox:
    def __init__(self, x: int, y: int, w: int, h: int,
                 placeholder: str = "", password: bool = False):
        self.rect = pygame.Rect(x, y, w, h)
        self.placeholder = placeholder
        self.password = password
        self.text = ""
        self.active = False
        self._cursor_vis = True
        self._cursor_timer = 0.0

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.MOUSEBUTTONDOWN:
            self.active = self.rect.collidepoint(event.pos)
        if event.type == pygame.KEYDOWN and self.active:
            if event.key == pygame.K_BACKSPACE:
                self.text = self.text[:-1]
            elif event.key not in (pygame.K_RETURN, pygame.K_TAB, pygame.K_ESCAPE):
                if len(self.text) < 60 and event.unicode.isprintable():
                    self.text += event.unicode

    def update(self, dt: float) -> None:
        self._cursor_timer += dt
        if self._cursor_timer >= 530:
            self._cursor_vis = not self._cursor_vis
            self._cursor_timer = 0.0

    def draw(self, surface: pygame.Surface, font: pygame.font.Font) -> None:
        # Glow border when active
        if self.active:
            glow_rect = self.rect.inflate(6, 6)
            gs = pygame.Surface(glow_rect.size, pygame.SRCALPHA)
            pygame.draw.rect(gs, (0, 170, 230, 35), gs.get_rect(), border_radius=12)
            surface.blit(gs, glow_rect.topleft)

        # Box
        pygame.draw.rect(surface, INPUT_BG,  self.rect, border_radius=8)
        border_col = INPUT_ACT if self.active else INPUT_EDGE
        pygame.draw.rect(surface, border_col, self.rect, 2, border_radius=8)

        # Text / placeholder
        display = ("●" * len(self.text)) if self.password else self.text
        if display:
            ts = font.render(display, True, TEXT_MAIN)
            tr = ts.get_rect(midleft=(self.rect.x + 16, self.rect.centery))
            # Clip if too wide
            clip = pygame.Rect(self.rect.x + 8, self.rect.y + 4,
                               self.rect.w - 16, self.rect.h - 8)
            surface.set_clip(clip)
            surface.blit(ts, tr)
            surface.set_clip(None)
            # Cursor
            if self.active and self._cursor_vis:
                cx = min(tr.right + 2, self.rect.right - 10)
                pygame.draw.line(surface, ACCENT,
                                 (cx, self.rect.y + 10),
                                 (cx, self.rect.bottom - 10), 2)
        else:
            ph = font.render(self.placeholder, True, TEXT_DIM)
            surface.blit(ph, ph.get_rect(midleft=(self.rect.x + 16, self.rect.centery)))

    def clear(self) -> None:
        self.text = ""
        self.active = False


# ─────────────────────────────────────────────
# BUTTON
# ─────────────────────────────────────────────
class Button:
    def __init__(self, x: int, y: int, w: int, h: int,
                 label: str, primary: bool = True):
        self.rect = pygame.Rect(x, y, w, h)
        self.label = label
        self.primary = primary
        self.hovered = False

    def handle_event(self, event: pygame.event.Event) -> bool:
        if event.type == pygame.MOUSEMOTION:
            self.hovered = self.rect.collidepoint(event.pos)
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                return True
        return False

    def draw(self, surface: pygame.Surface, font: pygame.font.Font) -> None:
        if self.primary:
            base = BTN_HOV if self.hovered else BTN_PRI
            pygame.draw.rect(surface, base, self.rect, border_radius=10)
            if self.hovered:
                gs = pygame.Surface(self.rect.inflate(8, 8).size, pygame.SRCALPHA)
                pygame.draw.rect(gs, (0, 180, 255, 55), gs.get_rect(), border_radius=14)
                surface.blit(gs, self.rect.inflate(8, 8).topleft)
        else:
            base = BTN_SEC_HOV if self.hovered else BTN_SEC
            pygame.draw.rect(surface, base, self.rect, border_radius=10)
            edge = ACCENT if self.hovered else PANEL_EDGE
            pygame.draw.rect(surface, edge, self.rect, 2, border_radius=10)

        ts = font.render(self.label, True, WHITE)
        surface.blit(ts, ts.get_rect(center=self.rect.center))


# ─────────────────────────────────────────────
# TEXT LINK (clickable)
# ─────────────────────────────────────────────
class TextLink:
    def __init__(self, x: int, y: int, label: str):
        self.label = label
        self.x = x
        self.y = y
        self.rect = None
        self.hovered = False

    def handle_event(self, event: pygame.event.Event) -> bool:
        if self.rect:
            if event.type == pygame.MOUSEMOTION:
                self.hovered = self.rect.collidepoint(event.pos)
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if self.rect.collidepoint(event.pos):
                    return True
        return False

    def draw(self, surface: pygame.Surface, font: pygame.font.Font) -> None:
        col = ACCENT if self.hovered else ACCENT_DIM
        ts = font.render(self.label, True, col)
        self.rect = ts.get_rect(center=(self.x, self.y))
        surface.blit(ts, self.rect)
        if self.hovered:
            pygame.draw.line(surface, col,
                             (self.rect.left, self.rect.bottom + 1),
                             (self.rect.right, self.rect.bottom + 1), 1)


# ─────────────────────────────────────────────
# HELPER: Draw glowing text
# ─────────────────────────────────────────────
def draw_glow_text(surface, text, font, cx, cy, color, glow_col, alpha=255):
    # Glow layer
    gts = font.render(text, True, glow_col)
    for dx, dy in [(-2, 0), (2, 0), (0, -2), (0, 2), (-1, -1), (1, 1)]:
        gs = pygame.Surface(gts.get_size(), pygame.SRCALPHA)
        gs.blit(gts, (0, 0))
        gs.set_alpha(int(alpha * 0.35))
        r = gs.get_rect(center=(cx + dx, cy + dy))
        surface.blit(gs, r)
    # Main text
    ts = font.render(text, True, color)
    ts.set_alpha(alpha)
    surface.blit(ts, ts.get_rect(center=(cx, cy)))


# ─────────────────────────────────────────────
# DRAW PANEL CARD
# ─────────────────────────────────────────────
def draw_panel(surface, x, y, w, h):
    s = pygame.Surface((w, h), pygame.SRCALPHA)
    pygame.draw.rect(s, (*PANEL, 230), s.get_rect(), border_radius=16)
    surface.blit(s, (x, y))
    pygame.draw.rect(surface, PANEL_EDGE, pygame.Rect(x, y, w, h), 2, border_radius=16)
    # Top accent line
    pygame.draw.line(surface, ACCENT,
                     (x + 30, y + 2), (x + w - 30, y + 2), 2)


# ─────────────────────────────────────────────
# MAIN APP
# ─────────────────────────────────────────────
def launch_jarvis_ui():
    """Launch the JARVIS GIF UI as a subprocess."""
    ui_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "jarvis_ui.py")
    if os.path.exists(ui_path):
        subprocess.Popen(
            [sys.executable, ui_path],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            stdin=subprocess.DEVNULL,
            close_fds=True
        )
    else:
        print(f"[JARVIS] jarvis_ui.py not found at {ui_path}")


def main():
    pygame.init()
    pygame.display.set_caption(TITLE)
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    clock = pygame.time.Clock()

    # ── Fonts ──────────────────────────────────
    font_logo   = get_font(46, bold=True)
    font_tag    = get_font(13)
    font_label  = get_font(13)
    font_input  = get_font(15)
    font_btn    = get_font(15, bold=True)
    font_msg    = get_font(13)
    font_name   = get_font(52, bold=True)
    font_welcome= get_font(18)
    font_start  = get_font(20, bold=True)
    font_link   = get_font(13)
    font_head   = get_font(22, bold=True)

    # ── Background elements ────────────────────
    bg_surf = pygame.Surface((WIDTH, HEIGHT))
    bg_surf.fill(BG)
    draw_grid(bg_surf)

    scanline = ScanLine()
    particles = [Particle() for _ in range(55)]

    # ── Determine initial screen ───────────────
    logged_in, current_name = is_logged_in()
    # States: "start" | "login" | "register"
    state = "start" if logged_in else "login"

    # ── Shared message state ───────────────────
    msg_text  = ""
    msg_color = TEXT_ERR
    msg_timer = 0.0

    def set_msg(text, ok=False):
        nonlocal msg_text, msg_color, msg_timer
        msg_text  = text
        msg_color = TEXT_OK if ok else TEXT_ERR
        msg_timer = 3500.0  # ms

    # ── PANEL geometry ─────────────────────────
    PW, PH_LOGIN = 480, 430
    PW, PH_REG   = 480, 510
    PW, PH_START = 480, 340
    PX = (WIDTH  - PW) // 2
    PY_LOGIN = (HEIGHT - PH_LOGIN) // 2
    PY_REG   = (HEIGHT - PH_REG)   // 2
    PY_START = (HEIGHT - PH_START) // 2

    # ─────────────────────────────────────────
    # LOGIN SCREEN WIDGETS
    # ─────────────────────────────────────────
    def build_login(py):
        ib_email = InputBox(PX + 40, py + 130, PW - 80, 46, "Email Address")
        ib_pass  = InputBox(PX + 40, py + 200, PW - 80, 46, "Password", password=True)
        btn_login = Button(PX + 40, py + 272, PW - 80, 48, "LOGIN", primary=True)
        lnk_reg   = TextLink(WIDTH // 2, py + PH_LOGIN - 32, "Don't have an account?  Register here")
        return ib_email, ib_pass, btn_login, lnk_reg

    py_l = PY_LOGIN
    l_email, l_pass, btn_login, lnk_to_reg = build_login(py_l)

    # ─────────────────────────────────────────
    # REGISTER SCREEN WIDGETS
    # ─────────────────────────────────────────
    def build_register(py):
        ib_name  = InputBox(PX + 40, py + 110, PW - 80, 46, "Your Name")
        ib_email = InputBox(PX + 40, py + 176, PW - 80, 46, "Email Address")
        ib_pass  = InputBox(PX + 40, py + 242, PW - 80, 46, "Password", password=True)
        ib_conf  = InputBox(PX + 40, py + 308, PW - 80, 46, "Confirm Password", password=True)
        btn_reg  = Button(PX + 40, py + 375, PW - 80, 48, "CREATE ACCOUNT", primary=True)
        lnk_log  = TextLink(WIDTH // 2, py + PH_REG - 28, "Already registered?  Login here")
        return ib_name, ib_email, ib_pass, ib_conf, btn_reg, lnk_log

    py_r = PY_REG
    r_name, r_email, r_pass, r_conf, btn_reg, lnk_to_log = build_register(py_r)
    all_reg_inputs = [r_name, r_email, r_pass, r_conf]

    # ─────────────────────────────────────────
    # START SCREEN WIDGETS
    # ─────────────────────────────────────────
    def build_start(py):
        btn_s   = Button(PX + 60, py + 218, PW - 120, 60, "▶  START JARVIS", primary=True)
        lnk_out = TextLink(WIDTH // 2, py + PH_START - 28, "Not you?  Logout")
        return btn_s, lnk_out

    btn_start, lnk_logout = build_start(PY_START)

    # ── Pulse animation for logo ───────────────
    t_val = 0.0

    running = True
    while running:
        dt = clock.tick(FPS)
        t_val += dt * 0.001   # seconds-based timer

        # ── Message timer ──────────────────────
        if msg_timer > 0:
            msg_timer -= dt

        # ── Events ─────────────────────────────
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                running = False

            # ── STATE: start ──────────────────
            if state == "start":
                if btn_start.handle_event(event):
                    launch_jarvis_ui()
                    pygame.quit()
                    sys.exit()
                if lnk_logout.handle_event(event):
                    logout()
                    logged_in, current_name = False, ""
                    state = "login"
                    l_email.clear(); l_pass.clear()
                    set_msg("")

            # ── STATE: login ──────────────────
            elif state == "login":
                l_email.handle_event(event)
                l_pass.handle_event(event)

                if event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN:
                    ok, msg, name = login_user(l_email.text, l_pass.text)
                    if ok:
                        current_name = name
                        btn_start, lnk_logout = build_start(PY_START)
                        state = "start"
                        set_msg(f"Welcome back, {name}!", ok=True)
                    else:
                        set_msg(msg)

                if btn_login.handle_event(event):
                    ok, msg, name = login_user(l_email.text, l_pass.text)
                    if ok:
                        current_name = name
                        btn_start, lnk_logout = build_start(PY_START)
                        state = "start"
                        set_msg(f"Welcome back, {name}!", ok=True)
                    else:
                        set_msg(msg)

                if lnk_to_reg.handle_event(event):
                    state = "register"
                    for ib in all_reg_inputs:
                        ib.clear()
                    set_msg("")

            # ── STATE: register ───────────────
            elif state == "register":
                for ib in all_reg_inputs:
                    ib.handle_event(event)

                if event.type == pygame.KEYDOWN and event.key == pygame.K_TAB:
                    # Cycle focus
                    focused = next((i for i, ib in enumerate(all_reg_inputs) if ib.active), -1)
                    for ib in all_reg_inputs:
                        ib.active = False
                    if focused >= 0:
                        all_reg_inputs[(focused + 1) % len(all_reg_inputs)].active = True

                if btn_reg.handle_event(event) or (
                    event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN
                ):
                    n, e, p, c = r_name.text, r_email.text, r_pass.text, r_conf.text
                    if p != c:
                        set_msg("Passwords do not match.")
                    else:
                        ok, msg = register_user(n, e, p)
                        if ok:
                            set_msg("Account created! Please login.", ok=True)
                            state = "login"
                            l_email.clear(); l_pass.clear()
                        else:
                            set_msg(msg)

                if lnk_to_log.handle_event(event):
                    state = "login"
                    l_email.clear(); l_pass.clear()
                    set_msg("")

        # ── Update ─────────────────────────────
        scanline.update()
        for p in particles:
            p.update()

        if state == "login":
            l_email.update(dt); l_pass.update(dt)
        elif state == "register":
            for ib in all_reg_inputs:
                ib.update(dt)

        # ── Draw background ────────────────────
        screen.blit(bg_surf, (0, 0))
        for p in particles:
            p.draw(screen)
        scanline.draw(screen)

        # ── Corner accents ─────────────────────
        def corner_accent(cx, cy, flip_x=False, flip_y=False):
            sz = 28
            sign_x = -1 if flip_x else 1
            sign_y = -1 if flip_y else 1
            pygame.draw.line(screen, ACCENT, (cx, cy), (cx + sign_x * sz, cy), 2)
            pygame.draw.line(screen, ACCENT, (cx, cy), (cx, cy + sign_y * sz), 2)

        corner_accent(20, 20)
        corner_accent(WIDTH - 20, 20, flip_x=True)
        corner_accent(20, HEIGHT - 20, flip_y=True)
        corner_accent(WIDTH - 20, HEIGHT - 20, flip_x=True, flip_y=True)

        # ── Top status bar ─────────────────────
        pygame.draw.line(screen, PANEL_EDGE, (0, 36), (WIDTH, 36), 1)
        status_lbl = font_label.render("JARVIS  //  IDENTITY VERIFICATION SYSTEM", True, TEXT_DIM)
        screen.blit(status_lbl, (WIDTH // 2 - status_lbl.get_width() // 2, 12))
        # Pulsing dot
        pulse = int(180 + 75 * math.sin(t_val * 3))
        pygame.draw.circle(screen, (0, pulse, 255), (30, 18), 5)

        # ─────────────────────────────────────
        # DRAW STATE: start
        # ─────────────────────────────────────
        if state == "start":
            py = PY_START
            draw_panel(screen, PX, py, PW, PH_START)

            # Logo
            draw_glow_text(screen, "J.A.R.V.I.S",
                           font_logo, WIDTH // 2, py + 48,
                           WHITE, ACCENT)

            # Welcome line
            tag = font_welcome.render("WELCOME BACK, OPERATOR", True, TEXT_DIM)
            screen.blit(tag, tag.get_rect(center=(WIDTH // 2, py + 92)))

            # User name (big, glowing, pulsing)
            name_scale = 1.0 + 0.015 * math.sin(t_val * 2)
            name_surf = font_name.render(current_name.upper(), True, ACCENT)
            nw = int(name_surf.get_width() * name_scale)
            nh = int(name_surf.get_height() * name_scale)
            scaled = pygame.transform.smoothscale(name_surf, (nw, nh))
            screen.blit(scaled, scaled.get_rect(center=(WIDTH // 2, py + 162)))

            # Thin separator
            pygame.draw.line(screen, PANEL_EDGE,
                             (PX + 40, py + 200), (PX + PW - 40, py + 200), 1)

            btn_start.draw(screen, font_start)
            lnk_logout.draw(screen, font_link)

        # ─────────────────────────────────────
        # DRAW STATE: login
        # ─────────────────────────────────────
        elif state == "login":
            py = py_l
            draw_panel(screen, PX, py, PW, PH_LOGIN)

            draw_glow_text(screen, "J.A.R.V.I.S",
                           font_logo, WIDTH // 2, py + 46, WHITE, ACCENT)
            tag = font_tag.render("OPERATOR LOGIN  —  AUTHORISED ACCESS ONLY", True, TEXT_DIM)
            screen.blit(tag, tag.get_rect(center=(WIDTH // 2, py + 84)))

            pygame.draw.line(screen, PANEL_EDGE,
                             (PX + 30, py + 100), (PX + PW - 30, py + 100), 1)

            # Field labels
            def field_lbl(label, fx, fy):
                ls = font_label.render(label, True, ACCENT_DIM)
                screen.blit(ls, (fx, fy - 18))

            field_lbl("EMAIL", PX + 40, py + 130)
            field_lbl("PASSWORD", PX + 40, py + 200)

            l_email.draw(screen, font_input)
            l_pass.draw(screen, font_input)
            btn_login.draw(screen, font_btn)
            lnk_to_reg.draw(screen, font_link)

        # ─────────────────────────────────────
        # DRAW STATE: register
        # ─────────────────────────────────────
        elif state == "register":
            py = py_r
            draw_panel(screen, PX, py, PW, PH_REG)

            draw_glow_text(screen, "J.A.R.V.I.S",
                           font_logo, WIDTH // 2, py + 40, WHITE, ACCENT)
            tag = font_tag.render("NEW OPERATOR REGISTRATION", True, TEXT_DIM)
            screen.blit(tag, tag.get_rect(center=(WIDTH // 2, py + 76)))

            pygame.draw.line(screen, PANEL_EDGE,
                             (PX + 30, py + 94), (PX + PW - 30, py + 94), 1)

            def field_lbl(label, fx, fy):
                ls = font_label.render(label, True, ACCENT_DIM)
                screen.blit(ls, (fx, fy - 17))

            field_lbl("FULL NAME",         PX + 40, py + 110)
            field_lbl("EMAIL ADDRESS",     PX + 40, py + 176)
            field_lbl("PASSWORD",          PX + 40, py + 242)
            field_lbl("CONFIRM PASSWORD",  PX + 40, py + 308)

            for ib in all_reg_inputs:
                ib.draw(screen, font_input)
            btn_reg.draw(screen, font_btn)
            lnk_to_log.draw(screen, font_link)

        # ── Message bar ────────────────────────
        if msg_text and msg_timer > 0:
            fade = min(1.0, msg_timer / 400.0)
            ms = font_msg.render(msg_text, True, msg_color)
            ms.set_alpha(int(255 * fade))
            screen.blit(ms, ms.get_rect(center=(WIDTH // 2, HEIGHT - 22)))

        pygame.display.flip()

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
