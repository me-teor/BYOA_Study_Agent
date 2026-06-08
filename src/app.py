from __future__ import annotations

import json
import os
import sys
from typing import Any, Dict, List, Optional, Tuple

from rich import box
from rich.align import Align
from rich.columns import Columns
from rich.console import Console, Group
from rich.markdown import Markdown
from rich.panel import Panel
from rich.prompt import Prompt
from rich.rule import Rule
from rich.table import Table
from rich.text import Text

from agent import MODEL, TOOL_SCHEMAS, run_agent
from tools import ROOT_DIR, list_documents


console = Console()

APP_NAME = "BYOA Study Agent"
APP_VERSION = "v0.2.0"
APP_SUBTITLE = "Local-first course assistant with tool use and web fallback"

TRACE_PREVIEW_CHARS = 360

QUICK_ACTIONS: List[Tuple[str, str]] = [
    ("/docs", "查看本地资料库"),
    ("/tools", "查看 Agent 工具技能"),
    ("/outputs", "查看已生成笔记"),
    ("/status", "刷新运行状态"),
    ("/help", "查看帮助命令"),
    ("/clear", "重绘首页界面"),
    ("/exit", "退出程序"),
]

ASCII_LOGO = r"""
 ____   __   __   ___     _       ____  _____  _   _  ____ __   __      _     ____  _____ _   _ _____
| __ )  \ \ / /  / _ \   / \     / ___||_   _|| | | ||  _ \\ \ / /     / \   / ___|| ____|| \ | |_   _|
|  _ \   \ V /  | | | | / _ \    \___ \  | |  | | | || | | |\ V /     / _ \ | |  _ |  _|  |  \| | | |
| |_) |   | |   | |_| |/ ___ \    ___) | | |  | |_| || |_| | | |     / ___ \| |_| || |___ | |\  | | |
|____/    |_|    \___//_/   \_\  |____/  |_|   \___/ |____/  |_|    /_/   \_\\____||_____||_| \_| |_|
"""


def clear_screen() -> None:
    os.system("cls" if os.name == "nt" else "clear")


def safe_parse_json(value: Any) -> Optional[Any]:
    if isinstance(value, (dict, list)):
        return value

    if not isinstance(value, str):
        return None

    try:
        return json.loads(value)
    except Exception:
        return None


def short_text(value: Any, limit: int = 120) -> str:
    text = str(value)
    text = text.replace("\n", " ").replace("\r", " ").strip()

    if len(text) <= limit:
        return text

    return text[: limit - 3] + "..."


def get_docs_count() -> int:
    try:
        return int(list_documents().get("count", 0))
    except Exception:
        return 0


def get_outputs_count() -> int:
    outputs_dir = ROOT_DIR / "outputs"

    if not outputs_dir.exists():
        return 0

    return len(list(outputs_dir.glob("*.md")))


def get_env_status() -> str:
    return "on" if (ROOT_DIR / ".env").exists() else "off"


def get_tool_style(tool_name: str) -> Dict[str, str]:
    mapping = {
        "list_documents": {
            "label": "DOCS",
            "style": "bright_cyan",
            "border": "bright_cyan",
        },
        "read_document": {
            "label": "READ",
            "style": "blue",
            "border": "blue",
        },
        "search_documents": {
            "label": "LOCAL",
            "style": "yellow",
            "border": "yellow",
        },
        "search_local_then_web": {
            "label": "HYBRID",
            "style": "magenta",
            "border": "magenta",
        },
        "web_search": {
            "label": "WEB",
            "style": "red",
            "border": "red",
        },
        "analyze_csv": {
            "label": "CSV",
            "style": "green",
            "border": "green",
        },
        "save_markdown_note": {
            "label": "SAVE",
            "style": "bright_green",
            "border": "bright_green",
        },
    }

    return mapping.get(
        tool_name,
        {
            "label": "TOOL",
            "style": "white",
            "border": "white",
        },
    )


