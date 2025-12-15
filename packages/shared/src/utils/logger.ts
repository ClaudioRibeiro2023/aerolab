/**
 * Structured Logger
 *
 * Provides consistent logging across the application with support for
 * different log levels and structured metadata.
 */

export type LogLevel = 'debug' | 'info' | 'warn' | 'error'

export interface LogEntry {
  level: LogLevel
  message: string
  timestamp: string
  context?: string
  data?: Record<string, unknown>
}

export interface LoggerOptions {
  context?: string
  enabled?: boolean
  minLevel?: LogLevel
}

const LOG_LEVELS: Record<LogLevel, number> = {
  debug: 0,
  info: 1,
  warn: 2,
  error: 3,
}

// Check if we're in production
const IS_PRODUCTION =
  typeof window !== 'undefined'
    ? window.location.hostname !== 'localhost' && !window.location.hostname.includes('127.0.0.1')
    : false

// Default minimum level based on environment
const DEFAULT_MIN_LEVEL: LogLevel = IS_PRODUCTION ? 'warn' : 'debug'

/**
 * Logger class for structured logging
 */
class Logger {
  private context?: string
  private enabled: boolean
  private minLevel: LogLevel

  constructor(options: LoggerOptions = {}) {
    this.context = options.context
    this.enabled = options.enabled ?? true
    this.minLevel = options.minLevel ?? DEFAULT_MIN_LEVEL
  }

  private shouldLog(level: LogLevel): boolean {
    if (!this.enabled) return false
    return LOG_LEVELS[level] >= LOG_LEVELS[this.minLevel]
  }

  private formatMessage(
    level: LogLevel,
    message: string,
    data?: Record<string, unknown>
  ): LogEntry {
    return {
      level,
      message,
      timestamp: new Date().toISOString(),
      context: this.context,
      data,
    }
  }

  private output(entry: LogEntry): void {
    const prefix = entry.context ? `[${entry.context}]` : ''
    const msg = `${prefix} ${entry.message}`

    switch (entry.level) {
      case 'debug':
        // eslint-disable-next-line no-console
        console.debug(msg, entry.data ?? '')
        break
      case 'info':
        // eslint-disable-next-line no-console
        console.info(msg, entry.data ?? '')
        break
      case 'warn':
        // eslint-disable-next-line no-console
        console.warn(msg, entry.data ?? '')
        break
      case 'error':
        // eslint-disable-next-line no-console
        console.error(msg, entry.data ?? '')
        break
    }
  }

  debug(message: string, data?: Record<string, unknown>): void {
    if (this.shouldLog('debug')) {
      this.output(this.formatMessage('debug', message, data))
    }
  }

  info(message: string, data?: Record<string, unknown>): void {
    if (this.shouldLog('info')) {
      this.output(this.formatMessage('info', message, data))
    }
  }

  warn(message: string, data?: Record<string, unknown>): void {
    if (this.shouldLog('warn')) {
      this.output(this.formatMessage('warn', message, data))
    }
  }

  error(message: string, data?: Record<string, unknown>): void {
    if (this.shouldLog('error')) {
      this.output(this.formatMessage('error', message, data))
    }
  }

  /**
   * Create a child logger with a specific context
   */
  child(context: string): Logger {
    return new Logger({
      context: this.context ? `${this.context}:${context}` : context,
      enabled: this.enabled,
      minLevel: this.minLevel,
    })
  }
}

// Default logger instance
export const logger = new Logger()

// Create context-specific loggers
export const createLogger = (context: string, options?: Omit<LoggerOptions, 'context'>): Logger => {
  return new Logger({ ...options, context })
}

// Pre-configured loggers for common contexts
export const authLogger = createLogger('Auth')
export const apiLogger = createLogger('API')
export const appLogger = createLogger('App')
