import api from './client'
import type { Report, ReportDetail } from '../types'

export async function listReports(): Promise<{ items: Report[]; total: number }> {
  const { data } = await api.get('/reports')
  return data
}

export async function getReport(id: number): Promise<ReportDetail> {
  const { data } = await api.get(`/reports/${id}`)
  return data
}

export async function uploadReport(file: File, reportDate?: string): Promise<Report> {
  const formData = new FormData()
  formData.append('file', file)
  if (reportDate) {
    formData.append('report_date', reportDate)
  }
  const { data } = await api.post('/reports/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
  return data
}

export async function parseReport(id: number): Promise<{ report_id: number; status: string; extracted_count: number; message?: string }> {
  const { data } = await api.post(`/reports/${id}/parse`)
  return data
}

export async function deleteReport(id: number): Promise<void> {
  await api.delete(`/reports/${id}`)
}
