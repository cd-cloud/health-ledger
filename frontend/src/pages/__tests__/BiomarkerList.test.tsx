import { render, screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter, Routes, Route } from 'react-router-dom'
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import BiomarkerList from '../BiomarkerList'
import * as biomarkersApi from '../../api/biomarkers'
import type { BiomarkerValue } from '../../types'

vi.mock('../../api/biomarkers', () => ({
  listBiomarkerValues: vi.fn(),
  exportBiomarkerValues: vi.fn(),
}))

const mockedListBiomarkerValues = vi.mocked(biomarkersApi.listBiomarkerValues)
const mockedExportBiomarkerValues = vi.mocked(biomarkersApi.exportBiomarkerValues)

const mockValues: BiomarkerValue[] = [
  {
    id: 1,
    report_id: 10,
    biomarker_id: 100,
    biomarker: {
      id: 100,
      code: 'GLU',
      name: '血糖',
      unit_standard: 'mmol/L',
      category: null,
      reference_low: 3.9,
      reference_high: 6.1,
      direction: null,
      description: null,
    },
    report: { id: 10, report_date: '2024-01-15T00:00:00' } as BiomarkerValue['report'],
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
    created_at: '2024-01-15T00:00:00',
  },
  {
    id: 2,
    report_id: 11,
    biomarker_id: 101,
    biomarker: {
      id: 101,
      code: 'WBC',
      name: '白细胞',
      unit_standard: '10^9/L',
      category: null,
      reference_low: 4,
      reference_high: 10,
      direction: null,
      description: null,
    },
    report: { id: 11, report_date: '2024-02-20T00:00:00' } as BiomarkerValue['report'],
    original_name: '白细胞计数',
    original_value_text: '5.5',
    original_unit: '10^9/L',
    value: 5.5,
    unit: '10^9/L',
    reference_low: 4,
    reference_high: 10,
    status: 'normal',
    is_reviewed: true,
    reviewed_at: '2024-02-20T00:00:00',
    created_at: '2024-02-20T00:00:00',
  },
]

function renderWithRouter(ui: React.ReactElement, initialEntries = ['/biomarkers']) {
  return render(
    <MemoryRouter initialEntries={initialEntries}>
      <Routes>
        <Route path="/biomarkers" element={ui} />
        <Route path="/abnormal" element={<BiomarkerList abnormalOnly />} />
      </Routes>
    </MemoryRouter>
  )
}

describe('BiomarkerList', () => {
  beforeEach(() => {
    mockedListBiomarkerValues.mockReset()
    mockedExportBiomarkerValues.mockReset()
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  it('renders loading state initially', () => {
    mockedListBiomarkerValues.mockImplementation(() => new Promise(() => {}))
    renderWithRouter(<BiomarkerList />)
    expect(screen.getByText('加载指标列表...')).toBeInTheDocument()
  })

  it('renders error state when API fails', async () => {
    mockedListBiomarkerValues.mockRejectedValue(new Error('网络错误'))
    renderWithRouter(<BiomarkerList />)

    await waitFor(() => {
      expect(screen.getByText('指标列表加载失败')).toBeInTheDocument()
    })
    expect(screen.getByText('网络错误')).toBeInTheDocument()
  })

  it('renders empty state when no values', async () => {
    mockedListBiomarkerValues.mockResolvedValue([])
    renderWithRouter(<BiomarkerList />)

    await waitFor(() => {
      expect(screen.getByText('暂无指标记录')).toBeInTheDocument()
    })
    expect(screen.getByRole('link', { name: '上传报告' })).toBeInTheDocument()
  })

  it('renders rows with biomarker data and status badges', async () => {
    mockedListBiomarkerValues.mockResolvedValue(mockValues)
    renderWithRouter(<BiomarkerList />)

    await waitFor(() => {
      expect(screen.getByText('血糖')).toBeInTheDocument()
    })

    const rows = screen.getAllByRole('row')
    expect(rows.length).toBeGreaterThan(2)

    const tableBody = rows[0].closest('table')?.querySelector('tbody')
    expect(tableBody).toBeInTheDocument()
    if (!tableBody) return

    expect(within(tableBody).getByText('偏高')).toBeInTheDocument()
    expect(within(tableBody).getByText('正常')).toBeInTheDocument()
    expect(within(tableBody).getByText('未校对')).toBeInTheDocument()
    expect(within(tableBody).getByText('已校对')).toBeInTheDocument()
  })

  it('filters rows by status', async () => {
    mockedListBiomarkerValues.mockResolvedValue(mockValues)
    renderWithRouter(<BiomarkerList />)

    await waitFor(() => {
      expect(screen.getByText('血糖')).toBeInTheDocument()
    })

    const filter = screen.getByRole('combobox')
    await userEvent.selectOptions(filter, 'high')

    expect(screen.getByText('血糖')).toBeInTheDocument()
    expect(screen.queryByText('白细胞')).not.toBeInTheDocument()
  })

  it('triggers CSV export', async () => {
    mockedListBiomarkerValues.mockResolvedValue(mockValues)
    mockedExportBiomarkerValues.mockResolvedValue(new Blob(['']))
    renderWithRouter(<BiomarkerList />)

    await waitFor(() => {
      expect(screen.getByText('血糖')).toBeInTheDocument()
    })

    const csvButton = screen.getByRole('button', { name: /CSV/i })
    await userEvent.click(csvButton)

    await waitFor(() => {
      expect(mockedExportBiomarkerValues).toHaveBeenCalledWith('csv', { abnormal_only: false })
    })
  })

  it('uses abnormal_only filter on /abnormal route', async () => {
    mockedListBiomarkerValues.mockResolvedValue([])
    renderWithRouter(<BiomarkerList />, ['/abnormal'])

    await waitFor(() => {
      expect(screen.getByText('暂无异常指标')).toBeInTheDocument()
    })

    expect(mockedListBiomarkerValues).toHaveBeenCalledWith({
      abnormal_only: true,
      reviewed_only: false,
    })
  })
})
