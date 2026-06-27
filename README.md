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
- OCR 兜底（可选）：PaddleOCR / Tesseract
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

## 快速开始

```bash
# 克隆默认主分支（main），确保获取最新代码
git clone -b main https://github.com/cd-cloud/health-ledger.git
cd health-ledger
```

## 环境准备

需要 Python 3.10+ 和 Node.js 18+。

### 环境变量

后端通过环境变量（`.env` 文件或启动前 `export`）进行配置。推荐在项目根目录创建 `.env`：

```bash
# Kimi / Moonshot AI（用于指标提取与趋势分析）
KIMI_API_KEY=your_kimi_api_key
KIMI_BASE_URL=https://api.moonshot.cn/v1
KIMI_MODEL=moonshot-v1-8k

# 可选：切换 LLM 提供商，当前仅支持 kimi
# LLM_PROVIDER=kimi

# 可选：自定义数据库路径
# DATABASE_URL=sqlite:///data/healthtracker.db

# 必填：用于加密登录会话 Cookie（生产环境务必修改）
SECRET_KEY=your-secret-key
```

| 变量名 | 说明 | 默认值 |
|---|---|---|
| `KIMI_API_KEY` | Kimi / Moonshot API Key。未配置时将使用规则化 fallback 提取并生成本地趋势描述。 | 空字符串 |
| `KIMI_BASE_URL` | Kimi API 基础地址 | `https://api.moonshot.cn/v1` |
| `KIMI_MODEL` | 使用的模型名称 | `moonshot-v1-8k` |
| `LLM_PROVIDER` | LLM 提供商，当前仅支持 `kimi` | `kimi` |
| `DATABASE_URL` | SQLite 数据库 URL | `sqlite:///data/healthtracker.db` |
| `SECRET_KEY` | 会话 Cookie 签名密钥 | `change-me-in-production` |

**注意**：数据库结构变更由 Alembic 迁移脚本管理，禁止通过删除数据库文件来升级。首次启动或拉取新代码后，后端启动时会自动执行迁移；也可手动运行：

```bash
cd backend
alembic upgrade head
```

如需生成新的迁移脚本（模型变更后）：

```bash
alembic revision --autogenerate -m "描述变更"
```

#### 已存在旧数据库的 baseline 处理

如果你此前通过 `Base.metadata.create_all()` 创建过数据库（v0.4.0 之前），且数据库中尚无 `alembic_version` 表，直接运行 `alembic upgrade head` 会因表已存在而失败。请先备份数据，然后执行 baseline 标记：

```bash
cd backend
alembic stamp head
alembic upgrade head
```

`alembic stamp head` 会将当前数据库结构标记为已处于最新迁移版本，后续模型变更即可正常通过 `alembic upgrade head` 升级。

### OCR 扫描件支持（可选）

对于扫描件或图片型 PDF，系统支持 OCR 文本兜底。需要额外安装依赖及系统工具：

1. 安装系统依赖：
   - **Windows**：安装 [poppler for Windows](https://github.com/oschwartz10612/poppler-windows/releases) 并将 `bin` 目录加入系统 PATH。
   - **Linux (Debian/Ubuntu)**：`sudo apt-get install poppler-utils tesseract-ocr tesseract-ocr-chi-sim`
   - **macOS**：`brew install poppler tesseract tesseract-lang`

2. 安装 Python OCR 依赖（取消 `backend/requirements.txt` 中对应行的注释后执行）：

   ```bash
   cd backend
   pip install pdf2image==1.17.0 paddleocr==2.9.1 pytesseract==0.3.13 Pillow==11.0.0
   ```

   - 中文报告推荐使用 **PaddleOCR**，识别效果较好但安装包较大。
   - 轻量场景可使用 **Tesseract** 作为回退。

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

### API 文档导出

FastAPI 原生提供交互式 API 文档：

- Swagger UI：`http://127.0.0.1:8000/docs`
- ReDoc：`http://127.0.0.1:8000/redoc`
- OpenAPI JSON：`http://127.0.0.1:8000/openapi.json`

如需导出静态 OpenAPI JSON 文件，可在后端启动后执行：

```bash
curl http://127.0.0.1:8000/openapi.json > docs/openapi.json
```

### 运行测试

#### 后端单元测试

```bash
cd backend
pytest tests/ -v
```

当前覆盖：
- `normalizer`：指标匹配、单位换算、状态判定、字典一致性。
- `report_parser`：报告解析、日期提取、错误状态、LLM 与 fallback 路径。
- `routers`：健康检查、指标 CURD、批量更新、导出、报告上传/解析/删除、趋势查询。

#### 前端构建检查

```bash
cd frontend
npm install
npm run build
```

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

## 异常处理说明

- 上传非 PDF 文件：前端/后端均会提示「仅支持 PDF 文件」。
- 上传空文件：后端会校验文件大小并返回错误。
- PDF 文本为空：可能是扫描件，系统会尝试 OCR 兜底（需安装依赖）；未安装 OCR 时返回明确提示。
- 解析失败：报告状态标记为 `error`，可在报告列表查看错误信息。
- LLM 调用失败：自动回退到规则化提取，并记录日志；不会阻断报告解析。

## 注意事项

- 所有 AI 输出均附带医疗免责声明，不构成诊断。
- 原始 PDF 文件会保留在 `uploads/` 目录。
- 未校对的指标值不会进入趋势分析。
- 指标名称通过 `docs/biomarker_dictionary.example.json` 标准化。
