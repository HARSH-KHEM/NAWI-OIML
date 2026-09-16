import { clsx, type ClassValue } from 'clsx'
import { twMerge } from 'tailwind-merge'

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

export function formatDateSafe(dateString?: string | null): string {
  if (!dateString) return '—'
  try {
    const d = new Date(dateString)
    if (isNaN(d.getTime())) return String(dateString)
    const year = d.getUTCFullYear()
    const month = String(d.getUTCMonth() + 1).padStart(2, '0')
    const day = String(d.getUTCDate()).padStart(2, '0')
    return `${day}/${month}/${year}`
  } catch {
    return String(dateString)
  }
}

export function formatDateTimeSafe(dateString?: string | null): string {
  if (!dateString) return '—'
  try {
    const d = new Date(dateString)
    if (isNaN(d.getTime())) return String(dateString)
    const year = d.getUTCFullYear()
    const month = String(d.getUTCMonth() + 1).padStart(2, '0')
    const day = String(d.getUTCDate()).padStart(2, '0')
    const hours = String(d.getUTCHours()).padStart(2, '0')
    const minutes = String(d.getUTCMinutes()).padStart(2, '0')
    return `${day}/${month}/${year} ${hours}:${minutes} UTC`
  } catch {
    return String(dateString)
  }
}

