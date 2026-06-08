import csv
import os
import re
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    from pypdf import PdfReader
except ImportError:
    PdfReader = None

try:
    from ddgs import DDGS
except ImportError:
    DDGS = None


ROOT_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT_DIR / "data"
OUTPUT_DIR = ROOT_DIR / "outputs"

SUPPORTED_SUFFIXES = {".txt", ".md", ".csv", ".pdf"}
EXCLUDED_DIR_NAMES = {"__pycache__", ".git", ".venv", "venv", "env"}


def _normalize_relative_path(filename: str) -> str:
    """
    Normalize user-provided file path.

    Supported input examples:
    - mcp_note.md
    - course/mcp_note.md
    - course\\mcp_note.md
    - csv/student_performance.csv
    """
    filename = filename.strip().replace("\\", "/")
    filename = filename.lstrip("/")

    if not filename:
        raise ValueError("Filename cannot be empty.")

    return filename


def _is_inside_data_dir(path: Path) -> bool:
    """
    Check whether a resolved path is inside DATA_DIR.
    """
    data_root = DATA_DIR.resolve()
    path = path.resolve()

    common_path = os.path.commonpath([str(path), str(data_root)])
    return common_path == str(data_root)


def _relative_display_path(path: Path) -> str:
    """
    Return a POSIX-style relative path for stable display and tool use.
    """
    return path.relative_to(DATA_DIR).as_posix()


def _is_supported_document(path: Path) -> bool:
    """
    Check whether the file is a supported document.
    """
    if not path.is_file():
        return False

    if path.suffix.lower() not in SUPPORTED_SUFFIXES:
        return False

    for part in path.parts:
        if part in EXCLUDED_DIR_NAMES:
            return False

    return True


def _get_category(path: Path) -> str:
    """
    Return first-level folder name as category.

    If the file is directly under data/, category is root.
    """
    relative_parts = path.relative_to(DATA_DIR).parts

    if len(relative_parts) <= 1:
        return "root"

    return relative_parts[0]


def _find_file_by_basename(filename: str) -> Path:
    """
    Recursively find a file by basename inside data/.

    Example:
    user gives:
        student_performance.csv

    actual path:
        data/csv/student_performance.csv

    If multiple files have the same basename, raise an error and list candidates.
    """
    DATA_DIR.mkdir(exist_ok=True)

    target_name = Path(filename).name
    matches: List[Path] = []

    for path in sorted(DATA_DIR.rglob(target_name)):
        if _is_supported_document(path):
            matches.append(path.resolve())

    if len(matches) == 1:
        return matches[0]

    if len(matches) > 1:
        candidates = [_relative_display_path(path) for path in matches]
        raise ValueError(
            "Multiple files with the same name were found. "
            "Please use a relative path instead. Candidates: "
            + ", ".join(candidates)
        )

    raise FileNotFoundError(f"File not found by name: {filename}")


def _safe_path(filename: str) -> Path:
    """
    Resolve a safe file path inside data/.

    Resolution order:
    1. Try the exact relative path under data/.
       Example: csv/student_performance.csv
    2. If it does not exist, search recursively by basename.
       Example: student_performance.csv -> csv/student_performance.csv

    Disallowed:
    - ../.env
    - absolute paths outside data/
    """
    relative_name = _normalize_relative_path(filename)
    exact_path = (DATA_DIR / relative_name).resolve()

    if not _is_inside_data_dir(exact_path):
        raise ValueError("Invalid file path. Only files inside the data folder are allowed.")

    if exact_path.exists():
        return exact_path

    # If exact path does not exist, search by file basename recursively.
    found_path = _find_file_by_basename(relative_name)

    if not _is_inside_data_dir(found_path):
        raise ValueError("Invalid resolved file path. Only files inside the data folder are allowed.")

    return found_path


def list_documents() -> Dict[str, Any]:
    """
    Recursively list supported documents in the data folder.
    """
    DATA_DIR.mkdir(exist_ok=True)

    documents: List[Dict[str, Any]] = []

    for path in sorted(DATA_DIR.rglob("*")):
        if not _is_supported_document(path):
            continue

        relative_path = _relative_display_path(path)

        documents.append(
            {
                "filename": relative_path,
                "name": path.name,
                "category": _get_category(path),
                "type": path.suffix.lower(),
                "size_bytes": path.stat().st_size,
            }
        )

    category_counts = Counter(doc["category"] for doc in documents)

    return {
        "data_dir": str(DATA_DIR),
        "recursive": True,
        "count": len(documents),
        "category_counts": dict(category_counts),
        "documents": documents,
    }


