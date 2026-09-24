/**
 * Formatting utilities for MemberForm
 */

/**
 * Formats a number as Colombian Pesos (COP) using Intl.NumberFormat
 * Uses es-CO locale, COP currency, 0 decimal places
 *
 * @param amount - The amount to format
 * @returns Formatted currency string (e.g., "$1.000.000")
 */
export function formatCurrencyCOP(amount: number): string {
  return new Intl.NumberFormat('es-CO', {
    style: 'currency',
    currency: 'COP',
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  }).format(amount);
}