'use client';

import React, { useState, useMemo } from 'react';
import { 
  ChevronUp, 
  ChevronDown, 
  ChevronLeft, 
  ChevronRight,
  Search 
} from 'lucide-react';
import { cn } from '@/lib/utils';
import type { Widget, TableConfig, TableColumn } from '@/types/dashboard';

interface TableWidgetProps {
  widget: Widget;
  data: Record<string, unknown>[];
  loading?: boolean;
  error?: string;
}

const formatCell = (value: unknown, format?: string): string => {
  if (value === null || value === undefined) return '-';
  
  const numValue = Number(value);
  
  switch (format) {
    case 'number':
      return isNaN(numValue) ? String(value) : numValue.toLocaleString();
    
    case 'currency':
      return isNaN(numValue) 
        ? String(value)
        : new Intl.NumberFormat('en-US', { 
            style: 'currency', 
            currency: 'USD' 
          }).format(numValue);
    
    case 'percent':
      return isNaN(numValue) 
        ? String(value)
        : `${(numValue * 100).toFixed(1)}%`;
    
    case 'date':
      const date = new Date(String(value));
      return isNaN(date.getTime()) 
        ? String(value)
        : date.toLocaleDateString();
    
    case 'duration':
      if (isNaN(numValue)) return String(value);
      if (numValue < 1000) return `${numValue.toFixed(0)}ms`;
      if (numValue < 60000) return `${(numValue / 1000).toFixed(1)}s`;
      return `${(numValue / 60000).toFixed(1)}m`;
    
    case 'badge':
      return String(value);
    
    default:
      return String(value);
  }
};

const Badge: React.FC<{ value: string }> = ({ value }) => {
  const colorMap: Record<string, string> = {
    success: 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400',
    error: 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400',
    warning: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-400',
    info: 'bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-400',
    pending: 'bg-gray-100 text-gray-800 dark:bg-gray-900/30 dark:text-gray-400',
  };
  
  const colorClass = colorMap[value.toLowerCase()] || colorMap.info;
  
  return (
    <span className={cn('px-2 py-0.5 rounded-full text-xs font-medium', colorClass)}>
      {value}
    </span>
  );
};

