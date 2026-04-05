import json
import os
from datetime import datetime
from typing import List, Dict, Union
import logging
from livekit.agents import function_tool

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ConversationMemory:
    """Handles persistent conversation memory for users"""

    def __init__(self, user_id: str, storage_path: str = "conversations"):
        self.user_id = user_id
        self.storage_path = storage_path
        self.memory_file = os.path.join(storage_path, f"{user_id}_memory.json")
        os.makedirs(storage_path, exist_ok=True)

    def load_memory(self) -> List[Dict]:
        if os.path.exists(self.memory_file):
            try:
                with open(self.memory_file, 'r', encoding="utf-8") as f:
                    data = json.load(f)
                    return data
            except (json.JSONDecodeError, FileNotFoundError) as e:
                logger.error(f"Error loading memory: {e}")
                return []
        return []

    def _conversation_exists(self, new_conversation: Dict, existing_conversations: List[Dict]) -> bool:
        new_conv_data = new_conversation.get('model_dump', lambda: new_conversation)()
        new_timestamp = new_conv_data.get('timestamp')
        new_messages = new_conv_data.get('messages', [])
        for existing_conv in existing_conversations:
            if (existing_conv.get('timestamp') == new_timestamp and
                len(existing_conv.get('messages', [])) == len(new_messages)):
                return True
        return False

    def save_conversation(self, conversation: Union[Dict, object]) -> bool:
        try:
            memory = self.load_memory()
            if hasattr(conversation, 'model_dump'):
                conversation_dict = conversation.model_dump()
            else:
                conversation_dict = conversation
            if 'timestamp' not in conversation_dict:
                conversation_dict['timestamp'] = datetime.now().isoformat()
            if self._conversation_exists(conversation_dict, memory):
                return True
            if memory and self._is_conversation_update(conversation_dict, memory[-1]):
                memory[-1] = conversation_dict
            else:
                memory.append(conversation_dict)
            with open(self.memory_file, 'w', encoding='utf-8') as f:
                json.dump(memory, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            logger.error(f"Error saving conversation: {e}")
            return False

    def _is_conversation_update(self, new_conv: Dict, last_conv: Dict) -> bool:
        try:
            new_timestamp = datetime.fromisoformat(new_conv.get('timestamp', ''))
            last_timestamp = datetime.fromisoformat(last_conv.get('timestamp', ''))
            time_diff = abs((new_timestamp - last_timestamp).total_seconds())
            new_msg_count = len(new_conv.get('messages', []))
            last_msg_count = len(last_conv.get('messages', []))
            return time_diff < 300 and new_msg_count > last_msg_count
        except Exception:
            return False

    def get_recent_context(self, max_messages: int = 30) -> List[Dict]:
        memory = self.load_memory()
        all_messages = []
        for conversation in memory:
            if "messages" in conversation:
                all_messages.extend(conversation["messages"])
        return all_messages[-max_messages:] if all_messages else []

    def get_conversation_count(self) -> int:
        return len(self.load_memory())


# ✅ Default memory instance — brain.py use pannuvathu ithey
_memory = ConversationMemory(user_id="jarvis_user")


# ✅ Wrapper functions — brain.py import pannuvathu ithey

@function_tool
async def load_memory() -> str:
    """Load and return recent conversation memory as a formatted string."""
    messages = _memory.get_recent_context(max_messages=20)
    if not messages:
        return "No previous conversations found."
    result = []
    for msg in messages:
        role = msg.get("role", "unknown")
        content = msg.get("content", "")
        result.append(f"{role}: {content}")
    return "\n".join(result)


@function_tool
async def save_memory(content: str) -> str:
    """
    Save a conversation or important note to memory.
    Use this when user asks to remember something.
    """
    conversation = {
        "timestamp": datetime.now().isoformat(),
        "messages": [
            {"role": "user", "content": content}
        ]
    }
    success = _memory.save_conversation(conversation)
    if success:
        return "Seri sir, memory-la save aaiduchu!"
    return "Memory save aagala, error vandhuchu."


@function_tool
async def get_recent_conversations(limit: int = 5) -> str:
    """
    Get the most recent conversations from memory.
    Use this to recall what was discussed earlier.
    """
    messages = _memory.get_recent_context(max_messages=limit * 2)
    if not messages:
        return "No conversations found."
    result = []
    for msg in messages:
        role = msg.get("role", "unknown")
        content = msg.get("content", "")
        result.append(f"{role}: {content}")
    return "\n".join(result)


@function_tool
async def add_memory_entry(note: str) -> str:
    """
    Add a specific note or fact to memory for future reference.
    Example: 'Remember that user likes dark mode'
    """
    conversation = {
        "timestamp": datetime.now().isoformat(),
        "messages": [
            {"role": "system", "content": f"[Memory Note] {note}"}
        ]
    }
    success = _memory.save_conversation(conversation)
    if success:
        return f"Note memory-la add aaiduchu: {note}"
    return "Note add aagala, error vandhuchu."