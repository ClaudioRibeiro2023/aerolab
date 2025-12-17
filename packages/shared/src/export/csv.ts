/**
 * CSV Export utilities
 */

import type { ExportColumn, CSVOptions, ExportResult } from './types'

const DEFAULT_CSV_OPTIONS: Partial<CSVOptions> = {
  separator: ',',
  includeBOM: true,
  quoteAll: false,
  includeTimestamp: true,
}

/**
 * Escape a value for CSV format
 */
function escapeCSVValue(value: unknown, separator: string, quoteAll: boolean): string {
  if (value === null || value === undefined) {
    return ''
  }

  const stringValue = String(value)
  const needsQuotes =
    quoteAll ||
    stringValue.includes(separator) ||
    stringValue.includes('"') ||
    stringValue.includes('\n') ||
    stringValue.includes('\r')

  if (needsQuotes) {
    return `"${stringValue.replace(/"/g, '""')}"`
  }

  return stringValue
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
 * Convert data to CSV string
 */
export function toCSV<T>(
  data: T[],
  columns: ExportColumn<T>[],
  options: Partial<CSVOptions> = {}
): string {
  const opts = { ...DEFAULT_CSV_OPTIONS, ...options }
  const separator = opts.separator!
  const quoteAll = opts.quoteAll!

  // Header row
  const headerRow = columns
    .map(col => escapeCSVValue(col.header, separator, quoteAll))
    .join(separator)

  // Data rows
  const dataRows = data.map(row =>
    columns
      .map(col => {
        const value = getValue(row, col.accessor)
        const formatted = col.format ? col.format(value) : value
        return escapeCSVValue(formatted, separator, quoteAll)
      })
      .join(separator)
  )

  // Combine with BOM if needed
  const csvContent = [headerRow, ...dataRows].join('\r\n')
  return opts.includeBOM ? '\uFEFF' + csvContent : csvContent
}

/**
 * Export data to CSV file and trigger download
 */
export function exportToCSV<T>(
  data: T[],
  columns: ExportColumn<T>[],
  options: Partial<CSVOptions> = {}
): ExportResult {
  try {
    const opts = { ...DEFAULT_CSV_OPTIONS, ...options }
    const filename = generateFilename(opts.filename || 'export', opts.includeTimestamp!, 'csv')

    const csvContent = toCSV(data, columns, opts)
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8' })

    // Trigger download
    downloadBlob(blob, filename)

    return { success: true, filename, blob }
  } catch (error) {
    return {
      success: false,
      error: error instanceof Error ? error.message : 'Unknown error',
    }
  }
}

/**
 * Download a blob as a file
 */
export function downloadBlob(blob: Blob, filename: string): void {
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = filename
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  URL.revokeObjectURL(url)
}
