# 个人体检指标追踪 MVP 架构设计

## 目标
本地单用户体检报告管理与指标趋势分析系统。

## 技术栈

- 前端：React + TypeScript + Vite + Recharts + Tailwind CSS
- 后端：FastAPI + SQLAlchemy + SQLite
- PDF 文本提取：pypdf / pdfplumber
- AI：LLMProvider 抽象，默认 Kimi（Moonshot）实现

## 目录结构

```
.
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI 应用入口
│   │   ├── database.py          # SQLAlchemy engine / session
│   │   ├── models.py            # 数据库模型
│   │   ├── schemas.py           # Pydantic 模型
│   │   ├── config.py            # 配置
│   │   ├── routers/
│   │   │   ├── reports.py       # 报告上传、列表、详情、归档
│   │   │   ├── biomarkers.py    # 指标列表、异常筛选、校对
│   │   │   └── trends.py        # 单指标趋势、AI 分析
│   │   └── services/
│   │       ├── pdf_extractor.py # PDF 文本提取
│   │       ├── llm_provider.py  # LLMProvider 抽象
│   │       ├── kimi_provider.py # Kimi 默认实现
│   │       ├── normalizer.py    # 指标标准化与状态判定
│   │       └── report_parser.py # 报告解析流程编排
│   ├── requirements.txt
│   └── run.py
├── frontend/
│   ├── src/
│   │   ├── main.tsx
│   │   ├── App.tsx
│   │   ├── api/client.ts
│   │   ├── types.ts
│   │   ├── pages/
│   │   │   ├── Dashboard.tsx
│   │   │   ├── UploadReport.tsx
│   │   │   ├── ReportList.tsx
│   │   │   ├── ReportDetail.tsx
│   │   │   ├── BiomarkerList.tsx
│   │   │   └── BiomarkerTrend.tsx
│   │   └── components/...
│   ├── package.json
│   ├── vite.config.ts
│   ├── tsconfig.json
│   ├── tailwind.config.js
│   └── index.html
├── data/                        # SQLite 数据库
├── uploads/                     # 原始 PDF 归档
├── docs/
│   ├── architecture.md
│   ├── biomarker_dictionary.example.json
│   └── report_parsing_example.json
└── README.md
```

## 数据库模型

- `Report`：报告元数据（文件名、原始路径、报告日期、创建时间、解析状态、错误信息）
- `Biomarker`：标准化指标定义（字典）
- `BiomarkerValue`：某次报告中的指标原始值、标准化值、单位、状态、是否已校对

## 核心流程

1. 用户上传 PDF -> 保存到 `uploads/` -> 创建 `Report` 记录（状态 `pending`）
2. PDF 文本提取 -> 调用 LLM 结构化提取指标 -> 标准化指标名称与单位
3. 保存 `BiomarkerValue`（`is_reviewed=false`）
4. 用户在报告详情页人工校对 -> 更新 `is_reviewed=true`
5. 趋势分析仅使用 `is_reviewed=true` 的值
6. AI 输出任何健康解读都附加医疗免责声明
