import { test, expect } from '@playwright/test'

const reports = [
  {
    id: 1,
    filename: 'report.pdf',
    original_name: '2024 年度体检报告',
    stored_path: '/tmp/report.pdf',
    report_date: '2024-06-01T00:00:00',
    status: 'parsed',
    error_message: null,
    created_at: '2024-06-01T00:00:00',
    updated_at: '2024-06-01T00:00:00',
  },
]

const biomarkers = [
  {
    id: 1,
    code: 'GLU',
    name: '血糖',
    unit_standard: 'mmol/L',
    category: '生化',
    reference_low: 3.9,
    reference_high: 6.1,
    direction: null,
    description: null,
  },
  {
    id: 2,
    code: 'WBC',
    name: '白细胞',
    unit_standard: '10^9/L',
    category: '血常规',
    reference_low: 4,
    reference_high: 10,
    direction: null,
    description: null,
  },
]

const abnormalValues = [
  {
    id: 101,
    report_id: 1,
    biomarker_id: 1,
    biomarker: biomarkers[0],
    report: reports[0],
    original_name: '血糖',
    original_value_text: '7.2',
    original_unit: 'mmol/L',
    value: 7.2,
    unit: 'mmol/L',
    reference_low: 3.9,
    reference_high: 6.1,
    status: 'high',
    is_reviewed: true,
    reviewed_at: '2024-06-01T00:00:00',
    created_at: '2024-06-01T00:00:00',
  },
]

const allValues = [
  abnormalValues[0],
  {
    id: 102,
    report_id: 1,
    biomarker_id: 2,
    biomarker: biomarkers[1],
    report: reports[0],
    original_name: '白细胞',
    original_value_text: '5.5',
    original_unit: '10^9/L',
    value: 5.5,
    unit: '10^9/L',
    reference_low: 4,
    reference_high: 10,
    status: 'normal',
    is_reviewed: true,
    reviewed_at: '2024-06-01T00:00:00',
    created_at: '2024-06-01T00:00:00',
  },
]

const reportDetail = {
  ...reports[0],
  values: [
    {
      id: 101,
      report_id: 1,
      biomarker_id: 1,
      biomarker: biomarkers[0],
      original_name: '血糖',
      original_value_text: '7.2',
      original_unit: 'mmol/L',
      value: 7.2,
      unit: 'mmol/L',
      reference_low: 3.9,
      reference_high: 6.1,
      status: 'high',
      is_reviewed: false,
      reviewed_at: null,
      created_at: '2024-06-01T00:00:00',
    },
    {
      id: 102,
      report_id: 1,
      biomarker_id: 2,
      biomarker: biomarkers[1],
      original_name: '白细胞',
      original_value_text: '5.5',
      original_unit: '10^9/L',
      value: 5.5,
      unit: '10^9/L',
      reference_low: 4,
      reference_high: 10,
      status: 'normal',
      is_reviewed: false,
      reviewed_at: null,
      created_at: '2024-06-01T00:00:00',
    },
  ],
}

const trendData = {
  biomarker: biomarkers[0],
  points: [
    {
      report_id: 1,
      report_date: '2024-01-15T00:00:00',
      value: 5.8,
      unit: 'mmol/L',
      status: 'normal',
      is_reviewed: true,
    },
    {
      report_id: 2,
      report_date: '2024-06-01T00:00:00',
      value: 7.2,
      unit: 'mmol/L',
      status: 'high',
      is_reviewed: true,
    },
    {
      report_id: 3,
      report_date: '2024-11-20T00:00:00',
      value: 6.5,
      unit: 'mmol/L',
      status: 'high',
      is_reviewed: true,
    },
  ],
}

test.beforeEach(async ({ page }) => {
  await page.route('/api/reports', async (route) => {
    await route.fulfill({ json: { items: reports, total: reports.length } })
  })

  await page.route('/api/reports/1', async (route) => {
    await route.fulfill({ json: reportDetail })
  })

  await page.route('/api/biomarkers', async (route) => {
    await route.fulfill({ json: biomarkers })
  })

  await page.route('/api/biomarkers/values*', async (route) => {
    const url = new URL(route.request().url())
    const abnormalOnly = url.searchParams.get('abnormal_only') === 'true'
    await route.fulfill({ json: abnormalOnly ? abnormalValues : allValues })
  })

  await page.route('/api/biomarkers/summary/abnormal', async (route) => {
    await route.fulfill({ json: abnormalValues })
  })

  await page.route('/api/trends/GLU', async (route) => {
    await route.fulfill({ json: trendData })
  })

  await page.route('/api/trends/GLU/analyze', async (route) => {
    await route.fulfill({
      json: {
        biomarker_code: 'GLU',
        biomarker_name: '血糖',
        analysis: '血糖呈波动上升趋势，建议关注饮食结构并定期复查。',
        disclaimer: '本分析仅供参考，不构成医疗建议。',
      },
    })
  })
})

test('Dashboard renders key cards and latest reports', async ({ page }) => {
  await page.goto('/')
  await expect(page.getByRole('heading', { name: '概览', level: 2 })).toBeVisible()
  await expect(page.getByText('报告总数')).toBeVisible()
  await expect(page.getByText('2024 年度体检报告')).toBeVisible()

  await page.screenshot({ path: 'e2e/screenshots/dashboard.png', fullPage: true })
})

test('BiomarkerTrend renders chart with reference range and abnormal dots', async ({ page }) => {
  await page.goto('/biomarkers/GLU/trend')
  await expect(page.getByText('血糖 趋势')).toBeVisible()
  await expect(page.locator('.recharts-surface')).toBeVisible()
  await expect(page.getByText('上限')).toBeVisible()
  await expect(page.getByText('下限')).toBeVisible()
  await expect(page.getByText('AI 趋势分析')).toBeVisible()

  await page.screenshot({ path: 'e2e/screenshots/biomarker-trend.png', fullPage: true })
})

test('ReportDetail renders batch operation controls', async ({ page }) => {
  await page.goto('/reports/1')
  await expect(page.getByText('2024 年度体检报告')).toBeVisible()
  await expect(page.getByRole('button', { name: '批量校对' })).toBeVisible()
  await expect(page.getByRole('button', { name: '批量取消' })).toBeVisible()
  await expect(page.getByText('血糖')).toBeVisible()

  await page.screenshot({ path: 'e2e/screenshots/report-detail.png', fullPage: true })
})
