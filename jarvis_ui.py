import pygame
import sys
import os

# ── GIF frame loader using Pillow ────────────────────────
try:
    from PIL import Image
except ImportError:
    print("Pillow தேவை! Install பண்ணு:  pip install Pillow")
    sys.exit(1)


def load_gif_frames(path):
    """Load all frames from a GIF and return list of pygame Surfaces."""
    gif = Image.open(path)
    frames = []
    durations = []
    try:
        while True:
            frame = gif.convert("RGBA")
            data = frame.tobytes()
            w, h = frame.size
            surf = pygame.image.fromstring(data, (w, h), "RGBA")
            frames.append(surf)
            durations.append(gif.info.get("duration", 50))
            gif.seek(gif.tell() + 1)
    except EOFError:
        pass
    return frames, durations


def main():
    pygame.init()
    pygame.display.set_caption("J.A.R.V.I.S  —  Mark 42")

    # ── GIF path — same folder as this script ────────────
    gif_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Untitled_design.gif")
    if not os.path.exists(gif_path):
        print(f"GIF கிடைக்கலை: {gif_path}")
        pygame.quit()
        sys.exit(1)

    frames, durations = load_gif_frames(gif_path)
    if not frames:
        print("GIF-ல frames இல்ல!")
        pygame.quit()
        sys.exit(1)

    # ── Window = GIF native size (full GIF visible, no black bars) ──
    gif_native_w, gif_native_h = frames[0].get_size()   # 1152 x 648
    screen = pygame.display.set_mode((gif_native_w, gif_native_h), pygame.RESIZABLE)
    clock  = pygame.time.Clock()

    frame_index   = 0
    frame_elapsed = 0
    is_fullscreen = False

    running = True
    while running:
        dt = clock.tick(60)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    if is_fullscreen:
                        screen = pygame.display.set_mode(
                            (gif_native_w, gif_native_h), pygame.RESIZABLE)
                        is_fullscreen = False
                    else:
                        running = False

                elif event.key == pygame.K_RETURN:
                    if is_fullscreen:
                        screen = pygame.display.set_mode(
                            (gif_native_w, gif_native_h), pygame.RESIZABLE)
                        is_fullscreen = False
                    else:
                        screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
                        is_fullscreen = True

        # ── Advance GIF frame ──────────────────────────────
        frame_elapsed += dt
        while frame_elapsed >= durations[frame_index]:
            frame_elapsed -= durations[frame_index]
            frame_index = (frame_index + 1) % len(frames)

        # ── Draw ───────────────────────────────────────────
        W, H = screen.get_size()
        screen.fill((0, 0, 0))

        gif_frame = frames[frame_index]
        fw, fh    = gif_frame.get_size()

        if is_fullscreen:
            # Fullscreen: cover — sides always visible, slight top/bottom crop ok
            scale = max(W / fw, H / fh)
        else:
            # Normal window: fit — full GIF visible, no crop, no black bars
            scale = min(W / fw, H / fh)

        new_w  = int(fw * scale)
        new_h  = int(fh * scale)
        scaled = pygame.transform.smoothscale(gif_frame, (new_w, new_h))

        x = (W - new_w) // 2
        y = (H - new_h) // 2
        screen.blit(scaled, (x, y))

        pygame.display.flip()

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()