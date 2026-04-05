from dotenv import load_dotenv
load_dotenv()

import subprocess
import logging
import os
import sys
import asyncio

from livekit import agents
from livekit.agents import AgentSession, Agent, RoomInputOptions, function_tool
from livekit.plugins import google, noise_cancellation

from jarvis_prompt import build_behavior_prompt, Reply_prompts
from jarvis_search import search_internet as google_search, get_formatted_datetime as get_current_datetime
from memory_store import load_memory, save_memory, get_recent_conversations, add_memory_entry
from jarvis_get_whether import get_weather
from jarvis_auth import load_session   # ← reads logged-in user's name

from Jarvis_window_CTRL import (
    open_common_app as open,
    open_file,
    run_application_or_media as close,
    list_folder_items as folder_file,
    shutdown_system,
    restart_system,
    sleep_system,
    lock_screen,
    get_battery_info,
    send_whatsapp_message,
    capture_photo
)

from jarvis_file_opner import Play_file
from keyboard_mouse_CTRL import (
    move_cursor_tool,
    mouse_click_tool,
    scroll_cursor_tool,
    type_text_tool,
    press_key_tool,
    swipe_gesture_tool,
    press_hotkey_tool,
    control_volume_tool
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

ENABLE_MEMORY_INTERCEPTOR = True

# ─────────────────────────────────────────────
# Global Activation State
# ─────────────────────────────────────────────
jarvis_active = False  # Sleep mode on launch — say "activate jarvis" to wake up

# Activation keywords — checked BEFORE Gemini generates any response
ACTIVATION_KEYWORDS = [
    "activate jarvis", "jarvis on", "wake up jarvis", "start jarvis",
    "hey jarvis", "jarvis on pannu", "jarvis start pannu", "ready aa jarvis",
    "activate pannu jarvis", "jarvis wake up da", "on pannu", "on panu",
    "jarvis start", "jarvis wake", "activate"
]


def _is_activation_phrase(text: str) -> bool:
    """Check if the transcribed text contains an activation phrase."""
    text_lower = text.lower().strip()
    return any(kw in text_lower for kw in ACTIVATION_KEYWORDS)


@function_tool
async def screenshot_tool() -> str:
    """Takes a screenshot of the current screen and saves it."""
    import pyautogui
    screenshot = pyautogui.screenshot()
    path = os.path.join(os.path.dirname(__file__), "screenshot.png")
    screenshot.save(path)
    return f"Screenshot saved: {path}"


@function_tool
async def activate_jarvis() -> str:
    """
    Activates JARVIS so it starts listening and responding fully.
    Call this when user says anything like:
    'activate jarvis', 'jarvis start', 'on pannு', 'start pannு',
    'jarvis wake up', 'ready aa', 'jarvis on'.
    """
    global jarvis_active
    jarvis_active = True
    return "ACTIVATED"


@function_tool
async def deactivate_jarvis() -> str:
    """
    Deactivates JARVIS - it will stop responding until activated again.
    Call this when user says anything like:
    'deactivate jarvis', 'jarvis stop', 'off pannu', 'sleep pannu',
    'bye jarvis', 'jarvis off', 'rest edu', 'shutdown jarvis'.
    """
    global jarvis_active
    jarvis_active = False
    return "DEACTIVATED"


@function_tool
async def get_jarvis_status() -> str:
    """Returns whether JARVIS is currently active or inactive."""
    return "active" if jarvis_active else "inactive"


class Assistant(Agent):
    def __init__(self, behavior_prompt: str) -> None:
        super().__init__(
            instructions=behavior_prompt,
            tools=[
                google_search,
                get_current_datetime,
                get_weather,
                open,
                open_file,
                close,
                folder_file,
                shutdown_system,
                restart_system,
                sleep_system,
                lock_screen,
                get_battery_info,
                send_whatsapp_message,
                capture_photo,
                load_memory,
                save_memory,
                get_recent_conversations,
                add_memory_entry,
                Play_file,
                screenshot_tool,
                move_cursor_tool,
                mouse_click_tool,
                scroll_cursor_tool,
                type_text_tool,
                press_key_tool,
                press_hotkey_tool,
                control_volume_tool,
                swipe_gesture_tool,
                activate_jarvis,
                deactivate_jarvis,
                get_jarvis_status,
            ]
        )

    async def on_user_turn_completed(self, turn_ctx, new_message) -> None:
        """
        Fires BEFORE Gemini generates any response.

        THE SLEEP MODE GATE:
        When jarvis_active is False, we check the user's transcript.
        - If it's an activation phrase → let it through normally.
        - If it's anything else → truncate the turn so Gemini says NOTHING.
        """
        global jarvis_active

        user_text = ""
        try:
            for part in new_message.content:
                if hasattr(part, "text"):
                    user_text += part.text
        except Exception:
            pass

        logger.info(f"[SLEEP GATE] active={jarvis_active} | heard: '{user_text}'")

        if not jarvis_active:
            if _is_activation_phrase(user_text):
                logger.info("[SLEEP GATE] ✅ Activation phrase — unblocking")
                jarvis_active = True  # ✅ FIX 2: Actually set active so it STAYS active
            else:
                logger.info("[SLEEP GATE] 🔇 Sleep mode — response blocked")
                try:
                    turn_ctx.truncate(index=0)
                except Exception as e:
                    logger.warning(f"[SLEEP GATE] truncate failed: {e}")
                    try:
                        items = turn_ctx.items
                        for item in list(items):
                            items.remove(item)
                    except Exception:
                        pass


async def entrypoint(ctx: agents.JobContext):
    max_retries = 5
    retry_count = 0
    base_wait_time = 3

    # ── Read the logged-in user's name from session ──────────────────
    session = load_session()
    user_name = session.get("name", "").strip()
    if user_name:
        logger.info(f"[JARVIS] Logged-in operator: {user_name}")
    else:
        logger.info("[JARVIS] No operator session found — using generic greeting.")

    # ── Build prompt with user name injected ────────────────────────
    behavior_prompt = await build_behavior_prompt(user_name=user_name)

    # ── Also inject name into Reply_prompts ─────────────────────────
    reply_prompt_with_name = Reply_prompts.replace(
        "{{user_name}}", user_name if user_name else "sir"
    )

    while retry_count < max_retries:
        try:
            print(f"\n Starting agent session (attempt {retry_count + 1}/{max_retries})...")

            session_obj = AgentSession(
                llm=google.beta.realtime.RealtimeModel(
                    voice="Puck",
                    temperature=0.8,
                )
            )

            await ctx.connect()

            await session_obj.start(
                room=ctx.room,
                agent=Assistant(behavior_prompt),
                room_input_options=RoomInputOptions(
                    noise_cancellation=noise_cancellation.BVC(),
                ),
            )

            print("Connected to room, waiting for audio input...")
            print("Waiting for Gemini connection to stabilise...")
            await asyncio.sleep(2)  # ✅ FIX 3: Reduced wait time

            try:
                # ✅ FIX 3: Only generate opening greeting, with short timeout protection
                instructions = reply_prompt_with_name

                if ENABLE_MEMORY_INTERCEPTOR:
                    try:
                        print("Fetching memory context...")
                        memory_context = await get_recent_conversations(limit=5)
                        if memory_context and "No conversations" not in memory_context:
                            instructions = (
                                f"{reply_prompt_with_name}\n\n"
                                f"[RECENT CONTEXT]\n{memory_context}\n[/CONTEXT]"
                            )
                            print("Memory context injected")
                        else:
                            print("No previous conversations to inject")
                    except Exception as e:
                        print(f"Memory injection skipped: {e}")

                print("Sending startup greeting to LLM...")
                try:
                    await asyncio.wait_for(
                        session_obj.generate_reply(instructions=instructions),
                        timeout=10.0  # ✅ FIX 3: Hard timeout so it never hangs
                    )
                except asyncio.TimeoutError:
                    print("⚠ Greeting timed out — but JARVIS mic is still active, continuing...")
                except Exception as e:
                    print(f"⚠ Greeting error (non-fatal): {e} — JARVIS mic still active")

                print(f"✅ Session active — JARVIS is listening (operator: {user_name or 'unknown'}).")

                # Keep session alive indefinitely
                await asyncio.Event().wait()

            except Exception as e:
                error_msg = str(e).lower()
                print(f"Reply error (attempt {retry_count + 1}): {e}")

                if any(k in error_msg for k in ["timed out", "timeout", "generation_created"]):
                    retry_count += 1
                    if retry_count < max_retries:
                        wait_time = base_wait_time * retry_count
                        print(f"Gemini timed out — retrying in {wait_time}s...")
                        await asyncio.sleep(wait_time)
                        continue
                    else:
                        print("Max retries exceeded. Gemini connection unstable.")
                        break
                elif any(k in error_msg for k in ["connection", "websocket", "closed"]):
                    retry_count += 1
                    if retry_count < max_retries:
                        wait_time = base_wait_time * retry_count
                        print(f"Connection error — retrying in {wait_time}s...")
                        await asyncio.sleep(wait_time)
                        continue
                print(f"Unexpected error: {e}")
                break

        except KeyboardInterrupt:
            print("\nAgent stopped by user")
            break
        except Exception as e:
            print(f"Session error: {e}")
            retry_count += 1
            if retry_count < max_retries:
                wait_time = base_wait_time * retry_count
                print(f"Waiting {wait_time}s before retry...")
                await asyncio.sleep(wait_time)
            else:
                print("Max retries exceeded.")
                raise


if __name__ == "__main__":
    # ── FIX: Suppress Windows console keyboard thread crash (LiveKit known bug) ──
    import threading
    _original_excepthook = threading.excepthook

    def _suppress_keyboard_interrupt_in_threads(args):
        if args.exc_type is KeyboardInterrupt:
            return  # silently ignore — keeps JARVIS session alive on Windows
        _original_excepthook(args)

    threading.excepthook = _suppress_keyboard_interrupt_in_threads

    # ── Launch Login UI (which will launch jarvis_ui.py after auth) ──
    try:
        login_path = os.path.join(os.path.dirname(__file__), "jarvis_login_ui.py")
        if os.path.exists(login_path):
            subprocess.Popen(
                [sys.executable, login_path],
                stdout=None, stderr=None, stdin=None, close_fds=True
            )
        else:
            # Fallback: launch jarvis_ui.py directly if login UI not found
            gui_path = os.path.join(os.path.dirname(__file__), "jarvis_ui.py")
            if os.path.exists(gui_path):
                subprocess.Popen(
                    [sys.executable, gui_path],
                    stdout=None, stderr=None, stdin=None, close_fds=True
                )
    except Exception as e:
        print("Failed to start UI subprocess:", e)

    agents.cli.run_app(agents.WorkerOptions(entrypoint_fnc=entrypoint))