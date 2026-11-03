import type { AuditEntry } from './api/adminClient'

const COLUMNS: (keyof AuditEntry)[] = ['at', 'actor', 'action', 'target', 'outcome', 'detail']

const cell = (value: string) => {
  const safe = /^[=+\-@\t\r]/.test(value) ? `'${value}` : value
  return `"${safe.replaceAll('"', '""')}"`
}

export const auditCsv = (rows: AuditEntry[]) =>
  [COLUMNS.join(','), ...rows.map((row) => COLUMNS.map((column) => cell(String(row[column]))).join(','))].join('\r\n')
