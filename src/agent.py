import json
import os
from typing import Any, Dict, List, Tuple

from dotenv import load_dotenv
from openai import OpenAI

from prompts import SYSTEM_PROMPT
from tools import (
    ROOT_DIR,
    analyze_csv,
    list_documents,
    read_document,
    save_markdown_note,
    search_documents,
    search_local_then_web,
    web_search,
)


load_dotenv(ROOT_DIR / ".env")


client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
    base_url=os.getenv("OPENAI_BASE_URL") or None,
)

MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")


TOOL_SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "list_documents",
            "description": "List all local course documents in the data folder.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "read_document",
            "description": "Read the content of a specific local course document.",
            "parameters": {
                "type": "object",
                "properties": {
                    "filename": {
                        "type": "string",
                        "description": "The file name inside the data folder.",
                    },
                    "max_chars": {
                        "type": "integer",
                        "description": "Maximum number of characters to read.",
                        "default": 5000,
                    },
                },
                "required": ["filename"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_documents",
            "description": "Search local course documents for relevant snippets.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search keyword or question.",
                    },
                    "max_results": {
                        "type": "integer",
                        "description": "Maximum number of search results.",
                        "default": 5,
                    },
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "analyze_csv",
            "description": (
                "Analyze a CSV file in the data folder and return columns, "
                "row count, preview rows, and numeric statistics."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "filename": {
                        "type": "string",
                        "description": "The CSV file name inside the data folder.",
                    },
                },
                "required": ["filename"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "save_markdown_note",
            "description": (
                "Save a generated study note or summary as a markdown file "
                "in the outputs folder."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "title": {
                        "type": "string",
                        "description": "The title of the markdown note.",
                    },
                    "content": {
                        "type": "string",
                        "description": "The markdown content to save.",
                    },
                },
                "required": ["title", "content"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "web_search",
            "description": (
                "Search the web for external information when local documents "
                "do not contain enough information."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The web search query.",
                    },
                    "max_results": {
                        "type": "integer",
                        "description": "Maximum number of web results.",
                        "default": 5,
                    },
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_local_then_web",
            "description": (
                "Search local documents first. If no local result is found, "
                "automatically fall back to web search."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The search query.",
                    },
                    "max_results": {
                        "type": "integer",
                        "description": "Maximum number of results.",
                        "default": 5,
                    },
                },
                "required": ["query"],
            },
        },
    },
]


