<p align="right">
  <strong>简体中文</strong> |
  <a href="./README.en.md">English</a>
</p>

# BYOA Study Agent

## 1. 项目简介

BYOA Study Agent 是一个面向课程学习场景的单用途 AI Agent 项目，用于完成 Experiment 2: Bring Your Own Agent。

本项目的核心目标是构建一个能够调用外部工具、读取本地资料、分析结构化数据，并在本地资料不足时使用网络搜索兜底的课程学习助手。Agent 不只依赖大语言模型自身知识，而是通过标准 LLM Function Calling 调用本地工具和外部检索工具，从而完成更可靠、更可解释的问答、资料检索、CSV 分析和学习笔记生成任务。

---

## 2. 核心功能

本项目实现了以下功能：

1. **本地资料递归扫描**
   自动扫描 `data/` 文件夹及其子文件夹中的 `.txt`、`.md`、`.csv`、`.pdf` 文件。

2. **本地资料读取**
   支持通过完整相对路径或单独文件名读取资料。例如：

   * `course/mcp_note.md`
   * `mcp_note.md`

3. **本地资料检索**
   根据用户问题检索本地课程资料，并返回相关片段作为回答依据。

4. **CSV 数据分析**
   支持分析 CSV 文件中的数值字段、分类字段和布尔字段，返回统计结果。

5. **Markdown 学习笔记保存**
   Agent 可以将总结结果保存为 Markdown 文件到 `outputs/` 文件夹。

6. **网络搜索兜底**
   当本地资料中没有相关内容时，Agent 可以通过网络搜索工具补充信息。

7. **Rich 命令行 UI**
   使用 Rich 构建彩色终端界面，支持快速命令、工具调用轨迹展示、本地证据展示、网络搜索结果展示和保存文件展示。

---

## 3. 项目结构

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
│  │  ├─ experiment2_requirements.md
│  │  ├─ ai_prompting_note.md
│  │  ├─ tool_calling_note.md
│  │  ├─ rag_note.md
│  │  ├─ mcp_note.md
│  │  ├─ ai_ide_note.md
│  │  └─ ai_agent_workflow_note.md
│  │
│  ├─ security/
│  │  ├─ ai_security_testing_note.md
│  │  ├─ prompt_injection_note.md
│  │  └─ owasp_security_note.md
│  │
│  ├─ software/
│  │  ├─ ai_code_review_note.md
│  │  ├─ ai_devops_note.md
│  │  ├─ software_testing_note.md
│  │  ├─ git_workflow_note.md
│  │  ├─ code_quality_note.md
│  │  ├─ agent_observability_note.md
│  │  ├─ ai_dev_note.txt
│  │  └─ database_note.txt
│  │
│  ├─ official/
│  │  └─ python_312_note.md
│  │
│  └─ csv/
│     ├─ study_scores.csv
│     ├─ student_performance.csv
│     ├─ programming_tasks.csv
│     ├─ ai_tools_comparison.csv
│     └─ security_test_results.csv
│
├─ outputs/
│  └─ generated markdown notes
│
└─ screenshots/
   └─ execution screenshots for report
```

---

## 4. 技术架构

本项目采用标准 LLM Function Calling 架构。

基本流程如下：

```text
用户输入
   ↓
LLM 判断是否需要调用工具
   ↓
生成结构化 tool call
   ↓
Python 执行本地工具或网络搜索工具
   ↓
工具结果返回给 LLM
   ↓
