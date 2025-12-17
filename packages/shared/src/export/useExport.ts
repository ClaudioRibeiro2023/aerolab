/**
 * React hook for exporting data
 */

import { useState, useCallback } from 'react'
import type {
  ExportColumn,
  CSVOptions,
  ExcelOptions,
  PDFOptions,
  ExportResult,
  ExportFormat,
} from './types'
import { exportToCSV } from './csv'
import { exportToExcel } from './excel'
import { exportToPDF } from './pdf'

export interface UseExportOptions {
  /** Callback when export starts */
  onExportStart?: (format: ExportFormat) => void
  /** Callback when export completes */
  onExportComplete?: (result: ExportResult, format: ExportFormat) => void
  /** Callback when export fails */
  onExportError?: (error: string, format: ExportFormat) => void
}

export interface UseExportReturn<T> {
  /** Whether an export is in progress */
  isExporting: boolean
  /** Current export format being processed */
  currentFormat: ExportFormat | null
  /** Last export result */
  lastResult: ExportResult | null
  /** Export to CSV */
  exportCSV: (data: T[], columns: ExportColumn<T>[], options?: Partial<CSVOptions>) => void
  /** Export to Excel */
  exportExcel: (
    data: T[],
    columns: ExportColumn<T>[],
    options?: Partial<ExcelOptions>
  ) => Promise<void>
  /** Export to PDF */
  exportPDF: (data: T[], columns: ExportColumn<T>[], options?: Partial<PDFOptions>) => Promise<void>
  /** Export to any format */
  exportData: (
    format: ExportFormat,
    data: T[],
    columns: ExportColumn<T>[],
    options?: Partial<CSVOptions | ExcelOptions | PDFOptions>
  ) => Promise<void>
}

/**
 * Hook for exporting data to various formats
 *
 * @example
 * ```tsx
 * const { exportCSV, exportPDF, isExporting } = useExport<User>({
 *   onExportComplete: (result) => toast.success(`Exported to ${result.filename}`),
 *   onExportError: (error) => toast.error(error),
 * })
 *
 * const columns: ExportColumn<User>[] = [
 *   { header: 'Nome', accessor: 'name' },
 *   { header: 'Email', accessor: 'email' },
 *   { header: 'Criado em', accessor: 'createdAt', format: (v) => new Date(v).toLocaleDateString('pt-BR') },
 * ]
 *
 * <Button onClick={() => exportCSV(users, columns, { filename: 'usuarios' })} disabled={isExporting}>
 *   {isExporting ? 'Exportando...' : 'Exportar CSV'}
 * </Button>
 * ```
 */
export function useExport<T>(options: UseExportOptions = {}): UseExportReturn<T> {
  const [isExporting, setIsExporting] = useState(false)
  const [currentFormat, setCurrentFormat] = useState<ExportFormat | null>(null)
  const [lastResult, setLastResult] = useState<ExportResult | null>(null)

  const handleExport = useCallback(
    async (format: ExportFormat, exportFn: () => ExportResult | Promise<ExportResult>) => {
      setIsExporting(true)
      setCurrentFormat(format)
      options.onExportStart?.(format)

      try {
        const result = await exportFn()
        setLastResult(result)

        if (result.success) {
          options.onExportComplete?.(result, format)
        } else {
          options.onExportError?.(result.error || 'Erro desconhecido', format)
        }
      } catch (error) {
        const errorMessage = error instanceof Error ? error.message : 'Erro desconhecido'
        const result: ExportResult = { success: false, error: errorMessage }
        setLastResult(result)
        options.onExportError?.(errorMessage, format)
      } finally {
        setIsExporting(false)
        setCurrentFormat(null)
      }
    },
    [options]
  )

  const exportCSV = useCallback(
    (data: T[], columns: ExportColumn<T>[], csvOptions?: Partial<CSVOptions>) => {
      handleExport('csv', () => exportToCSV(data, columns, csvOptions))
    },
    [handleExport]
  )

  const exportExcel = useCallback(
    async (data: T[], columns: ExportColumn<T>[], excelOptions?: Partial<ExcelOptions>) => {
      await handleExport('excel', () => exportToExcel(data, columns, excelOptions))
    },
    [handleExport]
  )

  const exportPDF = useCallback(
    async (data: T[], columns: ExportColumn<T>[], pdfOptions?: Partial<PDFOptions>) => {
      await handleExport('pdf', () => exportToPDF(data, columns, pdfOptions))
    },
    [handleExport]
  )

  const exportData = useCallback(
    async (
      format: ExportFormat,
      data: T[],
      columns: ExportColumn<T>[],
      exportOptions?: Partial<CSVOptions | ExcelOptions | PDFOptions>
    ) => {
      switch (format) {
        case 'csv':
          exportCSV(data, columns, exportOptions as Partial<CSVOptions>)
          break
        case 'excel':
          await exportExcel(data, columns, exportOptions as Partial<ExcelOptions>)
          break
        case 'pdf':
          await exportPDF(data, columns, exportOptions as Partial<PDFOptions>)
          break
      }
    },
    [exportCSV, exportExcel, exportPDF]
  )

  return {
    isExporting,
    currentFormat,
    lastResult,
    exportCSV,
    exportExcel,
    exportPDF,
    exportData,
  }
}
