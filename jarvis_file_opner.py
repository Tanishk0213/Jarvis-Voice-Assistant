import os
import subprocess
import sys
import logging
from fuzzywuzzy import process
import asyncio

try:
    import pygetwindow as gw
except ImportError:
    gw = None

from livekit.agents import function_tool

sys.stdout.reconfigure(encoding='utf-8')

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def focus_window(title_keyword: str) -> bool:
    """Try to bring the opened window to focus."""
    if not gw:
        logger.warning("⚠ pygetwindow not available")
        return False

    await asyncio.sleep(1.5)
    title_keyword = title_keyword.lower().strip()

    for window in gw.getAllWindows():
        if title_keyword in window.title.lower():
            if window.isMinimized:
                window.restore()
            window.activate()
            logger.info(f"🪟 Window focus aaiduchu: {window.title}")
            return True

    logger.warning("⚠ Window kandupidikka mudiyala.")
    return False


async def index_files(base_dirs):
    """Index all files from given directories."""
    file_index = []
    for base_dir in base_dirs:
        for root, _, files in os.walk(base_dir):
            for f in files:
                file_index.append({
                    "name": f,
                    "path": os.path.join(root, f),
                    "type": "file"
                })
    logger.info(f"✅ {base_dirs} - la irundhu {len(file_index)} files index aaiduchu.")
    return file_index


async def search_file(query, index):
    """Fuzzy search for a file by name."""
    choices = [item["name"] for item in index]
    if not choices:
        logger.warning("⚠ Match pannuva file illai.")
        return None

    best_match, score = process.extractOne(query, choices)
    logger.info(f"🔍 '{query}' → '{best_match}' match aaiduchu (Score: {score})")

    if score > 70:
        for item in index:
            if item["name"] == best_match:
                return item
    return None


async def open_file(item):
    """Open the file using the OS default application."""
    try:
        logger.info(f"📂 File open pannuren: {item['path']}")
        if os.name == 'nt':
            os.startfile(item["path"])
        else:
            subprocess.call(['open' if sys.platform == 'darwin' else 'xdg-open', item["path"]])
        await focus_window(item["name"])
        return f"✅ File open aaiduchu: {item['name']}"
    except Exception as e:
        logger.error(f"❌ File open pannuvadhil error: {e}")
        return f"❌ File open aagala. Error: {e}"


async def handle_command(command, index):
    """Search and open file based on command."""
    item = await search_file(command, index)
    if item:
        return await open_file(item)
    else:
        logger.warning("❌ File kandupidikka mudiyala.")
        return "❌ File kandupidikka mudiyala sir, vera name try pannunga."


@function_tool
async def Play_file(name: str) -> str:
    """
    Searches for and opens a file by name from the D:/ drive.

    Use this tool when the user wants to open a file like a video, PDF, document, image, etc.
    Example prompts:
    - "Open my resume from D drive"
    - "D drive la project report open pannu"
    - "MP4 file play pannu"
    """
    folders_to_index = ["D:/"]
    index = await index_files(folders_to_index)
    command = name.strip()
    return await handle_command(command, index)