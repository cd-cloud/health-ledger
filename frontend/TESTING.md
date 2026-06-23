# 前端测试指南

## 测试栈

- **单元/组件测试**：Vitest + React Testing Library + jsdom
- **端到端/视觉验证**：Playwright

## 命令

```bash
# 运行组件测试
npm test

# 运行端到端视觉测试
npm run test:e2e

# 本地开发
npm run dev
```

## 组件测试覆盖

| 组件/页面 | 覆盖点 |
|-----------|--------|
| `LoadingSpinner` | 默认/自定义文案、图标渲染 |
| `EmptyState` | 默认/自定义文案、操作区渲染 |
| `ErrorState` | 默认/字符串/Error 对象错误、重试按钮 |
| `BiomarkerList` | 加载、错误、空状态、列表渲染、状态筛选、CSV 导出、异常页过滤 |
| `ReportDetail` | 加载、错误、报告渲染、单选/全选、批量校对、撤销、重新解析 |

## 视觉验证

使用 Playwright 对以下关键页面进行真实 Chromium 渲染并截图：

1. **Dashboard** (`/`) — 概览卡片、最近报告、异常指标
2. **BiomarkerTrend** (`/biomarkers/GLU/trend`) — 趋势图、参考范围线、异常点颜色、AI 分析区
3. **ReportDetail** (`/reports/1`) — 报告信息、批量操作控件、指标表格

截图保存在 `e2e/screenshots/`：

- `dashboard.png`
- `biomarker-trend.png`
- `report-detail.png`

## 最近一次测试结果

- 组件测试：24 passed
- 端到端视觉测试：3 passed
- 生产构建：`npm run build` 通过
