/**
 * Excel Export utilities
 *
 * Note: For full Excel support, install xlsx package:
 * pnpm add xlsx
 *
 * This module provides a lightweight alternative using CSV with Excel-compatible format,
 * and prepares for full xlsx integration when the package is installed.
 */

import type { ExportColumn, ExcelOptions, ExportResult } from './types'
import { downloadBlob } from './csv'

const DEFAULT_EXCEL_OPTIONS: Partial<ExcelOptions> = {
  sheetName: 'Sheet1',
  includeTimestamp: true,
  autoFitColumns: true,
  freezeHeader: true,
  headerStyle: {
    bold: true,
    backgroundColor: '#4F46E5',
    textColor: '#FFFFFF',
  },
}

/**
 * Get value from row using accessor
 */
function getValue<T>(row: T, accessor: ExportColumn<T>['accessor']): unknown {
  if (typeof accessor === 'function') {
    return accessor(row)
  }
  return row[accessor as keyof T]
}

/**
 * Generate filename with optional timestamp
 */
function generateFilename(base: string, includeTimestamp: boolean, extension: string): string {
  if (includeTimestamp) {
    const now = new Date()
    const timestamp = now.toISOString().slice(0, 19).replace(/[:-]/g, '').replace('T', '_')
    return `${base}_${timestamp}.${extension}`
  }
  return `${base}.${extension}`
}

/**
 * Convert data to Excel-compatible format (using native xlsx if available, fallback to CSV)
 */
export async function exportToExcel<T>(
  data: T[],
  columns: ExportColumn<T>[],
  options: Partial<ExcelOptions> = {}
): Promise<ExportResult> {
  const opts = { ...DEFAULT_EXCEL_OPTIONS, ...options }

  try {
    // Try to use xlsx library if available
    const xlsx = await tryLoadXLSX()

    const filename = opts.filename || 'export'
    const optsWithFilename = { ...opts, filename }

    if (xlsx) {
      return exportWithXLSX(data, columns, optsWithFilename, xlsx)
    }

    // Fallback to CSV with Excel-compatible format
    return exportAsExcelCSV(data, columns, optsWithFilename)
  } catch (error) {
    return {
      success: false,
      error: error instanceof Error ? error.message : 'Unknown error',
    }
  }
}

// eslint-disable-next-line @typescript-eslint/no-explicit-any
type XLSXModule = any

/**
 * Try to dynamically load xlsx library
 */
async function tryLoadXLSX(): Promise<XLSXModule | null> {
  try {
    // Dynamic import - xlsx is an optional peer dependency
    // Use Function constructor to avoid static analysis by bundlers
    const moduleName = 'xlsx'
    const dynamicImport = new Function('m', 'return import(m)')
    const xlsx = await dynamicImport(moduleName)
    return xlsx
  } catch {
    // xlsx not installed - will use CSV fallback
    return null
  }
}

/**
 * Export using xlsx library (when available)
 */
function exportWithXLSX<T>(
  data: T[],
  columns: ExportColumn<T>[],
  options: Partial<ExcelOptions> & { filename: string },
  xlsx: XLSXModule
): ExportResult {
  const filename = generateFilename(
    options.filename || 'export',
    options.includeTimestamp ?? true,
    'xlsx'
  )

  // Prepare data for xlsx
  const headers = columns.map(col => col.header)
  const rows = data.map(row =>
    columns.map(col => {
      const value = getValue(row, col.accessor)
      return col.format ? col.format(value) : value
    })
  )

  // Create worksheet
  const wsData = [headers, ...rows]
  const ws = xlsx.utils.aoa_to_sheet(wsData)

  // Set column widths
  if (options.autoFitColumns) {
    const colWidths = columns.map((col, i) => {
      if (col.width) return { wch: col.width }
      const maxLen = Math.max(col.header.length, ...rows.map(row => String(row[i] ?? '').length))
      return { wch: Math.min(maxLen + 2, 50) }
    })
    ws['!cols'] = colWidths
  }

  // Freeze header row
  if (options.freezeHeader) {
    ws['!freeze'] = { xSplit: 0, ySplit: 1 }
  }

  // Create workbook
  const wb = xlsx.utils.book_new()
  xlsx.utils.book_append_sheet(wb, ws, options.sheetName || 'Sheet1')

  // Generate buffer and download
  const buffer = xlsx.write(wb, { bookType: 'xlsx', type: 'array' })
  const blob = new Blob([buffer], {
    type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
  })

  downloadBlob(blob, filename)

  return { success: true, filename, blob }
}

/**
 * Export as CSV with Excel-compatible format (fallback)
 */
function exportAsExcelCSV<T>(
  data: T[],
  columns: ExportColumn<T>[],
  options: Partial<ExcelOptions> & { filename: string }
): ExportResult {
  const filename = generateFilename(
    options.filename || 'export',
    options.includeTimestamp ?? true,
    'csv'
  )

  // Use tab separator for better Excel compatibility
  const separator = '\t'

  // Header row
  const headerRow = columns.map(col => escapeExcelValue(col.header)).join(separator)

  // Data rows
  const dataRows = data.map(row =>
    columns
      .map(col => {
        const value = getValue(row, col.accessor)
        const formatted = col.format ? col.format(value) : value
        return escapeExcelValue(formatted)
      })
      .join(separator)
  )

  // Add BOM for Excel UTF-8 compatibility
  const csvContent = '\uFEFF' + [headerRow, ...dataRows].join('\r\n')
  const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8' })

  downloadBlob(blob, filename)

  return { success: true, filename, blob }
}

/**
 * Escape value for Excel
 */
function escapeExcelValue(value: unknown): string {
  if (value === null || value === undefined) {
    return ''
  }

  const stringValue = String(value)

  // Quote if contains special characters
  if (
    stringValue.includes('\t') ||
    stringValue.includes('"') ||
    stringValue.includes('\n') ||
    stringValue.includes('\r')
  ) {
    return `"${stringValue.replace(/"/g, '""')}"`
  }

  return stringValue
}

/**
 * Check if xlsx library is available
 */
export async function isXLSXAvailable(): Promise<boolean> {
  const xlsx = await tryLoadXLSX()
  return xlsx !== null
}