export const TableWidget: React.FC<TableWidgetProps> = ({
  widget,
  data,
  loading = false,
  error,
}) => {
  const config = widget.config?.table || {} as TableConfig;
  const [sortColumn, setSortColumn] = useState<string | null>(null);
  const [sortDirection, setSortDirection] = useState<'asc' | 'desc'>('asc');
  const [currentPage, setCurrentPage] = useState(1);
  const [searchQuery, setSearchQuery] = useState('');
  
  const pageSize = config.pageSize || 10;
  
  // Generate columns from data if not provided
  const columns: TableColumn[] = useMemo(() => {
    if (config.columns && config.columns.length > 0) {
      return config.columns;
    }
    
    if (data.length === 0) return [];
    
    return Object.keys(data[0]).map(key => ({
      key,
      title: key.charAt(0).toUpperCase() + key.slice(1).replace(/_/g, ' '),
      sortable: true,
    }));
  }, [config.columns, data]);
  
  // Filter and sort data
  const processedData = useMemo(() => {
    let result = [...data];
    
    // Search filter
    if (searchQuery && config.filterable !== false) {
      const query = searchQuery.toLowerCase();
      result = result.filter(row => 
        Object.values(row).some(v => 
          String(v).toLowerCase().includes(query)
        )
      );
    }
    
    // Sort
    if (sortColumn && config.sortable !== false) {
      result.sort((a, b) => {
        const aVal = a[sortColumn];
        const bVal = b[sortColumn];
        
        if (aVal === bVal) return 0;
        if (aVal === null || aVal === undefined) return 1;
        if (bVal === null || bVal === undefined) return -1;
        
        const comparison = aVal < bVal ? -1 : 1;
        return sortDirection === 'asc' ? comparison : -comparison;
      });
    }
    
    return result;
  }, [data, searchQuery, sortColumn, sortDirection, config.filterable, config.sortable]);
  
  // Paginate
  const paginatedData = useMemo(() => {
    if (config.pagination === false) return processedData;
    
    const start = (currentPage - 1) * pageSize;
    return processedData.slice(start, start + pageSize);
  }, [processedData, currentPage, pageSize, config.pagination]);
  
  const totalPages = Math.ceil(processedData.length / pageSize);
  
  const handleSort = (columnKey: string) => {
    if (sortColumn === columnKey) {
      setSortDirection(prev => prev === 'asc' ? 'desc' : 'asc');
    } else {
      setSortColumn(columnKey);
      setSortDirection('asc');
    }
  };
  
  if (loading) {
    return (
      <div className="p-4 rounded-lg border bg-card h-full animate-pulse">
        <div className="h-4 w-32 bg-muted rounded mb-4" />
        <div className="space-y-2">
          {[...Array(5)].map((_, i) => (
            <div key={i} className="h-8 bg-muted rounded" />
          ))}
        </div>
      </div>
    );
  }
  
  if (error) {
    return (
      <div className="p-4 rounded-lg border bg-card h-full">
        <p className="text-sm font-medium">{widget.title}</p>
        <p className="text-sm text-destructive mt-2">{error}</p>
      </div>
    );
  }
  
  return (
    <div className="p-4 rounded-lg border bg-card h-full flex flex-col">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div>
          <h3 className="text-sm font-medium">{widget.title}</h3>
          {widget.description && (
            <p className="text-xs text-muted-foreground">{widget.description}</p>
          )}
        </div>
        
        {config.filterable !== false && (
          <div className="relative">
            <Search className="absolute left-2 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
            <input
              type="text"
              placeholder="Search..."
              value={searchQuery}
              onChange={e => setSearchQuery(e.target.value)}
              className="pl-8 pr-3 py-1.5 text-sm border rounded-md bg-background w-48"
            />
          </div>
        )}
      </div>
      
      {/* Table */}
      <div className="flex-1 overflow-auto">
        <table className="w-full text-sm">
          <thead className="sticky top-0 bg-muted/50">
            <tr>
              {columns.map(column => (
                <th
                  key={column.key}
                  className={cn(
                    'px-3 py-2 font-medium text-muted-foreground',
                    column.align === 'right' && 'text-right',
                    column.align === 'center' && 'text-center',
                    column.sortable !== false && config.sortable !== false && 'cursor-pointer hover:text-foreground'
                  )}
                  style={{ width: column.width }}
                  onClick={() => column.sortable !== false && handleSort(column.key)}
                >
                  <div className="flex items-center gap-1">
                    <span>{column.title}</span>
                    {sortColumn === column.key && (
                      sortDirection === 'asc' 
                        ? <ChevronUp className="h-3 w-3" />
                        : <ChevronDown className="h-3 w-3" />
                    )}
                  </div>
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {paginatedData.map((row, rowIdx) => (
              <tr 
                key={rowIdx}
                className="border-b hover:bg-muted/30 transition-colors"
              >
                {columns.map(column => (
                  <td
                    key={column.key}
                    className={cn(
                      'px-3 py-2',
                      column.align === 'right' && 'text-right',
                      column.align === 'center' && 'text-center'
                    )}
                  >
                    {column.format === 'badge' ? (
                      <Badge value={String(row[column.key])} />
                    ) : (
                      formatCell(row[column.key], column.format)
                    )}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
        
        {paginatedData.length === 0 && (
          <div className="py-8 text-center text-muted-foreground">
            No data available
          </div>
        )}
      </div>
      
      {/* Pagination */}
      {config.pagination !== false && totalPages > 1 && (
        <div className="flex items-center justify-between pt-4 border-t mt-4">
          <span className="text-sm text-muted-foreground">
            Showing {((currentPage - 1) * pageSize) + 1} to {Math.min(currentPage * pageSize, processedData.length)} of {processedData.length}
          </span>
          
          <div className="flex items-center gap-2">
            <button
              onClick={() => setCurrentPage(p => Math.max(1, p - 1))}
              disabled={currentPage === 1}
              className="p-1 rounded hover:bg-muted disabled:opacity-50"
              title="Previous page"
              aria-label="Previous page"
            >
              <ChevronLeft className="h-4 w-4" />
            </button>
            
            <span className="text-sm">
              Page {currentPage} of {totalPages}
            </span>
            
            <button
              onClick={() => setCurrentPage(p => Math.min(totalPages, p + 1))}
              disabled={currentPage === totalPages}
              className="p-1 rounded hover:bg-muted disabled:opacity-50"
              title="Next page"
              aria-label="Next page"
            >
              <ChevronRight className="h-4 w-4" />
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

export default TableWidget;
