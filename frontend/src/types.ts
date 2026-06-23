export interface User {
  id: number
  username: string
  created_at: string
}

export interface Report {
  id: number
  user_id: number
  filename: string
  original_name: string
  stored_path: string
  report_date: string | null
  status: 'pending' | 'parsed' | 'error'
  error_message: string | null
  created_at: string
  updated_at: string
}

export interface ReportDetail extends Report {
  values: BiomarkerValue[]
}

export interface Biomarker {
  id: number
  code: string
  name: string
  unit_standard: string
  category: string | null
  reference_low: number | null
  reference_high: number | null
  direction: string | null
  description: string | null
}

export interface BiomarkerValue {
  id: number
  report_id: number
  biomarker_id: number
  biomarker: Biomarker
  report?: Report
  original_name: string | null
  original_value_text: string | null
  original_unit: string | null
  value: number
  unit: string
  reference_low: number | null
  reference_high: number | null
  status: 'normal' | 'high' | 'low' | null
  is_reviewed: boolean
  reviewed_at: string | null
  created_at: string
}

export interface TrendPoint {
  report_id: number
  report_date: string | null
  value: number
  unit: string
  status: string | null
  is_reviewed: boolean
}

export interface TrendData {
  biomarker: Biomarker
  points: TrendPoint[]
}

export interface TrendAnalysis {
  biomarker_code: string
  biomarker_name: string
  analysis: string
  disclaimer: string
}
