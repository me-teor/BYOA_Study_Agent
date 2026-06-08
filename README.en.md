<p align="right">
  <a href="./README.zh-CN.md">简体中文</a> |
  <strong>English</strong>
</p>

# BYOA Study Agent

## 1. Project Overview

BYOA Study Agent is a single-purpose AI learning assistant built for Experiment 2: Bring Your Own Agent.

The project demonstrates how an AI agent can use external tools and local context instead of relying only on the base knowledge of a large language model. It can recursively scan local course materials, search documents, analyze CSV files, save Markdown study notes, and use web search as a fallback when local materials are insufficient.

---

## 2. Key Features

1. **Recursive Local Document Scanning**
   The agent scans the `data/` folder and its subfolders for supported documents.

2. **Document Reading**
   The agent can read `.txt`, `.md`, `.csv`, and `.pdf` files.

3. **Automatic Filename Resolution**
   The user or model can provide either a full relative path or only a filename. For example:

   * `csv/student_performance.csv`
   * `student_performance.csv`

4. **Local Document Search**
   The agent searches local course materials and returns relevant evidence snippets.

5. **CSV Analysis**
   The agent analyzes numeric, categorical, and boolean columns in CSV files.

6. **Markdown Note Saving**
   The agent can save generated summaries and study notes into the `outputs/` folder.

7. **Web Search Fallback**
   If no relevant local evidence is found, the agent can use web search.

8. **Rich Terminal UI**
   The project provides a colorful command-line interface using Rich.

---

## 3. Project Structure

```text
byoa-study-agent/
│
├─ README.zh-CN.md
├─ README.en.md
├─ requirements.txt
├─ .gitignore
├─ .env.example
│
├─ src/
│  ├─ app.py
│  ├─ agent.py
│  ├─ tools.py
│  └─ prompts.py
│
├─ data/
│  ├─ course/
│  ├─ security/
│  ├─ software/
│  ├─ official/
│  └─ csv/
│
├─ outputs/
│  └─ generated markdown notes
│
└─ screenshots/
   └─ execution screenshots for report
```

---

## 4. Architecture

The project uses standard LLM Function Calling.

```text
User Query
   ↓
LLM decides whether a tool is needed
   ↓
LLM emits a structured tool call
   ↓
Python executes the selected tool
   ↓
Tool result is returned to the LLM
   ↓
LLM generates the final answer
```

This design satisfies the BYOA requirements:

* Tool Use / Skills
* Context Integration
* Function Calling
* External Context
* AI-assisted development

---

## 5. Implemented Tools

| Tool Name               | Description                                                 |
| ----------------------- | ----------------------------------------------------------- |
| `list_documents`        | Recursively list local documents under `data/`              |
| `read_document`         | Read a local document by relative path or filename          |
| `search_documents`      | Search local documents for relevant snippets                |
| `analyze_csv`           | Analyze CSV files and return statistics                     |
| `save_markdown_note`    | Save generated notes as Markdown files                      |
| `web_search`            | Search the web for external information                     |
| `search_local_then_web` | Search local documents first, then use web search if needed |

---

## 6. Environment Setup

Create and activate a Conda environment:

```bash
conda create -n byoa_agent python=3.11
conda activate byoa_agent
```

Install dependencies:

```bash
pip install -r requirements.txt
```

---

## 7. API Configuration

Create a `.env` file in the project root:

```env
OPENAI_API_KEY=your_api_key_here
OPENAI_BASE_URL=your_openai_compatible_base_url
OPENAI_MODEL=your_model_name
```

Example:

```env
OPENAI_API_KEY=your_api_key_here
OPENAI_BASE_URL=https://open.bigmodel.cn/api/paas/v4
OPENAI_MODEL=glm-4-flash-250414
```

Do not commit `.env` to GitHub.

---

## 8. Run the Project

Run:

```bash
python src/app.py
```

Available terminal commands:

```text
/docs       Show local document library
/tools      Show available agent tools
/outputs    Show generated Markdown notes
/status     Show system status
/help       Show help menu
/clear      Redraw home screen
/exit       Exit the program
```

---

## 9. Example Queries

### 9.1 Local Document Search

```text
根据本地资料，解释 SAST、DAST 和 SCA 的区别。
```

Expected behavior:

* Calls `search_documents`
* Finds evidence from `security/ai_security_testing_note.md`
* Generates an answer based on local evidence

### 9.2 Summarize MCP and Save a Note

```text
请根据本地资料总结 MCP 的核心组件，并保存成 markdown 复习笔记。
```

Expected behavior:

* Calls `search_documents`
* Calls `save_markdown_note`
* Saves a Markdown file into `outputs/`

### 9.3 CSV Analysis

```text
请分析 student_performance.csv 中的成绩数据。
```

Expected behavior:

* Resolves `student_performance.csv` to `csv/student_performance.csv`
* Calls `analyze_csv`
* Returns numeric, categorical, and boolean statistics

### 9.4 Local-First Web Fallback

```text
请解释 Python 3.12 的主要新特性，并保存成 markdown 复习笔记。
```

Expected behavior:

* Searches local materials first
* Falls back to web search if local evidence is insufficient
* Optionally saves the result as a Markdown note

---

## 10. Suggested Screenshots for Report

1. Home status screen.
2. Tool list screen.
3. Local document search and answer.
4. Markdown note saving result.

---

## 11. Security Notes

Before submission, make sure that the repository does not include:

* `.env`
* API keys
* virtual environments
* cache folders
* private files
* large temporary files

---

## 12. AI-Assisted Development Reflection

Large language models were used to help scaffold the project structure, design function calling schemas, implement local tools, improve the orchestration loop, build the Rich terminal UI, and write documentation.

One technical challenge was that the model sometimes stopped after only one tool call and failed to complete multi-step tasks such as searching local materials and saving a Markdown note. This was solved by implementing a multi-round tool calling loop and adding a fallback auto-save mechanism. Another issue was that the model sometimes passed only a filename instead of a full relative path. This was solved by adding recursive filename resolution in `read_document()` and `analyze_csv()`.

## License

This project is licensed under the MIT License. See [LICENSE](./LICENSE) for details.