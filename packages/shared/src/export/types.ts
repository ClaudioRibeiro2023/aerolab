/**
 * Types for export functionality
 */

export interface ExportColumn<T = unknown> {
  /** Column header label */
  header: string
  /** Key to access data or accessor function */
  accessor: keyof T | ((row: T) => string | number | boolean | null | undefined)
  /** Optional width (for Excel) */
  width?: number
  /** Optional format function */
  format?: (value: unknown) => string
}

export interface ExportOptions {
  /** File name without extension */
  filename: string
  /** Sheet name (for Excel) */
  sheetName?: string
  /** Include timestamp in filename */
  includeTimestamp?: boolean
  /** Date format for timestamp */
  dateFormat?: string
}

export interface CSVOptions extends ExportOptions {
  /** Field separator */
  separator?: string
  /** Include BOM for Excel compatibility */
  includeBOM?: boolean
  /** Quote all fields */
  quoteAll?: boolean
}

export interface ExcelOptions extends ExportOptions {
  /** Auto-fit column widths */
  autoFitColumns?: boolean
  /** Freeze header row */
  freezeHeader?: boolean
  /** Header row style */
  headerStyle?: {
    bold?: boolean
    backgroundColor?: string
    textColor?: string
  }
}

export interface PDFOptions extends ExportOptions {
  /** Page orientation */
  orientation?: 'portrait' | 'landscape'
  /** Page size */
  pageSize?: 'A4' | 'A3' | 'Letter' | 'Legal'
  /** Title for the report */
  title?: string
  /** Subtitle or description */
  subtitle?: string
  /** Include page numbers */
  includePageNumbers?: boolean
  /** Header logo URL */
  logoUrl?: string
  /** Footer text */
  footerText?: string
}

export interface ExportResult {
  success: boolean
  filename?: string
  error?: string
  blob?: Blob
}

export type ExportFormat = 'csv' | 'excel' | 'pdf'