def _dispatch_tool(name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
    """
    Execute the selected tool and return a structured result.
    """
    try:
        if name == "list_documents":
            return list_documents()

        if name == "read_document":
            return read_document(
                filename=arguments["filename"],
                max_chars=arguments.get("max_chars", 5000),
            )

        if name == "search_documents":
            return search_documents(
                query=arguments["query"],
                max_results=arguments.get("max_results", 5),
            )

        if name == "analyze_csv":
            return analyze_csv(
                filename=arguments["filename"],
            )

        if name == "save_markdown_note":
            return save_markdown_note(
                title=arguments["title"],
                content=arguments["content"],
            )

        if name == "web_search":
            return web_search(
                query=arguments["query"],
                max_results=arguments.get("max_results", 5),
            )

        if name == "search_local_then_web":
            return search_local_then_web(
                query=arguments["query"],
                max_results=arguments.get("max_results", 5),
            )

        return {
            "ok": False,
            "error": f"Unknown tool: {name}",
        }

    except Exception as exc:
        return {
            "ok": False,
            "error": str(exc),
            "tool": name,
            "arguments": arguments,
        }


def _user_requested_save(user_input: str) -> bool:
    """
    Detect whether the user explicitly asked to save a note/file.
    """
    keywords = [
        "保存",
        "存成",
        "生成文件",
        "markdown",
        "md",
        "复习笔记",
        "笔记",
        "导出",
        "save",
    ]

    lowered = user_input.lower()
    return any(keyword.lower() in lowered for keyword in keywords)


def _has_saved_note(tool_trace: List[Dict[str, Any]]) -> bool:
    """
    Check whether save_markdown_note has already been called.
    """
    return any(item.get("tool") == "save_markdown_note" for item in tool_trace)


def _guess_note_title(user_input: str) -> str:
    """
    Generate a readable title for auto-saved markdown notes.
    """
    lowered = user_input.lower()

    if "python 3.12" in lowered:
        return "Python 3.12 新特性复习笔记"

    if "python 3.13" in lowered:
        return "Python 3.13 新特性复习笔记"

    if "mcp" in lowered:
        return "MCP 复习笔记"

    if "sast" in lowered or "dast" in lowered or "sca" in lowered:
        return "软件安全测试复习笔记"

    if "prompt" in lowered or "prompting" in lowered:
        return "Prompting 技术复习笔记"

    return "自动保存的复习笔记"


def _auto_save_if_requested(
    user_input: str,
    final_answer: str,
    tool_trace: List[Dict[str, Any]],
) -> str:
    """
    If the user asked to save a markdown note but the model forgot to call
    save_markdown_note, save the final answer automatically.
    """
    if not _user_requested_save(user_input):
        return final_answer

    if _has_saved_note(tool_trace):
        return final_answer

    if not final_answer.strip():
        return final_answer

    title = _guess_note_title(user_input)

    save_result = save_markdown_note(
        title=title,
        content=final_answer,
    )

    tool_trace.append(
        {
            "tool": "save_markdown_note",
            "arguments": {
                "title": title,
                "content": "[auto-saved final answer]",
            },
            "result": save_result,
            "result_preview": json.dumps(save_result, ensure_ascii=False)[:700],
        }
    )

    if save_result.get("ok"):
        return (
            final_answer
            + "\n\n"
            + "已自动保存为 Markdown 文件：\n"
            + f"`{save_result['path']}`"
        )

    return (
        final_answer
        + "\n\n"
        + f"尝试自动保存 Markdown 文件失败：{save_result.get('error')}"
    )


def _append_tool_trace(
    tool_trace: List[Dict[str, Any]],
    tool_name: str,
    tool_args: Dict[str, Any],
    tool_result: Dict[str, Any],
) -> None:
    """
    Append a normalized tool trace item for UI rendering and report screenshots.
    """
    tool_trace.append(
        {
            "tool": tool_name,
            "arguments": tool_args,
            "result": tool_result,
            "result_preview": json.dumps(tool_result, ensure_ascii=False)[:700],
        }
    )


def run_agent(user_input: str) -> Tuple[str, List[Dict[str, Any]]]:
    """
    Run one user turn of the BYOA Study Agent.

    This version supports:
    1. multiple rounds of tool calling;
    2. local document search;
    3. CSV analysis;
    4. web fallback search;
    5. markdown note saving;
    6. automatic markdown saving if the model forgets to call the save tool.
    """
    if not os.getenv("OPENAI_API_KEY"):
        return (
            "未检测到 OPENAI_API_KEY。请先在项目根目录创建 .env 文件并填写 API Key。",
            [],
        )

    messages: List[Dict[str, Any]] = [
        {
            "role": "system",
            "content": SYSTEM_PROMPT,
        },
        {
            "role": "user",
            "content": user_input,
        },
    ]

    tool_trace: List[Dict[str, Any]] = []
    max_tool_rounds = 6

    for _ in range(max_tool_rounds):
        response = client.chat.completions.create(
            model=MODEL,
            messages=messages,
            tools=TOOL_SCHEMAS,
            tool_choice="auto",
        )

        message = response.choices[0].message
        messages.append(message.model_dump(exclude_none=True))

        if not message.tool_calls:
            final_answer = message.content or ""
            final_answer = _auto_save_if_requested(
                user_input=user_input,
                final_answer=final_answer,
                tool_trace=tool_trace,
            )
            return final_answer, tool_trace

        for tool_call in message.tool_calls:
            tool_name = tool_call.function.name

            try:
                tool_args = json.loads(tool_call.function.arguments or "{}")
            except json.JSONDecodeError:
                tool_args = {}

            tool_result = _dispatch_tool(tool_name, tool_args)

            _append_tool_trace(
                tool_trace=tool_trace,
                tool_name=tool_name,
                tool_args=tool_args,
                tool_result=tool_result,
            )

            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": json.dumps(tool_result, ensure_ascii=False),
                }
            )

    final_response = client.chat.completions.create(
        model=MODEL,
        messages=messages
        + [
            {
                "role": "user",
                "content": (
                    "请根据以上工具调用结果给出最终回答。"
                    "如果使用了本地资料，请说明文件名；"
                    "如果使用了网络搜索，请说明这是网络搜索结果；"
                    "如果保存了文件，请说明保存路径。"
                ),
            }
        ],
    )

    final_answer = final_response.choices[0].message.content or ""
    final_answer = _auto_save_if_requested(
        user_input=user_input,
        final_answer=final_answer,
        tool_trace=tool_trace,
    )

    return final_answer, tool_trace