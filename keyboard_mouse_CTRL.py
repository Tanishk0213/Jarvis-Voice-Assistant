import pyautogui
import asyncio
import time
from datetime import datetime
from pynput.keyboard import Key, Controller as KeyboardController
from pynput.mouse import Button, Controller as MouseController
from typing import List
from livekit.agents import function_tool
import codecs

# ---------------------
# SafeController Class
# ---------------------
class SafeController:
    def __init__(self):
        self.active = False
        self.activation_time = None
        self.keyboard = KeyboardController()
        self.mouse = MouseController()
        self.valid_keys = set("abcdefghijklmnopqrstuvwxyz1234567890")
        self.special_keys = {
            "enter": Key.enter, "space": Key.space, "tab": Key.tab,
            "shift": Key.shift, "ctrl": Key.ctrl, "alt": Key.alt,
            "esc": Key.esc, "backspace": Key.backspace, "delete": Key.delete,
            "up": Key.up, "down": Key.down, "left": Key.left, "right": Key.right,
            "caps_lock": Key.caps_lock, "cmd": Key.cmd, "win": Key.cmd,
            "home": Key.home, "end": Key.end,
            "page_up": Key.page_up, "page_down": Key.page_down
        }

    def resolve_key(self, key):
        return self.special_keys.get(key.lower(), key)

    def log(self, action: str):
        with open("control_log.txt", "a") as f:
            f.write(f"{datetime.now()}: {action}\n")

    def activate(self, token=None):
        if token != "my_secret_token":
            self.log("Activation attempt failed.")
            return
        self.active = True
        self.activation_time = time.time()
        self.log("Controller auto-activated.")

    def deactivate(self):
        self.active = False
        self.log("Controller auto-deactivated.")

    def is_active(self):
        return self.active

    async def move_cursor(self, direction: str, distance: int = 100):
        if not self.is_active():
            return "Controller is inactive."
        x, y = self.mouse.position
        if direction == "left":
            self.mouse.position = (x - distance, y)
        elif direction == "right":
            self.mouse.position = (x + distance, y)
        elif direction == "up":
            self.mouse.position = (x, y - distance)
        elif direction == "down":
            self.mouse.position = (x, y + distance)
        await asyncio.sleep(0.2)
        self.log(f"Mouse moved {direction}")
        return f"Mouse moved {direction}."

    async def mouse_click(self, button: str = "left"):
        if not self.is_active():
            return "Controller is inactive."
        if button == "left":
            self.mouse.click(Button.left, 1)
        elif button == "right":
            self.mouse.click(Button.right, 1)
        elif button == "double":
            self.mouse.click(Button.left, 2)
        await asyncio.sleep(0.2)
        self.log(f"Mouse clicked: {button}")
        return f"{button.capitalize()} click done."

    async def scroll_cursor(self, direction: str, amount: int = 10):
        if not self.is_active():
            return "Controller is inactive."
        try:
            if direction == "up":
                self.mouse.scroll(0, amount)
            elif direction == "down":
                self.mouse.scroll(0, -amount)
        except Exception:
            pyautogui.scroll(amount * 100)
        await asyncio.sleep(0.2)
        self.log(f"Mouse scrolled {direction}")
        return f"Scrolled {direction}."

    async def type_text(self, text: str):
        if not self.is_active():
            return "Controller is inactive."

        text = codecs.decode(text, "unicode_escape")

        for char in text:
            try:
                if char == "\n":
                    self.keyboard.press(Key.enter)
                    self.keyboard.release(Key.enter)
                elif char == "\t":
                    self.keyboard.press(Key.tab)
                    self.keyboard.release(Key.tab)
                elif char.isprintable():
                    self.keyboard.press(char)
                    self.keyboard.release(char)
                else:
                    continue
                await asyncio.sleep(0.05)
            except Exception:
                continue

        self.log(f"Typed text: {text}")
        return f"Typed: {text}"

    async def press_key(self, key: str):
        if not self.is_active():
            return "Controller is inactive."
        if key.lower() not in self.special_keys and key.lower() not in self.valid_keys:
            return f"Invalid key: {key}"
        k = self.resolve_key(key)
        try:
            self.keyboard.press(k)
            self.keyboard.release(k)
        except Exception as e:
            return f"Failed to press key: {key} — {e}"
        await asyncio.sleep(0.2)
        self.log(f"Pressed key: {key}")
        return f"Key '{key}' pressed."

    async def press_hotkey(self, keys: List[str]):
        if not self.is_active():
            return "Controller is inactive."
        resolved = []
        for k in keys:
            if k.lower() not in self.special_keys and k.lower() not in self.valid_keys:
                return f"Invalid key in hotkey: {k}"
            resolved.append(self.resolve_key(k))

        for k in resolved:
            self.keyboard.press(k)
        for k in reversed(resolved):
            self.keyboard.release(k)
        await asyncio.sleep(0.3)
        self.log(f"Pressed hotkey: {' + '.join(keys)}")
        return f"Hotkey {' + '.join(keys)} pressed."

    async def control_volume(self, action: str):
        if not self.is_active():
            return "Controller is inactive."
        if action == "up":
            pyautogui.press("volumeup")
        elif action == "down":
            pyautogui.press("volumedown")
        elif action == "mute":
            pyautogui.press("volumemute")
        await asyncio.sleep(0.2)
        self.log(f"Volume control: {action}")
        return f"Volume {action} done."

    async def swipe_gesture(self, direction: str):
        if not self.is_active():
            return "Controller is inactive."
        screen_width, screen_height = pyautogui.size()
        x, y = screen_width // 2, screen_height // 2
        try:
            if direction == "up":
                pyautogui.moveTo(x, y + 200)
                pyautogui.dragTo(x, y - 200, duration=0.5)
            elif direction == "down":
                pyautogui.moveTo(x, y - 200)
                pyautogui.dragTo(x, y + 200, duration=0.5)
            elif direction == "left":
                pyautogui.moveTo(x + 200, y)
                pyautogui.dragTo(x - 200, y, duration=0.5)
            elif direction == "right":
                pyautogui.moveTo(x - 200, y)
                pyautogui.dragTo(x + 200, y, duration=0.5)
        except Exception:
            pass
        await asyncio.sleep(0.5)
        self.log(f"Swipe gesture: {direction}")
        return f"Swipe {direction} done."


