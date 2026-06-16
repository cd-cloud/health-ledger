import api from './client'
import type { Biomarker, BiomarkerValue, TrendAnalysis, TrendData } from '../types'

export async function listBiomarkers(): Promise<Biomarker[]> {
  const { data } = await api.get('/biomarkers')
  return data
}

export interface ValueFilters {
  report_id?: number
  biomarker_code?: string
  status?: string
  abnormal_only?: boolean
  reviewed_only?: boolean
}

export async function listBiomarkerValues(filters: ValueFilters = {}): Promise<BiomarkerValue[]> {
  const { data } = await api.get('/biomarkers/values', { params: filters })
  return data
}

export async function updateBiomarkerValue(
  id: number,
  payload: Partial<Pick<BiomarkerValue, 'value' | 'unit' | 'status' | 'is_reviewed'>>,
): Promise<BiomarkerValue> {
  const { data } = await api.patch(`/biomarkers/values/${id}`, payload)
  return data
}

export interface BatchUpdateItem {
  id: number
  value?: number
  unit?: string
  status?: 'normal' | 'high' | 'low'
  is_reviewed?: boolean
}

export async function batchUpdateBiomarkerValues(
  items: BatchUpdateItem[],
): Promise<BiomarkerValue[]> {
  const { data } = await api.patch('/biomarkers/values/batch', { items })
  return data
}

export async function exportBiomarkerValues(
  format: 'csv' | 'json' = 'csv',
  filters: ValueFilters = {},
): Promise<Blob> {
  const { data } = await api.get('/biomarkers/values/export', {
    params: { format, ...filters },
    responseType: 'blob',
  })
  return data
}

export async function getAbnormalSummary(): Promise<BiomarkerValue[]> {
  const { data } = await api.get('/biomarkers/summary/abnormal')
  return data
}

export async function getTrend(biomarkerCode: string): Promise<TrendData> {
  const { data } = await api.get(`/trends/${biomarkerCode}`)
  return data
}

export async function analyzeTrend(biomarkerCode: string): Promise<TrendAnalysis> {
  const { data } = await api.post(`/trends/${biomarkerCode}/analyze`)
  return data
}