def read_key() -> str:
    """
    Read one key from terminal.

    Return values:
    - UP
    - DOWN
    - ENTER
    - BACKSPACE
    - CTRL_C
    - CHAR:<char>
    """
    if os.name == "nt":
        import msvcrt

        ch = msvcrt.getwch()

        if ch in ("\x00", "\xe0"):
            ch2 = msvcrt.getwch()

            if ch2 == "H":
                return "UP"

            if ch2 == "P":
                return "DOWN"

            return ""

        if ch == "\r":
            return "ENTER"

        if ch == "\x08":
            return "BACKSPACE"

        if ch == "\x03":
            return "CTRL_C"

        if ch:
            return f"CHAR:{ch}"

        return ""

    import termios
    import tty

    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)

    try:
        tty.setraw(fd)
        ch = sys.stdin.read(1)

        if ch == "\x03":
            return "CTRL_C"

        if ch in ("\r", "\n"):
            return "ENTER"

        if ch in ("\x7f", "\b"):
            return "BACKSPACE"

        if ch == "\x1b":
            seq = sys.stdin.read(2)

            if seq == "[A":
                return "UP"

            if seq == "[B":
                return "DOWN"

            return ""

        if ch:
            return f"CHAR:{ch}"

        return ""

    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)


def render_header() -> Panel:
    logo = Text(ASCII_LOGO, style="bright_cyan")
    title = Text(f"{APP_NAME} / {APP_VERSION}", style="bold bright_cyan")
    subtitle = Text(APP_SUBTITLE, style="dim")

    return Panel(
        Align.center(
            Group(
                Align.center(logo),
                Align.center(subtitle),
            )
        ),
        title=title,
        border_style="bright_cyan",
        box=box.ROUNDED,
        padding=(1, 2),
    )


def render_status_panel() -> Panel:
    status_table = Table.grid(expand=True)
    status_table.add_column(ratio=1)
    status_table.add_column(ratio=1)

    left_status = Text()
    left_status.append("项目 / Project   ", style="dim")
    left_status.append(str(ROOT_DIR), style="white")
    left_status.append("\n模型 / Model     ", style="dim")
    left_status.append(MODEL, style="bright_white")
    left_status.append("\n工具 / Tools     ", style="dim")
    left_status.append(f"{len(TOOL_SCHEMAS)} tools", style="bright_cyan")

    right_status = Text()
    right_status.append("资料 / Docs      ", style="dim")
    right_status.append(f"{get_docs_count()} files", style="yellow")
    right_status.append("\n笔记 / Notes     ", style="dim")
    right_status.append(f"{get_outputs_count()} markdown files", style="bright_green")
    right_status.append("\n.env / API       ", style="dim")

    env_status = get_env_status()
    right_status.append(
        env_status,
        style="green" if env_status == "on" else "red",
    )

    status_table.add_row(left_status, right_status)

    return Panel(
        status_table,
        title="[bold bright_cyan]会话状态 / Status[/bold bright_cyan]",
        border_style="bright_cyan",
        box=box.ROUNDED,
        padding=(1, 2),
    )


def render_actions_panel(selected_index: int, focus_area: str) -> Panel:
    actions = Table.grid(expand=True)
    actions.add_column(width=22)
    actions.add_column()

    for index, (command, description) in enumerate(QUICK_ACTIONS):
        is_selected = focus_area == "actions" and index == selected_index
        is_exit_command = command in {"/exit", "exit", "quit"}

        if is_selected:
            command_text = Text(f"➤ {command}", style="bold black on bright_cyan")
            desc_text = Text(description, style="bold black on bright_cyan")
        else:
            command_style = "bold red" if is_exit_command else "bold bright_cyan"
            desc_style = "red" if is_exit_command else "white"

            command_text = Text(f"  {command}", style=command_style)
            desc_text = Text(description, style=desc_style)

        actions.add_row(command_text, desc_text)

    hint = Text()
    hint.append("\n↑/↓ 选择命令  ", style="dim")
    hint.append("Enter 执行", style="bold yellow")
    hint.append("  ·  ", style="dim")
    hint.append("↓ 到底进入输入行", style="dim")

    content = Group(actions, hint)

    return Panel(
        content,
        title="[bold blue]快速动作 / Actions[/bold blue]",
        border_style="blue" if focus_area == "actions" else "bright_black",
        box=box.ROUNDED,
        padding=(1, 2),
        height=14,
    )