LLM 基于工具结果生成最终回答
```

该流程体现了 BYOA 实验要求中的：

* Tool Use / Skills
* Context Integration
* Function Calling
* External Context
* Vibe Coding

---

## 5. 工具列表

| 工具名称                    | 功能说明                         |
| ----------------------- | ---------------------------- |
| `list_documents`        | 递归列出 `data/` 文件夹中的本地资料       |
| `read_document`         | 读取指定本地资料文件，支持按文件名自动查找        |
| `search_documents`      | 在本地资料中检索相关内容                 |
| `analyze_csv`           | 分析 CSV 文件的数值字段、分类字段和布尔字段     |
| `save_markdown_note`    | 将 Agent 生成的内容保存为 Markdown 文件 |
| `web_search`            | 使用网络搜索补充外部信息                 |
| `search_local_then_web` | 先检索本地资料，若无结果再进行网络搜索          |

---

## 6. 环境配置

推荐使用 Conda 创建独立环境：

```bash
conda create -n byoa_agent python=3.11
conda activate byoa_agent
```

安装依赖：

```bash
pip install -r requirements.txt
```

---

## 7. API 配置

在项目根目录创建 `.env` 文件：

```env
OPENAI_API_KEY=your_api_key_here
OPENAI_BASE_URL=your_openai_compatible_base_url
OPENAI_MODEL=your_model_name
```

示例：

```env
OPENAI_API_KEY=your_api_key_here
OPENAI_BASE_URL=https://open.bigmodel.cn/api/paas/v4
OPENAI_MODEL=glm-4-flash-250414
```

注意：

* `.env` 文件包含 API Key，不能上传到 GitHub。
* 建议仓库中只保留 `.env.example`。
* 如果切换模型服务，只需要修改 `.env`，通常不需要修改源代码。

---

## 8. 运行方式

在项目根目录执行：

```bash
python src/app.py
```

启动后可以使用终端 UI 中的快速命令：

```text
/docs       查看本地资料库
/tools      查看 Agent 工具技能
/outputs    查看已生成笔记
/status     刷新运行状态
/help       查看帮助命令
/clear      重绘首页界面
/exit       退出程序
```

---

## 9. 推荐测试问题

### 9.1 本地资料检索

```text
根据本地资料，解释 SAST、DAST 和 SCA 的区别。
```

预期效果：

* 调用 `search_documents`
* 命中 `security/ai_security_testing_note.md`
* 基于本地资料生成回答

### 9.2 MCP 总结并保存笔记

```text
请根据本地资料总结 MCP 的核心组件，并保存成 markdown 复习笔记。
```

预期效果：

* 调用 `search_documents`
* 调用 `save_markdown_note`
* 在 `outputs/` 中生成 Markdown 文件

### 9.3 CSV 数据分析

```text
请分析 student_performance.csv 中的成绩数据。
```

预期效果：

* 自动找到 `csv/student_performance.csv`
* 调用 `analyze_csv`
* 返回数值统计、分类统计和预览行

### 9.4 本地优先 + 网络兜底

```text
请解释 Python 3.12 的主要新特性，并保存成 markdown 复习笔记。
```

预期效果：

* 优先检索本地资料
* 如果本地资料不足，调用 `search_local_then_web`
* 可继续调用 `save_markdown_note`

---

## 10. 实验截图建议

实验报告中建议放置以下 3～4 张截图：

1. 首页状态界面：显示模型、资料数量、工具数量、输出目录。
2. `/tools` 工具列表：展示 Agent 具有多个工具技能。
3. 本地检索问答：展示 `search_documents` 和本地证据来源。
4. Markdown 保存结果：展示 `save_markdown_note` 和保存路径。

---

## 11. 安全说明

提交代码仓库前请确认：

* 不提交 `.env`
* 不提交 API Key
* 不提交虚拟环境文件夹
* 不提交 `__pycache__`
* 不提交过大的临时文件
* 不公开包含隐私或未授权课程资料的文件

---

## 12. AI 辅助开发说明

本项目在开发过程中使用大语言模型辅助完成了项目结构设计、Function Calling 调度逻辑、工具 schema 编写、递归文件扫描、CSV 分析、Rich 命令行 UI 设计以及 README 文档编写。

开发过程中遇到的主要问题包括：模型有时只调用一次工具，无法完成“检索资料并保存笔记”的多步骤任务；部分工具参数中只传入文件名而不是完整相对路径。针对这些问题，项目通过多轮 tool calling loop、自动保存兜底逻辑，以及按文件名递归查找文件的方式进行了修正。

## 许可证

本项目采用 MIT License 开源许可证。详情请查看 [LICENSE](./LICENSE)。