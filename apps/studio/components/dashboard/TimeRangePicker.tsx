'use client';

import React, { useState } from 'react';
import { Calendar, Clock, ChevronDown } from 'lucide-react';
import { cn } from '@/lib/utils';
import type { TimeRange, PresetTimeRange } from '@/types/dashboard';

interface TimeRangePickerProps {
  value: TimeRange;
  onChange: (range: TimeRange | PresetTimeRange) => void;
  className?: string;
}

interface PresetOption {
  label: string;
  value: PresetTimeRange;
  description: string;
}

const presets: PresetOption[] = [
  { label: 'Last 5 minutes', value: '5m', description: 'Last 5 min' },
  { label: 'Last 15 minutes', value: '15m', description: 'Last 15 min' },
  { label: 'Last 30 minutes', value: '30m', description: 'Last 30 min' },
  { label: 'Last 1 hour', value: '1h', description: 'Last 1 hour' },
  { label: 'Last 3 hours', value: '3h', description: 'Last 3 hours' },
  { label: 'Last 6 hours', value: '6h', description: 'Last 6 hours' },
  { label: 'Last 12 hours', value: '12h', description: 'Last 12 hours' },
  { label: 'Last 24 hours', value: '24h', description: 'Last 24 hours' },
  { label: 'Last 2 days', value: '2d', description: 'Last 2 days' },
  { label: 'Last 7 days', value: '7d', description: 'Last 7 days' },
  { label: 'Last 30 days', value: '30d', description: 'Last 30 days' },
  { label: 'Last 90 days', value: '90d', description: 'Last 90 days' },
];

const formatTimeRange = (range: TimeRange): string => {
  if (range.label) {
    const preset = presets.find(p => p.value === range.label);
    if (preset) return preset.description;
  }
  
  const start = new Date(range.start);
  const end = new Date(range.end);
  
  const formatDate = (date: Date) => {
    return date.toLocaleString('en-US', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };
  
  return `${formatDate(start)} - ${formatDate(end)}`;
};

export const TimeRangePicker: React.FC<TimeRangePickerProps> = ({
  value,
  onChange,
  className,
}) => {
  const [isOpen, setIsOpen] = useState(false);
  const [activeTab, setActiveTab] = useState<'presets' | 'custom'>('presets');
  const [customStart, setCustomStart] = useState('');
  const [customEnd, setCustomEnd] = useState('');
  
  const handlePresetSelect = (preset: PresetTimeRange) => {
    onChange(preset);
    setIsOpen(false);
  };
  
  const handleCustomApply = () => {
    if (customStart && customEnd) {
      onChange({
        start: new Date(customStart).toISOString(),
        end: new Date(customEnd).toISOString(),
      });
      setIsOpen(false);
    }
  };
  
  return (
    <div className={cn('relative', className)}>
      <button
        onClick={() => setIsOpen(!isOpen)}
        className={cn(
          'flex items-center gap-2 px-3 py-2 rounded-md border bg-background',
          'hover:bg-muted transition-colors',
          'text-sm font-medium'
        )}
        aria-label="Select time range"
      >
        <Clock className="h-4 w-4 text-muted-foreground" />
        <span>{formatTimeRange(value)}</span>
        <ChevronDown className={cn(
          'h-4 w-4 text-muted-foreground transition-transform',
          isOpen && 'rotate-180'
        )} />
      </button>
      
      {isOpen && (
        <>
          {/* Backdrop */}
          <div 
            className="fixed inset-0 z-40" 
            onClick={() => setIsOpen(false)} 
          />
          
          {/* Dropdown */}
          <div className="absolute right-0 top-full mt-2 z-50 w-80 bg-background border rounded-lg shadow-lg">
            {/* Tabs */}
            <div className="flex border-b">
              <button
                onClick={() => setActiveTab('presets')}
                className={cn(
                  'flex-1 px-4 py-2 text-sm font-medium',
                  activeTab === 'presets'
                    ? 'text-foreground border-b-2 border-primary'
                    : 'text-muted-foreground hover:text-foreground'
                )}
              >
                Quick Select
              </button>
              <button
                onClick={() => setActiveTab('custom')}
                className={cn(
                  'flex-1 px-4 py-2 text-sm font-medium',
                  activeTab === 'custom'
                    ? 'text-foreground border-b-2 border-primary'
                    : 'text-muted-foreground hover:text-foreground'
                )}
              >
                Custom Range
              </button>
            </div>
            
            {activeTab === 'presets' ? (
              <div className="p-2 grid grid-cols-2 gap-1 max-h-72 overflow-y-auto">
                {presets.map(preset => (
                  <button
                    key={preset.value}
                    onClick={() => handlePresetSelect(preset.value)}
                    className={cn(
                      'px-3 py-2 text-sm text-left rounded-md',
                      'hover:bg-muted transition-colors',
                      value.label === preset.value && 'bg-primary/10 text-primary'
                    )}
                  >
                    {preset.label}
                  </button>
                ))}
              </div>
            ) : (
              <div className="p-4 space-y-4">
                <div>
                  <label 
                    htmlFor="custom-start"
                    className="block text-sm font-medium mb-1"
                  >
                    Start
                  </label>
                  <input
                    id="custom-start"
                    type="datetime-local"
                    value={customStart}
                    onChange={e => setCustomStart(e.target.value)}
                    className="w-full px-3 py-2 border rounded-md bg-background text-sm"
                  />
                </div>
                
                <div>
                  <label 
                    htmlFor="custom-end"
                    className="block text-sm font-medium mb-1"
                  >
                    End
                  </label>
                  <input
                    id="custom-end"
                    type="datetime-local"
                    value={customEnd}
                    onChange={e => setCustomEnd(e.target.value)}
                    className="w-full px-3 py-2 border rounded-md bg-background text-sm"
                  />
                </div>
                
                <button
                  onClick={handleCustomApply}
                  disabled={!customStart || !customEnd}
                  className={cn(
                    'w-full px-4 py-2 rounded-md text-sm font-medium',
                    'bg-primary text-primary-foreground',
                    'hover:bg-primary/90 transition-colors',
                    'disabled:opacity-50 disabled:cursor-not-allowed'
                  )}
                >
                  Apply
                </button>
              </div>
            )}
          </div>
        </>
      )}
    </div>
  );
};

export default TimeRangePicker;