def render_input_rules_panel() -> Panel:
    rules = Text()
    rules.append("/help", style="bold bright_cyan")
    rules.append(" 查看命令    ")
    rules.append("/status", style="bold bright_cyan")
    rules.append(" 查看状态    ")
    rules.append("/exit", style="bold red")
    rules.append(" 退出\n")
    rules.append("也可以输入 ", style="white")
    rules.append("exit", style="bold red")
    rules.append(" 或 ", style="white")
    rules.append("quit", style="bold red")
    rules.append(" 退出程序。\n", style="white")
    rules.append("直接输入自然语言即可追问；以 ")
    rules.append("根据本地资料", style="bold yellow")
    rules.append(" 开头可强化本地检索。")

    return Panel(
        rules,
        title="[bold magenta]输入规则 / Input[/bold magenta]",
        border_style="magenta",
        box=box.ROUNDED,
        padding=(1, 2),
        height=7,
    )


def render_about_panel() -> Panel:
    about = Text()
    about.append("BYOA Study Agent", style="bold yellow")
    about.append(" · Experiment 2\n", style="dim")
    about.append(
        "Local Search · CSV Analysis · Web Fallback · Markdown Notes",
        style="yellow",
    )

    return Panel(
        Align.center(about),
        title="[bold yellow]关于 / About[/bold yellow]",
        border_style="yellow",
        box=box.ROUNDED,
        padding=(1, 2),
        height=7,
    )


def render_command_input_line(buffer: str, focus_area: str) -> Panel:
    prompt = Text()

    if focus_area == "input":
        prompt.append("BYOA>: ", style="bold bright_cyan")
        prompt.append(buffer, style="white")
        prompt.append("█", style="bold bright_cyan")
    else:
        prompt.append("BYOA>: ", style="dim")
        prompt.append(buffer, style="dim")
        prompt.append("  ", style="dim")
        prompt.append("当前焦点在快速动作区。按 ↓ 到底进入输入行。", style="dim")

    return Panel(
        prompt,
        title="[bold bright_cyan]命令输入 / Command Input[/bold bright_cyan]",
        border_style="bright_cyan" if focus_area == "input" else "bright_black",
        box=box.ROUNDED,
        padding=(0, 1),
    )


def render_home(
    selected_index: int = 0,
    focus_area: str = "actions",
    buffer: str = "",
) -> None:
    """
    Render RepoPilot-like cockpit home screen.
    """
    clear_screen()

    right_group = Group(
        render_input_rules_panel(),
        render_about_panel(),
    )

    console.print(render_header())
    console.print(render_status_panel())
    console.print(
        Columns(
            [
                render_actions_panel(selected_index, focus_area),
                right_group,
            ],
            equal=True,
            expand=True,
        )
    )
    console.print(render_command_input_line(buffer, focus_area))


def read_interactive_command() -> str:
    """
    Read command/query with arrow-key navigation.

    Movement rules:
    - UP in quick actions: move up, stop at first item.
    - DOWN in quick actions: move down.
    - DOWN at last quick action: jump to input line.
    - DOWN in input line: no movement.
    - UP in empty input line: jump back to last quick action.
    - ENTER in quick actions: execute selected command.
    - ENTER in input line: submit text.
    """
    selected_index = 0
    focus_area = "actions"
    buffer = ""

    while True:
        render_home(
            selected_index=selected_index,
            focus_area=focus_area,
            buffer=buffer,
        )

        key = read_key()

        if key == "CTRL_C":
            raise KeyboardInterrupt

        if key == "UP":
            if focus_area == "actions":
                selected_index = max(0, selected_index - 1)
            elif focus_area == "input" and not buffer:
                focus_area = "actions"
                selected_index = len(QUICK_ACTIONS) - 1
            continue

        if key == "DOWN":
            if focus_area == "actions":
                if selected_index < len(QUICK_ACTIONS) - 1:
                    selected_index += 1
                else:
                    focus_area = "input"
            elif focus_area == "input":
                pass
            continue

        if key == "ENTER":
            if focus_area == "actions":
                return QUICK_ACTIONS[selected_index][0]

            return buffer.strip()

        if key == "BACKSPACE":
            if focus_area == "input":
                buffer = buffer[:-1]
            continue

        if key.startswith("CHAR:"):
            char = key.removeprefix("CHAR:")

            if char == "\x1b":
                continue

            if focus_area == "actions":
                focus_area = "input"
                buffer = char
            else:
                buffer += char

            continue