def read_document(filename: str, max_chars: int = 5000) -> Dict[str, Any]:
    """
    Read one document from the data folder.

    Supports:
    - .txt
    - .md
    - .csv
    - .pdf

    Filename can be:
    - exact relative path: csv/student_performance.csv
    - basename only: student_performance.csv
    """
    try:
        path = _safe_path(filename)
    except (ValueError, FileNotFoundError) as exc:
        return {
            "ok": False,
            "error": str(exc),
            "filename": filename,
        }

    if not path.exists():
        return {
            "ok": False,
            "error": f"File not found: {filename}",
        }

    suffix = path.suffix.lower()

    try:
        if suffix in {".txt", ".md", ".csv"}:
            text = path.read_text(encoding="utf-8-sig", errors="ignore")

        elif suffix == ".pdf":
            if PdfReader is None:
                return {
                    "ok": False,
                    "error": "pypdf is not installed. Please run: pip install pypdf",
                }

            reader = PdfReader(str(path))
            pages = []
            for page in reader.pages:
                pages.append(page.extract_text() or "")
            text = "\n".join(pages)

        else:
            return {
                "ok": False,
                "error": f"Unsupported file type: {suffix}",
            }

    except Exception as exc:
        return {
            "ok": False,
            "error": f"Failed to read file: {exc}",
            "filename": filename,
        }

    relative_path = _relative_display_path(path)

    return {
        "ok": True,
        "filename": relative_path,
        "name": path.name,
        "category": _get_category(path),
        "type": suffix,
        "content": text[:max_chars],
        "truncated": len(text) > max_chars,
        "total_chars": len(text),
        "resolved_from": filename,
    }


def _query_terms(query: str) -> List[str]:
    """
    Build search terms from a query.

    For English queries, split by words.
    For Chinese or mixed queries, also keep the full query as a term.
    """
    query = query.strip().lower()

    if not query:
        return []

    terms = [query]

    extracted = re.findall(r"[a-zA-Z0-9_.+#-]+", query)
    terms.extend(extracted)
    terms.extend([item.strip() for item in query.split() if item.strip()])

    seen = set()
    unique_terms = []

    for term in terms:
        if term and term not in seen:
            seen.add(term)
            unique_terms.append(term)

    return unique_terms


def search_documents(query: str, max_results: int = 5) -> Dict[str, Any]:
    """
    Recursively search local documents by keyword matching.

    It searches all supported files under data/, including subfolders.
    """
    DATA_DIR.mkdir(exist_ok=True)

    query = query.strip()

    if not query:
        return {
            "ok": False,
            "error": "Query cannot be empty.",
        }

    terms = _query_terms(query)
    results: List[Dict[str, Any]] = []

    documents = list_documents().get("documents", [])

    for doc in documents:
        filename = doc["filename"]
        content_result = read_document(filename, max_chars=50000)

        if not content_result.get("ok"):
            continue

        text = content_result.get("content", "")
        lower_text = text.lower()

        score = 0

        for term in terms:
            count = lower_text.count(term)
            if count > 0:
                score += count

        if query.lower() in lower_text:
            score += 5

        if score <= 0:
            continue

        first_hit_positions = [
            lower_text.find(term)
            for term in terms
            if lower_text.find(term) >= 0
        ]

        first_hit = min(first_hit_positions) if first_hit_positions else 0

        start = max(0, first_hit - 300)
        end = min(len(text), first_hit + 900)
        snippet = text[start:end].strip()

        results.append(
            {
                "filename": filename,
                "name": doc.get("name", Path(filename).name),
                "category": doc.get("category", "root"),
                "type": doc.get("type", ""),
                "score": score,
                "snippet": snippet,
            }
        )

    results.sort(key=lambda item: item["score"], reverse=True)

    return {
        "ok": True,
        "source": "local_documents",
        "recursive": True,
        "query": query,
        "count": len(results[:max_results]),
        "results": results[:max_results],
    }


def _try_float(value: Any) -> Optional[float]:
    """
    Convert value to float if possible.
    """
    try:
        if value is None:
            return None

        text = str(value).strip()

        if not text:
            return None

        return float(text)

    except ValueError:
        return None


def _is_boolean_like(value: Any) -> bool:
    """
    Check whether a value looks like a boolean.
    """
    text = str(value).strip().lower()
    return text in {"true", "false", "yes", "no", "1", "0"}


