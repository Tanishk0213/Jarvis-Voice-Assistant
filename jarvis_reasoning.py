from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.agents import create_react_agent, AgentExecutor
from dotenv import load_dotenv
from jarvis_search import search_internet as google_search, get_formatted_datetime as get_current_datetime
from jarvis_get_whether import get_weather
from Jarvis_window_CTRL import (
    open_common_app as open_app,
    run_application_or_media as close_app,
    list_folder_items as folder_file
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
from langchain import hub
import asyncio
from livekit.agents import function_tool

load_dotenv()


@function_tool(
    name="thinking_capability",
    description=(
        "Use this tool whenever the user asks to generate or write something new. "
        "If the user does not specify where to write, open Notepad automatically using open_app and start writing. "
        "This tool can also handle tasks like Google search, checking the weather, "
        "opening/closing apps, accessing files, controlling mouse/keyboard, "
        "and system utilities."
    )
)
async def thinking_capability(query: str) -> dict:
    """
    LangChain-powered reasoning and action tool.
    Takes a natural language query and executes the appropriate workflow.
    """
    model = ChatGoogleGenerativeAI(model="gemini-2.0-flash")

    prompt = hub.pull("hwchase17/react")

    tools = [
        google_search,
        get_current_datetime,
        get_weather,
        open_app,
        close_app,
        folder_file,
        Play_file,
        move_cursor_tool,
        mouse_click_tool,
        scroll_cursor_tool,
        type_text_tool,
        press_key_tool,
        press_hotkey_tool,
        control_volume_tool,
        swipe_gesture_tool
    ]

    agent = create_react_agent(
        llm=model,
        tools=tools,
        prompt=prompt
    )

    executor = AgentExecutor(
        agent=agent,
        tools=tools,
        verbose=True
    )

    try:
        result = await executor.ainvoke({"input": query})
        return result
    except Exception as e:
        return {"error": f"Agent execution failed: {str(e)}"}