def wait_to_return_home() -> None:
    console.print()
    console.print(
        Panel(
            "按 Enter 返回首页，或按 Ctrl+C 继续停留在当前输出。",
            title="[bold bright_cyan]Continue[/bold bright_cyan]",
            border_style="bright_black",
            box=box.ROUNDED,
        )
    )

    try:
        Prompt.ask("[dim]Press Enter[/dim]", default="")
    except KeyboardInterrupt:
        console.print()


def render_help() -> None:
    table = Table(
        title="命令菜单 / Command Menu",
        title_style="bold bright_cyan",
        border_style="bright_cyan",
        box=box.ROUNDED,
        show_lines=True,
    )

    table.add_column("命令", style="bold yellow", no_wrap=True)
    table.add_column("说明", style="white")

    table.add_row("/help", "显示帮助菜单。")
    table.add_row("/status", "显示模型、资料库、工具数量和输出文件状态。")
    table.add_row("/docs", "列出 data/ 目录中的本地课程资料。")
    table.add_row("/tools", "列出 Agent 当前具备的所有工具技能。")
    table.add_row("/outputs", "列出 outputs/ 目录中已经生成的 Markdown 笔记。")
    table.add_row("/clear", "清空终端并重新显示首页。")
    table.add_row("/exit", "退出程序。")
    table.add_row("exit / quit", "退出程序。")

    examples = """
### 推荐测试问题

1. 根据本地资料，解释 SAST、DAST 和 SCA 的区别。
2. 请根据本地资料总结 MCP 的核心组件，并保存成 markdown 复习笔记。
3. 请解释 Python 3.12 的主要新特性，并保存成 markdown 复习笔记。
4. 请分析 study_scores.csv 中的成绩数据。
5. 根据本地资料，比较 zero-shot、k-shot 和 chain-of-thought prompting。
"""

    console.print(table)
    console.print(
        Panel(
            Markdown(examples),
            title="[bold green]示例 / Examples[/bold green]",
            border_style="green",
            box=box.ROUNDED,
            padding=(1, 2),
        )
    )


def render_status() -> None:
    table = Table(
        title="运行状态 / System Status",
        title_style="bold bright_cyan",
        border_style="bright_cyan",
        box=box.ROUNDED,
        show_header=True,
        header_style="bold white",
    )

    table.add_column("项目", style="bold")
    table.add_column("值", style="white")

    env_status = get_env_status()

    table.add_row("Project", str(ROOT_DIR))
    table.add_row("Model", f"[green]{MODEL}[/green]")
    table.add_row("Local Docs", f"[yellow]{get_docs_count()} files[/yellow]")
    table.add_row("Tools", f"[bright_cyan]{len(TOOL_SCHEMAS)} tools[/bright_cyan]")
    table.add_row("Search Mode", "[magenta]Local First → Web Fallback[/magenta]")
    table.add_row(
        "Output Notes",
        f"[bright_green]{get_outputs_count()} markdown files[/bright_green]",
    )
    table.add_row(
        ".env",
        f"[green]{env_status}[/green]" if env_status == "on" else f"[red]{env_status}[/red]",
    )

    console.print(table)


def render_docs() -> None:
    result = list_documents()
    docs = result.get("documents", [])

    table = Table(
        title=f"本地资料库 / Local Course Library：{result.get('count', 0)} files",
        title_style="bold bright_cyan",
        border_style="green",
        box=box.ROUNDED,
        show_lines=True,
    )

    table.add_column("#", justify="right", style="dim", width=4)
    table.add_column("文件名 / Filename", style="bold white")
    table.add_column("类型", style="cyan", width=8)
    table.add_column("大小", justify="right", style="magenta")

    for index, doc in enumerate(docs, start=1):
        table.add_row(
            str(index),
            doc.get("filename", ""),
            doc.get("type", ""),
            f"{doc.get('size_bytes', 0)} bytes",
        )

    console.print(table)