def analyze_csv(filename: str) -> Dict[str, Any]:
    """
    Analyze a CSV file in the data folder.

    Supports:
    - exact relative path: csv/student_performance.csv
    - basename only: student_performance.csv

    It returns:
    - row count
    - column names
    - numeric statistics
    - categorical value counts
    - boolean counts
    - preview rows
    """
    try:
        path = _safe_path(filename)
    except (ValueError, FileNotFoundError) as exc:
        return {
            "ok": False,
            "error": str(exc),
            "filename": filename,
        }

    if not path.exists():
        return {
            "ok": False,
            "error": f"File not found: {filename}",
        }

    if path.suffix.lower() != ".csv":
        return {
            "ok": False,
            "error": "Only .csv files can be analyzed by this tool.",
            "filename": filename,
        }

    rows: List[Dict[str, str]] = []

    try:
        with path.open("r", encoding="utf-8-sig", errors="ignore", newline="") as file:
            reader = csv.DictReader(file)
            fieldnames = reader.fieldnames or []

            for row in reader:
                rows.append(dict(row))

    except Exception as exc:
        return {
            "ok": False,
            "error": f"Failed to analyze CSV: {exc}",
            "filename": filename,
        }

    numeric_stats: Dict[str, Dict[str, Any]] = {}
    categorical_stats: Dict[str, Dict[str, int]] = {}
    boolean_stats: Dict[str, Dict[str, int]] = {}

    for column in fieldnames:
        raw_values = [row.get(column, "") for row in rows]
        non_empty_values = [str(value).strip() for value in raw_values if str(value).strip()]

        numeric_values = []

        for value in non_empty_values:
            converted = _try_float(value)

            if converted is not None:
                numeric_values.append(converted)

        if numeric_values and len(numeric_values) == len(non_empty_values):
            numeric_stats[column] = {
                "count": len(numeric_values),
                "min": min(numeric_values),
                "max": max(numeric_values),
                "average": round(sum(numeric_values) / len(numeric_values), 2),
            }
            continue

        if non_empty_values and all(_is_boolean_like(value) for value in non_empty_values):
            counter = Counter(str(value).strip().lower() for value in non_empty_values)
            boolean_stats[column] = dict(counter)
            continue

        if non_empty_values:
            counter = Counter(non_empty_values)
            categorical_stats[column] = dict(counter.most_common(10))

    relative_path = _relative_display_path(path)

    return {
        "ok": True,
        "filename": relative_path,
        "name": path.name,
        "category": _get_category(path),
        "row_count": len(rows),
        "columns": fieldnames,
        "numeric_stats": numeric_stats,
        "categorical_stats": categorical_stats,
        "boolean_stats": boolean_stats,
        "preview_rows": rows[:5],
        "resolved_from": filename,
    }


def save_markdown_note(title: str, content: str) -> Dict[str, Any]:
    """
    Save a markdown note to the outputs folder.

    This remains outside data/ because outputs are generated artifacts.
    """
    OUTPUT_DIR.mkdir(exist_ok=True)

    safe_title = re.sub(r"[^a-zA-Z0-9\u4e00-\u9fff_-]+", "_", title).strip("_")

    if not safe_title:
        safe_title = "study_note"

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{safe_title}_{timestamp}.md"
    path = OUTPUT_DIR / filename

    markdown = f"# {title}\n\n{content}\n"

    path.write_text(markdown, encoding="utf-8")

    return {
        "ok": True,
        "filename": filename,
        "path": str(path),
        "size_bytes": path.stat().st_size,
    }


def web_search(query: str, max_results: int = 5) -> Dict[str, Any]:
    """
    Search the web when local documents do not contain enough information.

    This tool uses ddgs and does not require an extra search API key.
    """
    query = query.strip()

    if not query:
        return {
            "ok": False,
            "error": "Query cannot be empty.",
        }

    if DDGS is None:
        return {
            "ok": False,
            "error": "ddgs is not installed. Please run: pip install ddgs",
        }

    try:
        with DDGS() as searcher:
            raw_results = list(searcher.text(query, max_results=max_results))

        results = []

        for item in raw_results[:max_results]:
            results.append(
                {
                    "title": item.get("title", ""),
                    "url": item.get("href", item.get("url", "")),
                    "snippet": item.get("body", item.get("snippet", "")),
                }
            )

        return {
            "ok": True,
            "source": "web_search",
            "query": query,
            "count": len(results),
            "results": results,
        }

    except Exception as exc:
        return {
            "ok": False,
            "source": "web_search",
            "error": str(exc),
            "query": query,
        }


def search_local_then_web(query: str, max_results: int = 5) -> Dict[str, Any]:
    """
    First search local course materials recursively.
    If no local result is found, fall back to web search.
    """
    local_result = search_documents(query=query, max_results=max_results)

    if local_result.get("ok") and local_result.get("count", 0) > 0:
        return {
            "ok": True,
            "source_used": "local_documents",
            "query": query,
            "local_result": local_result,
            "web_result": None,
        }

    web_result = web_search(query=query, max_results=max_results)

    return {
        "ok": web_result.get("ok", False),
        "source_used": "web_search",
        "query": query,
        "local_result": local_result,
        "web_result": web_result,
    }