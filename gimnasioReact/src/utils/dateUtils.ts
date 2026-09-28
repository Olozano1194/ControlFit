/**
 * Date utility functions for MemberForm
 * Uses date-fns with Spanish locale
 */
import { addDays, isValid, parse } from 'date-fns';

/**
 * Calculates the estimated final date by adding totalDays to the initial date
 * Returns formatted date in DD/MM/YYYY format for display
 *
 * @param dateInitial - Initial date in YYYY-MM-DD format (from date input)
 * @param totalDays - Total number of days to add
 * @returns Formatted date string in DD/MM/YYYY format, or empty string if invalid
 */
export function calculateEstimatedDateFinal(
  dateInitial: string,
  totalDays: number
): string {
  if (!dateInitial || !isValid(parse(dateInitial, 'yyyy-MM-dd', new Date()))) {
    return '';
  }

  if (typeof totalDays !== 'number' || isNaN(totalDays) || totalDays < 0) {
    return '';
  }

  const initialDate = parse(dateInitial, 'yyyy-MM-dd', new Date());
  const finalDate = addDays(initialDate, totalDays);

  // Format as DD/MM/YYYY for display
  const day = String(finalDate.getDate()).padStart(2, '0');
  const month = String(finalDate.getMonth() + 1).padStart(2, '0');
  const year = finalDate.getFullYear();

  return `${day}/${month}/${year}`;
}

/**
 * Converts API date (DD-MM-YYYY, DD/MM/YYYY, or YYYY-MM-DD) to HTML input date format (YYYY-MM-DD)
 * Handles multiple formats from backend
 *
 * @param apiDate - Date string in various formats
 * @returns Date string in YYYY-MM-DD format, or empty string if invalid
 */
export function parseApiDateToInput(apiDate: string): string {
  if (!apiDate) return '';

  try {
    // If already in YYYY-MM-DD format (ISO), return as-is
    if (/^\d{4}-\d{2}-\d{2}$/.test(apiDate)) {
      const date = parse(apiDate, 'yyyy-MM-dd', new Date());
      return isValid(date) ? apiDate : '';
    }

    // Otherwise assume DD/MM/YYYY or DD-MM-YYYY
    const separator = apiDate.includes('/') ? '/' : '-';
    const [day, month, year] = apiDate.split(separator);
    if (!day || !month || !year) return '';

    const normalized = `${year}-${month.padStart(2, '0')}-${day.padStart(2, '0')}`;
    const date = parse(normalized, 'yyyy-MM-dd', new Date());
    return isValid(date) ? normalized : '';
  } catch {
    return '';
  }
}

/**
 * Converts HTML input date format (YYYY-MM-DD) to display format (DD/MM/YYYY)
 *
 * @param inputDate - Date string in YYYY-MM-DD format
 * @returns Date string in DD/MM/YYYY format, or empty string if invalid
 */
export function formatDateForDisplay(inputDate: string): string {
  if (!inputDate) return '';

  try {
    const [year, month, day] = inputDate.split('-');
    if (!year || !month || !day) return '';

    // Validate it's a valid date
    const date = parse(inputDate, 'yyyy-MM-dd', new Date());
    if (!isValid(date)) return '';

    return `${day.padStart(2, '0')}/${month.padStart(2, '0')}/${year}`;
  } catch {
    return '';
  }
}

/**
 * Legacy alias for backward compatibility
 * @deprecated Use parseApiDateToInput instead
 */
export const formatDateForInput = parseApiDateToInput;