controller = SafeController()


async def with_temporary_activation(fn, *args, **kwargs):
    controller.activate("my_secret_token")
    result = await fn(*args, **kwargs)
    await asyncio.sleep(2)
    controller.deactivate()
    return result


@function_tool
async def move_cursor_tool(direction: str, distance: int = 100):
    """
    Moves the mouse cursor in the given direction by the given number of pixels.

    Use this when user says things like:
    - "move mouse left" / "cursor right pannu" / "mouse up podu"
    - "mouse keezhey podu" / "cursor move pannu"

    Args:
        direction (str): One of ["up", "down", "left", "right"].
        distance (int): Pixels to move. Default is 100.

    Returns:
        str: Confirmation message of the mouse movement.
    """
    return await with_temporary_activation(controller.move_cursor, direction, distance)


@function_tool
async def mouse_click_tool(button: str = "left"):
    """
    Performs a mouse click — left click, right click, or double click.

    Use this when user says things like:
    - "click pannu" / "left click podu" / "double click" / "right click pannu"
    - "inga click pannu" / "mouse click podu"

    Args:
        button (str): One of ["left", "right", "double"]. Default is "left".

    Returns:
        str: Confirmation of the click performed.
    """
    return await with_temporary_activation(controller.mouse_click, button)


@function_tool
async def scroll_cursor_tool(direction: str, amount: int = 10):
    """
    Scrolls the screen up or down.

    Use this when user says things like:
    - "scroll down pannu" / "scroll up" / "page keezhey podu"
    - "keezhey scroll pannu" / "melay scroll podu" / "scroll cheyyи"

    Args:
        direction (str): Either "up" or "down".
        amount (int): How much to scroll. Default is 10.

    Returns:
        str: Confirmation of the scroll action.
    """
    return await with_temporary_activation(controller.scroll_cursor, direction, amount)


@function_tool
async def type_text_tool(text: str):
    """
    Types the given text on the keyboard, one character at a time.

    Use this when user says things like:
    - "type hello world" / "itha type pannu" / "write this text"
    - "keyboard la type pannu" / "itha ezhuthu"

    Args:
        text (str): The full text to type, including spaces and punctuation.

    Returns:
        str: Confirmation of what was typed.
    """
    return await with_temporary_activation(controller.type_text, text)


@function_tool
async def press_key_tool(key: str):
    """
    Presses a single keyboard key like Enter, Escape, Space, or any letter or number.

    Use this when user says things like:
    - "press enter" / "enter key podu" / "escape press pannu"
    - "enter podu" / "backspace pannu" / "space key press pannu"

    Args:
        key (str): Key name — e.g. "enter", "esc", "a", "ctrl", "space", "backspace".

    Returns:
        str: Confirmation of the key press, or error if the key is invalid.
    """
    return await with_temporary_activation(controller.press_key, key)


@function_tool
async def press_hotkey_tool(keys: List[str]):
    """
    Presses a keyboard shortcut combination like Ctrl+S, Alt+F4, Ctrl+Z etc.

    Use this when user says things like:
    - "save pannu" / "Ctrl+S podu" / "file save pannidu"
    - "window close pannu" / "Alt+F4 press pannu"
    - "copy pannu" / "paste pannu" / "undo pannu" / "redo pannu"

    Args:
        keys (List[str]): List of key names to press together.
            Example: ["ctrl", "s"] for save, ["alt", "f4"] for close window.

    Returns:
        str: Confirmation of which hotkey combination was pressed.
    """
    return await with_temporary_activation(controller.press_hotkey, keys)


@function_tool
async def control_volume_tool(action: str):
    """
    Controls the system volume — increase, decrease, or mute.

    Use this when user says things like:
    - "volume up pannu" / "sound yetra" / "increase volume"
    - "volume kurachu" / "sound kammiya pannu" / "lower the volume"
    - "mute pannu" / "sound off pannu" / "mute the audio"

    Args:
        action (str): One of ["up", "down", "mute"].

    Returns:
        str: Confirmation of the volume change.
    """
    return await with_temporary_activation(controller.control_volume, action)


@function_tool
async def swipe_gesture_tool(direction: str):
    """
    Simulates a swipe gesture on the screen using mouse drag.

    Use this when user says things like:
    - "swipe left pannu" / "left swipe podu" / "swipe right"
    - "screen keezhey swipe pannu" / "melay swipe podu"

    Args:
        direction (str): One of ["up", "down", "left", "right"].

    Returns:
        str: Confirmation of the swipe gesture performed.
    """
    return await with_temporary_activation(controller.swipe_gesture, direction)