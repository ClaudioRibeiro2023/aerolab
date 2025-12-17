/**
 * PDF Export utilities
 *
 * Note: For full PDF support, install jspdf and jspdf-autotable:
 * pnpm add jspdf jspdf-autotable
 *
 * This module provides browser-native print-to-PDF as fallback,
 * and prepares for full jspdf integration when packages are installed.
 */

import type { ExportColumn, PDFOptions, ExportResult } from './types'
import { downloadBlob } from './csv'

const DEFAULT_PDF_OPTIONS: Partial<PDFOptions> = {
  orientation: 'portrait',
  pageSize: 'A4',
  includeTimestamp: true,
  includePageNumbers: true,
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
 * Export data to PDF
 */
export async function exportToPDF<T>(
  data: T[],
  columns: ExportColumn<T>[],
  options: Partial<PDFOptions> = {}
): Promise<ExportResult> {
  const opts = { ...DEFAULT_PDF_OPTIONS, ...options }

  try {
    // Try to use jspdf library if available
    const jspdf = await tryLoadJsPDF()

    const filename = opts.filename || 'report'
    const optsWithFilename = { ...opts, filename }

    if (jspdf) {
      return exportWithJsPDF(data, columns, optsWithFilename, jspdf)
    }

    // Fallback to browser print dialog
    return exportWithPrintDialog(data, columns, optsWithFilename)
  } catch (error) {
    return {
      success: false,
      error: error instanceof Error ? error.message : 'Unknown error',
    }
  }
}

// eslint-disable-next-line @typescript-eslint/no-explicit-any
type JsPDFModule = { jsPDF: any }

/**
 * Try to dynamically load jspdf library
 */
async function tryLoadJsPDF(): Promise<JsPDFModule | null> {
  try {
    // Dynamic import - jspdf is an optional peer dependency
    // Use Function constructor to avoid static analysis by bundlers
    const dynamicImport = new Function('m', 'return import(m)')
    const jspdf = await dynamicImport('jspdf')
    await dynamicImport('jspdf-autotable')
    return { jsPDF: jspdf.jsPDF }
  } catch {
    // jspdf not installed - will use print dialog fallback
    return null
  }
}

/**
 * Export using jspdf library (when available)
 */
function exportWithJsPDF<T>(
  data: T[],
  columns: ExportColumn<T>[],
  options: Partial<PDFOptions> & { filename: string },
  jspdf: JsPDFModule
): ExportResult {
  const filename = generateFilename(
    options.filename || 'report',
    options.includeTimestamp ?? true,
    'pdf'
  )

  const { jsPDF } = jspdf

  // Create PDF document
  const doc = new jsPDF({
    orientation: options.orientation,
    unit: 'mm',
    format: options.pageSize?.toLowerCase() as 'a4' | 'a3' | 'letter' | 'legal',
  })

  const pageWidth = doc.internal.pageSize.getWidth()
  let yPosition = 20

  // Add title
  if (options.title) {
    doc.setFontSize(18)
    doc.setFont('helvetica', 'bold')
    doc.text(options.title, pageWidth / 2, yPosition, { align: 'center' })
    yPosition += 10
  }

  // Add subtitle
  if (options.subtitle) {
    doc.setFontSize(12)
    doc.setFont('helvetica', 'normal')
    doc.text(options.subtitle, pageWidth / 2, yPosition, { align: 'center' })
    yPosition += 10
  }

  // Add timestamp
  doc.setFontSize(10)
  doc.setTextColor(128)
  const timestamp = new Date().toLocaleString('pt-BR')
  doc.text(`Gerado em: ${timestamp}`, pageWidth / 2, yPosition, { align: 'center' })
  yPosition += 10

  // Prepare table data
  const headers = columns.map(col => col.header)
  const rows = data.map(row =>
    columns.map(col => {
      const value = getValue(row, col.accessor)
      return col.format ? col.format(value) : String(value ?? '')
    })
  )

  // Add table using autoTable plugin
  const autoTable = (doc as unknown as { autoTable: (options: unknown) => void }).autoTable
  if (autoTable) {
    autoTable({
      head: [headers],
      body: rows,
      startY: yPosition,
      theme: 'striped',
      headStyles: {
        fillColor: [79, 70, 229], // Indigo
        textColor: 255,
        fontStyle: 'bold',
      },
      styles: {
        fontSize: 9,
        cellPadding: 3,
      },
      didDrawPage: (pageData: { pageNumber: number }) => {
        // Add page numbers
        if (options.includePageNumbers) {
          const pageNumber = pageData.pageNumber
          doc.setFontSize(10)
          doc.setTextColor(128)
          doc.text(`Página ${pageNumber}`, pageWidth / 2, doc.internal.pageSize.getHeight() - 10, {
            align: 'center',
          })
        }

        // Add footer text
        if (options.footerText) {
          doc.setFontSize(8)
          doc.setTextColor(128)
          doc.text(options.footerText, pageWidth / 2, doc.internal.pageSize.getHeight() - 5, {
            align: 'center',
          })
        }
      },
    })
  }

  // Generate blob and download
  const blob = doc.output('blob')
  downloadBlob(blob, filename)

  return { success: true, filename, blob }
}

/**
 * Export using browser print dialog (fallback)
 */
function exportWithPrintDialog<T>(
  data: T[],
  columns: ExportColumn<T>[],
  options: Partial<PDFOptions> & { filename: string }
): ExportResult {
  // Create a printable HTML document
  const html = generatePrintableHTML(data, columns, options)

  // Open in new window and trigger print
  const printWindow = window.open('', '_blank')
  if (!printWindow) {
    return {
      success: false,
      error: 'Não foi possível abrir janela de impressão. Verifique se popups estão permitidos.',
    }
  }

  printWindow.document.write(html)
  printWindow.document.close()

  // Wait for content to load, then print
  printWindow.onload = () => {
    printWindow.print()
  }

  return {
    success: true,
    filename: generateFilename(
      options.filename || 'report',
      options.includeTimestamp ?? true,
      'pdf'
    ),
  }
}

/**
 * Generate printable HTML for PDF
 */
function generatePrintableHTML<T>(
  data: T[],
  columns: ExportColumn<T>[],
  options: PDFOptions
): string {
  const timestamp = new Date().toLocaleString('pt-BR')

  const tableRows = data
    .map(
      row =>
        `<tr>${columns
          .map(col => {
            const value = getValue(row, col.accessor)
            const formatted = col.format ? col.format(value) : String(value ?? '')
            return `<td>${escapeHTML(formatted)}</td>`
          })
          .join('')}</tr>`
    )
    .join('')

  return `
<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <title>${escapeHTML(options.title || 'Relatório')}</title>
  <style>
    * { box-sizing: border-box; }
    body {
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
      padding: 20px;
      color: #1f2937;
    }
    .header { text-align: center; margin-bottom: 20px; }
    .title { font-size: 24px; font-weight: bold; margin: 0 0 8px 0; }
    .subtitle { font-size: 14px; color: #6b7280; margin: 0 0 4px 0; }
    .timestamp { font-size: 12px; color: #9ca3af; }
    table {
      width: 100%;
      border-collapse: collapse;
      margin-top: 20px;
    }
    th, td {
      border: 1px solid #e5e7eb;
      padding: 8px 12px;
      text-align: left;
    }
    th {
      background-color: #4f46e5;
      color: white;
      font-weight: 600;
    }
    tr:nth-child(even) { background-color: #f9fafb; }
    tr:hover { background-color: #f3f4f6; }
    .footer {
      margin-top: 20px;
      text-align: center;
      font-size: 10px;
      color: #9ca3af;
    }
    @media print {
      body { padding: 0; }
      .no-print { display: none; }
    }
  </style>
</head>
<body>
  <div class="header">
    ${options.title ? `<h1 class="title">${escapeHTML(options.title)}</h1>` : ''}
    ${options.subtitle ? `<p class="subtitle">${escapeHTML(options.subtitle)}</p>` : ''}
    <p class="timestamp">Gerado em: ${timestamp}</p>
  </div>
  <table>
    <thead>
      <tr>${columns.map(col => `<th>${escapeHTML(col.header)}</th>`).join('')}</tr>
    </thead>
    <tbody>
      ${tableRows}
    </tbody>
  </table>
  ${options.footerText ? `<div class="footer">${escapeHTML(options.footerText)}</div>` : ''}
</body>
</html>
`
}

/**
 * Escape HTML special characters
 */
function escapeHTML(str: string): string {
  return str
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;')
}

/**
 * Check if jspdf library is available
 */
export async function isJsPDFAvailable(): Promise<boolean> {
  const jspdf = await tryLoadJsPDF()
  return jspdf !== null
}
