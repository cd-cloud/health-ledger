# Health Ledger 更新日志

> 版本格式遵循 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.1.0/)，版本号遵循 [Semantic Versioning](https://semver.org/lang/zh-CN/)。

## [Unreleased]

### Added
- 新增用户认证模块：注册、登录、登出 API 与前端页面，密码使用 bcrypt 安全存储。
- 新增基于加密 Cookie 的会话认证，受保护接口未登录时返回 401。
- 实现报告、指标值、趋势数据按用户隔离，用户 A 无法查看或操作用户 B 的数据。
- 新增 `SECRET_KEY` 环境变量用于会话 Cookie 签名。
- 新增后端单元测试覆盖认证与数据隔离场景。

### Changed
- 所有报告、指标值、趋势相关接口均需登录，并仅返回当前用户的数据。
- `README.md` 更新环境变量说明与 v0.4.0 数据库升级提示。

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
