# Health Ledger 更新日志

> 版本格式遵循 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.1.0/)，版本号遵循 [Semantic Versioning](https://semver.org/lang/zh-CN/)。

## [Unreleased]

### Added
- 新增后端单元测试套件，覆盖 `normalizer`、`report_parser`、`routers` 三个核心模块，共 40 个用例。
- `README.md` 增加 API 文档导出说明与测试运行指南。

### Changed
- 后端依赖注入测试中统一使用内存 SQLite + 事务回滚，避免污染真实数据库。

## [0.3.0] - 2026-06-15

### Added
- 指标值批量校对/撤销：新增 `PATCH /biomarkers/values/batch` 接口。
- 趋势图增强：增加参考范围线、异常点高亮。
- 指标值导出：支持 `GET /biomarkers/values/export?format=csv|json`。
- 统一空状态与错误提示组件，提升前端一致性。

### Changed
- 优化异常处理与错误提示文案。

## [0.2.0] - 2026-06-12

### Added
- 指标字典扩展至 31 项常见生化指标，覆盖血常规、肝功能、肾功能、血脂、血糖等。
- 报告解析 OCR 兜底：支持 PaddleOCR/Tesseract 识别扫描件 PDF。
- 完善 `README.md`：新增环境变量、OCR 安装与启动说明。
- 增强解析异常处理，提升非标准报告容错能力。

### Changed
- 优化日期提取逻辑，支持更多中文日期格式。

## [0.1.0] - 2026-06-10

### Added
- 初始化 Health Ledger 项目。
- 后端：FastAPI + SQLAlchemy + SQLite，完成报告上传、指标存储、趋势查询。
- 前端：React + TypeScript + Vite + Tailwind + Recharts，完成报告上传、指标列表、趋势图。
- 支持基础单位换算、英文别名匹配、报告日期入库。

