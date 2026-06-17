import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter, Routes, Route } from 'react-router-dom'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import ReportDetail from '../ReportDetail'
import * as reportsApi from '../../api/reports'
import * as biomarkersApi from '../../api/biomarkers'
import type { ReportDetail as ReportDetailType, BiomarkerValue } from '../../types'

vi.mock('../../api/reports', () => ({
  getReport: vi.fn(),
  parseReport: vi.fn(),
}))

vi.mock('../../api/biomarkers', () => ({
  updateBiomarkerValue: vi.fn(),
  batchUpdateBiomarkerValues: vi.fn(),
}))

const mockedGetReport = vi.mocked(reportsApi.getReport)
const mockedParseReport = vi.mocked(reportsApi.parseReport)
const mockedBatchUpdate = vi.mocked(biomarkersApi.batchUpdateBiomarkerValues)

const mockReport: ReportDetailType = {
  id: 1,
  filename: 'report.pdf',
  original_name: '2024 年度体检报告',
  stored_path: '/tmp/report.pdf',
  report_date: '2024-06-01T00:00:00',
  status: 'parsed',
  error_message: null,
  created_at: '2024-06-01T00:00:00',
  updated_at: '2024-06-01T00:00:00',
  values: [
    {
      id: 101,
      report_id: 1,
      biomarker_id: 1,
      biomarker: {
        id: 1,
        code: 'GLU',
        name: '血糖',
        unit_standard: 'mmol/L',
        category: null,
        reference_low: 3.9,
        reference_high: 6.1,
        direction: null,
        description: null,
      },
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
    } as BiomarkerValue,
    {
      id: 102,
      report_id: 1,
      biomarker_id: 2,
      biomarker: {
        id: 2,
        code: 'WBC',
        name: '白细胞',
        unit_standard: '10^9/L',
        category: null,
        reference_low: 4,
        reference_high: 10,
        direction: null,
        description: null,
      },
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
    } as BiomarkerValue,
  ],
}

function renderWithRouter() {
  return render(
    <MemoryRouter initialEntries={['/reports/1']}>
      <Routes>
        <Route path="/reports/:id" element={<ReportDetail />} />
      </Routes>
    </MemoryRouter>
  )
}

describe('ReportDetail', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders loading state', () => {
    mockedGetReport.mockImplementation(() => new Promise(() => {}))
    renderWithRouter()
    expect(screen.getByText('加载报告详情...')).toBeInTheDocument()
  })

  it('renders error state when report fails to load', async () => {
    mockedGetReport.mockRejectedValue(new Error('报告不存在'))
    renderWithRouter()

    await waitFor(() => {
      expect(screen.getByText('报告详情加载失败')).toBeInTheDocument()
    })
    expect(screen.getByText('报告不存在')).toBeInTheDocument()
  })

  it('renders report header and values', async () => {
    mockedGetReport.mockResolvedValue(mockReport)
    renderWithRouter()

    await waitFor(() => {
      expect(screen.getByText('2024 年度体检报告')).toBeInTheDocument()
    })

    expect(screen.getByText('血糖')).toBeInTheDocument()
    expect(screen.getByText('白细胞')).toBeInTheDocument()
    expect(screen.getAllByRole('checkbox').length).toBeGreaterThan(1)
  })

  it('toggles individual selection', async () => {
    mockedGetReport.mockResolvedValue(mockReport)
    renderWithRouter()

    await waitFor(() => {
      expect(screen.getByText('血糖')).toBeInTheDocument()
    })

    const checkboxes = screen.getAllByRole('checkbox')
    const firstRowCheckbox = checkboxes[1]

    await userEvent.click(firstRowCheckbox)
    expect(firstRowCheckbox).toBeChecked()

    await userEvent.click(firstRowCheckbox)
    expect(firstRowCheckbox).not.toBeChecked()
  })

  it('toggles select all', async () => {
    mockedGetReport.mockResolvedValue(mockReport)
    renderWithRouter()

    await waitFor(() => {
      expect(screen.getByText('血糖')).toBeInTheDocument()
    })

    const selectAllButton = screen.getByRole('button', { name: '全选' })
    await userEvent.click(selectAllButton)

    const checkboxes = screen.getAllByRole('checkbox')
    expect(checkboxes.slice(1).every((cb) => (cb as HTMLInputElement).checked)).toBe(true)

    const batchReviewButton = screen.getByRole('button', { name: '批量校对' })
    expect(batchReviewButton).not.toBeDisabled()
  })

  it('executes batch review and supports undo', async () => {
    mockedGetReport.mockResolvedValueOnce(mockReport).mockResolvedValueOnce({
      ...mockReport,
      values: mockReport.values.map((v) => ({ ...v, is_reviewed: true })),
    })
    mockedBatchUpdate.mockResolvedValue([])

    renderWithRouter()

    await waitFor(() => {
      expect(screen.getByText('血糖')).toBeInTheDocument()
    })

    const selectAllButton = screen.getByRole('button', { name: '全选' })
    await userEvent.click(selectAllButton)

    const batchReviewButton = screen.getByRole('button', { name: '批量校对' })
    await userEvent.click(batchReviewButton)

    await waitFor(() => {
      expect(mockedBatchUpdate).toHaveBeenCalledWith([
        { id: 101, is_reviewed: true },
        { id: 102, is_reviewed: true },
      ])
    })

    const undoButton = screen.getByRole('button', { name: /撤销/i })
    expect(undoButton).toBeInTheDocument()
    expect(undoButton).not.toBeDisabled()

    await userEvent.click(undoButton)
    await waitFor(() => {
      expect(mockedBatchUpdate).toHaveBeenLastCalledWith([
        { id: 101, is_reviewed: false },
        { id: 102, is_reviewed: false },
      ])
    })
  })

  it('triggers re-parse when clicking reparse button', async () => {
    mockedGetReport.mockResolvedValue({ ...mockReport, status: 'pending' })
    mockedParseReport.mockResolvedValue({ report_id: 1, status: 'parsed', extracted_count: 2 })

    renderWithRouter()

    await waitFor(() => {
      expect(screen.getByText('2024 年度体检报告')).toBeInTheDocument()
    })

    const reparseButton = screen.getByRole('button', { name: '重新解析' })
    await userEvent.click(reparseButton)

    await waitFor(() => {
      expect(mockedParseReport).toHaveBeenCalledWith(1)
    })
  })
})