def render_tools() -> None:
    table = Table(
        title="工具技能 / Agent Tool Skills",
        title_style="bold bright_cyan",
        border_style="blue",
        box=box.ROUNDED,
        show_lines=True,
    )

    table.add_column("#", justify="right", style="dim", width=4)
    table.add_column("标签", style="bold")
    table.add_column("工具名", style="bold bright_cyan")
    table.add_column("说明", style="white")

    for index, schema in enumerate(TOOL_SCHEMAS, start=1):
        fn = schema.get("function", {})
        tool_name = fn.get("name", "")
        description = fn.get("description", "")
        style = get_tool_style(tool_name)

        table.add_row(
            str(index),
            f"[{style['style']}]{style['label']}[/{style['style']}]",
            tool_name,
            description,
        )

    console.print(table)


def render_outputs() -> None:
    outputs_dir = ROOT_DIR / "outputs"
    outputs_dir.mkdir(exist_ok=True)

    files = sorted(
        outputs_dir.glob("*.md"),
        key=lambda path: path.stat().st_mtime,
        reverse=True,
    )

    table = Table(
        title=f"已生成笔记 / Generated Markdown Notes：{len(files)} files",
        title_style="bold bright_green",
        border_style="bright_green",
        box=box.ROUNDED,
        show_lines=True,
    )

    table.add_column("#", justify="right", style="dim", width=4)
    table.add_column("文件名", style="bold white")
    table.add_column("大小", justify="right", style="magenta")
    table.add_column("路径", style="dim")

    for index, path in enumerate(files, start=1):
        table.add_row(
            str(index),
            path.name,
            f"{path.stat().st_size} bytes",
            str(path),
        )

    console.print(table)


def render_user_query(user_input: str) -> None:
    console.print()
    console.print(
        Text.assemble(
            ("BYOA> ", "bold bright_cyan"),
            (user_input, "white"),
        )
    )
    console.print(
        Panel(
            user_input,
            title="[bold bright_cyan]你 / You[/bold bright_cyan]",
            border_style="bright_black",
            box=box.ROUNDED,
            padding=(1, 2),
        )
    )


def render_thinking() -> Panel:
    return Panel(
        "处理追问。按 Ctrl+C 可尝试中断。",
        title="[bold magenta]运行中 / Thinking[/bold magenta]",
        border_style="magenta",
        box=box.ROUNDED,
        padding=(1, 2),
    )


def render_tool_summary(tool_trace: List[Dict[str, Any]]) -> None:
    if not tool_trace:
        console.print(
            Panel(
                "[yellow]No tool call in this round.[/yellow]\n"
                "[dim]提示：如果希望强制使用本地资料，可输入“根据本地资料……”。[/dim]",
                title="[bold yellow]工具链 / Tool Trace[/bold yellow]",
                border_style="yellow",
                box=box.ROUNDED,
            )
        )
        return

    table = Table(
        title="工具链 / Tool Trace",
        title_style="bold blue",
        border_style="blue",
        box=box.ROUNDED,
        show_lines=True,
    )

    table.add_column("#", justify="right", style="dim", width=4)
    table.add_column("标签", style="bold")
    table.add_column("工具", style="bold bright_cyan")
    table.add_column("关键参数", style="white")

    for index, item in enumerate(tool_trace, start=1):
        tool_name = item.get("tool", "")
        args = item.get("arguments", {})
        style = get_tool_style(tool_name)

        key_parts = []

        for key in ["query", "filename", "title"]:
            if key in args:
                key_parts.append(f"{key}={short_text(args[key], 60)}")

        if not key_parts:
            key_parts.append(short_text(json.dumps(args, ensure_ascii=False), 80))

        table.add_row(
            str(index),
            f"[{style['style']}]{style['label']}[/{style['style']}]",
            tool_name,
            "; ".join(key_parts),
        )

    console.print(table)


