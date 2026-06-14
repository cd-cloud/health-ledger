# 个人体检指标追踪 MVP

本地单用户体检报告管理与指标趋势分析系统。

## 功能

- PDF 体检报告上传与本地归档
- PDF 文本提取 + AI 结构化指标提取
- 指标名称标准化（基于 `docs/biomarker_dictionary.example.json`）
- 人工校对提取结果
- 指标列表与异常筛选
- 单指标趋势图（Recharts）
- AI 趋势分析摘要（默认 Kimi / Moonshot，可扩展）
- 医疗免责声明

## 技术栈

- 前端：React + TypeScript + Vite + Tailwind CSS + Recharts
- 后端：FastAPI + SQLAlchemy + SQLite
- PDF 提取：pdfplumber / pypdf
- AI：LLMProvider 抽象 + Kimi 默认实现

## 目录结构

```
.
├── backend/           # FastAPI 后端
├── frontend/          # React 前端
├── data/              # SQLite 数据库
├── uploads/           # 原始 PDF 归档
└── docs/              # 架构文档与示例数据
```

## 环境准备

需要 Python 3.10+ 和 Node.js 18+。

后端可选配置环境变量（`.env` 或在启动前 export）：

```bash
KIMI_API_KEY=your_kimi_api_key
KIMI_BASE_URL=https://api.moonshot.cn/v1
KIMI_MODEL=moonshot-v1-8k
```

未配置 `KIMI_API_KEY` 时，系统将使用规则化 fallback 提取并生成本地趋势描述。

## 启动命令

### 1. 启动后端

```bash
cd backend
python -m venv .venv
# Windows
.\.venv\Scripts\activate
# macOS/Linux
source .venv/bin/activate

pip install -r requirements.txt
python run.py
```

后端默认运行在 `http://127.0.0.1:8000`，API 文档见 `http://127.0.0.1:8000/docs`。

### 2. 启动前端

```bash
cd frontend
npm install
npm run dev
```

前端默认运行在 `http://127.0.0.1:5173`，并通过 Vite 代理将 `/api` 请求转发到后端。

## 使用流程

1. 打开前端 `http://127.0.0.1:5173`。
2. 在「上传报告」页选择 PDF 体检报告并上传。
3. 系统自动提取文本并解析指标。
4. 进入「报告列表」-> 报告详情，人工校对指标数值和状态。
5. 校对完成后，指标数据进入趋势分析。
6. 在「指标列表」或「异常指标」页查看数据，点击「趋势」查看趋势图与 AI 分析。

## 注意事项

- 所有 AI 输出均附带医疗免责声明，不构成诊断。
- 原始 PDF 文件会保留在 `uploads/` 目录。
- 未校对的指标值不会进入趋势分析。
- 指标名称通过 `docs/biomarker_dictionary.example.json` 标准化。