def extract_result(item: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    result = item.get("result")

    if isinstance(result, dict):
        return result

    parsed = safe_parse_json(item.get("result_preview", ""))

    if isinstance(parsed, dict):
        return parsed

    return None


def render_local_evidence(result: Dict[str, Any]) -> None:
    results = result.get("results", [])

    if not results:
        console.print(
            Panel(
                "[yellow]本地资料库没有找到相关证据。[/yellow]",
                title="[bold yellow]本地证据 / Local Evidence[/bold yellow]",
                border_style="yellow",
                box=box.ROUNDED,
            )
        )
        return

    for index, evidence in enumerate(results[:2], start=1):
        filename = evidence.get("filename", "unknown")
        score = evidence.get("score", 0)
        snippet = evidence.get("snippet", "")

        content = Text()
        content.append("Source: ", style="bold")
        content.append(filename, style="yellow")
        content.append("\nScore: ", style="bold")
        content.append(str(score), style="green")
        content.append("\n\n")
        content.append(snippet[:TRACE_PREVIEW_CHARS], style="white")

        console.print(
            Panel(
                content,
                title=f"[bold yellow]本地证据 / Local Evidence {index}[/bold yellow]",
                border_style="yellow",
                box=box.ROUNDED,
                padding=(1, 2),
            )
        )


def render_web_results(result: Dict[str, Any]) -> None:
    results = result.get("results", [])

    if not results:
        console.print(
            Panel(
                "[red]网络搜索没有返回结果，或搜索失败。[/red]",
                title="[bold red]网络搜索 / Web Search[/bold red]",
                border_style="red",
                box=box.ROUNDED,
            )
        )
        return

    table = Table(
        title="网络搜索结果 / Web Search Results",
        title_style="bold magenta",
        border_style="magenta",
        box=box.ROUNDED,
        show_lines=True,
    )

    table.add_column("#", justify="right", style="dim", width=4)
    table.add_column("标题", style="bold white", max_width=36)
    table.add_column("摘要", style="white", max_width=70)
    table.add_column("链接", style="cyan", max_width=45)

    for index, result_item in enumerate(results[:5], start=1):
        table.add_row(
            str(index),
            short_text(result_item.get("title", ""), 55),
            short_text(result_item.get("snippet", ""), 120),
            short_text(result_item.get("url", ""), 60),
        )

    console.print(table)


def render_hybrid_result(result: Dict[str, Any]) -> None:
    source_used = result.get("source_used", "unknown")

    if source_used == "local_documents":
        console.print(
            Panel(
                "[green]Source Used: Local Documents[/green]\n"
                "[dim]本轮回答优先基于 data/ 本地资料库。[/dim]",
                title="[bold green]混合检索决策 / Hybrid Decision[/bold green]",
                border_style="green",
                box=box.ROUNDED,
            )
        )
        local_result = result.get("local_result") or {}
        render_local_evidence(local_result)
        return

    if source_used == "web_search":
        console.print(
            Panel(
                "[magenta]Source Used: Web Search[/magenta]\n"
                "[dim]Reason: no relevant local document was found.[/dim]",
                title="[bold magenta]混合检索决策 / Hybrid Decision[/bold magenta]",
                border_style="magenta",
                box=box.ROUNDED,
            )
        )
        web_result = result.get("web_result") or {}
        render_web_results(web_result)
        return

    console.print(
        Panel(
            json.dumps(result, ensure_ascii=False, indent=2),
            title="[bold white]Hybrid Result[/bold white]",
            border_style="white",
            box=box.ROUNDED,
        )
    )


def render_csv_result(result: Dict[str, Any]) -> None:
    numeric_stats = result.get("numeric_stats", {})

    table = Table(
        title=f"CSV 分析 / CSV Analysis：{result.get('filename', '')}",
        title_style="bold green",
        border_style="green",
        box=box.ROUNDED,
        show_lines=True,
    )

    table.add_column("字段", style="bold white")
    table.add_column("Count", justify="right", style="cyan")
    table.add_column("Min", justify="right", style="yellow")
    table.add_column("Max", justify="right", style="yellow")
    table.add_column("Average", justify="right", style="bright_green")

    for column, stats in numeric_stats.items():
        table.add_row(
            column,
            str(stats.get("count", "")),
            str(stats.get("min", "")),
            str(stats.get("max", "")),
            str(stats.get("average", "")),
        )

    console.print(table)


def render_saved_note(result: Dict[str, Any]) -> None:
    if not result.get("ok"):
        console.print(
            Panel(
                json.dumps(result, ensure_ascii=False, indent=2),
                title="[bold red]保存失败 / Save Failed[/bold red]",
                border_style="red",
                box=box.ROUNDED,
            )
        )
        return

    content = Text()
    content.append("Markdown note saved successfully.\n\n", style="bold bright_green")
    content.append("File: ", style="bold")
    content.append(result.get("filename", ""), style="white")
    content.append("\nPath: ", style="bold")
    content.append(result.get("path", ""), style="bright_cyan")
    content.append("\nSize: ", style="bold")
    content.append(f"{result.get('size_bytes', 0)} bytes", style="yellow")

    console.print(
        Panel(
            content,
            title="[bold bright_green]已保存 / Saved Markdown Note[/bold bright_green]",
            border_style="bright_green",
            box=box.ROUNDED,
            padding=(1, 2),
        )
    )


def render_tool_results(tool_trace: List[Dict[str, Any]]) -> None:
    if not tool_trace:
        return

    console.print(
        Rule(
            "[bold bright_cyan]证据与结果 / Evidence and Tool Results[/bold bright_cyan]",
            style="bright_black",
        )
    )

    for item in tool_trace:
        tool_name = item.get("tool", "")
        result = extract_result(item)

        if not isinstance(result, dict):
            continue

        if tool_name == "search_documents":
            render_local_evidence(result)
        elif tool_name == "search_local_then_web":
            render_hybrid_result(result)
        elif tool_name == "web_search":
            render_web_results(result)
        elif tool_name == "analyze_csv":
            render_csv_result(result)
        elif tool_name == "save_markdown_note":
            render_saved_note(result)


def render_answer(answer: str) -> None:
    console.print(
        Rule(
            "[bold bright_cyan]回复 / Answer[/bold bright_cyan]",
            style="bright_black",
        )
    )

    if not answer.strip():
        console.print(
            Panel(
                "[red]Agent did not return a valid answer.[/red]",
                title="[bold red]回复 / Answer[/bold red]",
                border_style="red",
                box=box.ROUNDED,
            )
        )
        return

    try:
        rendered = Markdown(answer)
    except Exception:
        rendered = answer

    console.print(
        Panel(
            rendered,
            title="[bold bright_cyan]回复 / Answer[/bold bright_cyan]",
            border_style="bright_cyan",
            box=box.ROUNDED,
            padding=(1, 2),
        )
    )


def handle_special_command(user_input: str) -> bool:
    command = user_input.strip().lower()

    if command in {"/help", "help"}:
        render_help()
        return True

    if command in {"/status", "status"}:
        render_status()
        return True

    if command in {"/docs", "docs"}:
        render_docs()
        return True

    if command in {"/tools", "tools"}:
        render_tools()
        return True

    if command in {"/outputs", "outputs"}:
        render_outputs()
        return True

    if command in {"/clear", "clear", "cls"}:
        render_home()
        return True

    return False


def main() -> None:
    while True:
        try:
            user_input = read_interactive_command()
        except KeyboardInterrupt:
            console.print("\n[bold red]已中断当前输入。[/bold red]")
            wait_to_return_home()
            continue

        if user_input.lower() in {"exit", "quit", "/exit"}:
            clear_screen()
            console.print(
                Panel(
                    "[bold green]已退出 BYOA Study Agent。[/bold green]",
                    border_style="green",
                    box=box.ROUNDED,
                )
            )
            break

        if not user_input:
            continue

        clear_screen()

        if handle_special_command(user_input):
            wait_to_return_home()
            continue

        render_user_query(user_input)
        console.print(render_thinking())

        try:
            with console.status(
                "[bold green]Agent 正在选择工具并生成回答...[/bold green]",
                spinner="dots",
            ):
                answer, tool_trace = run_agent(user_input)
        except KeyboardInterrupt:
            console.print(
                Panel(
                    "[red]本轮请求已被用户中断。[/red]",
                    title="[bold red]中断 / Interrupted[/bold red]",
                    border_style="red",
                    box=box.ROUNDED,
                )
            )
            wait_to_return_home()
            continue
        except Exception as exc:
            console.print(
                Panel(
                    str(exc),
                    title="[bold red]运行错误 / Runtime Error[/bold red]",
                    border_style="red",
                    box=box.ROUNDED,
                )
            )
            wait_to_return_home()
            continue

        render_tool_summary(tool_trace)
        render_tool_results(tool_trace)
        render_answer(answer)
        wait_to_return_home()


if __name__ == "__main__":
    main()