/**
 * Pricing calculation utilities for MemberForm
 */

/**
 * Calculates the estimated price based on base price, multiplier, and discount percentage
 * Formula: base * multiplier * (1 - discountPercent / 100)
 *
 * @param price - Base price of the membership
 * @param multiplier - Number of periods (months)
 * @param discountPercent - Discount percentage (0-100)
 * @returns Estimated price after applying multiplier and discount
 */
export function calculateEstimatedPrice(
  price: number,
  multiplier: number,
  discountPercent: number
): number {
  return price * multiplier * (1 - discountPercent / 100);
}

/**
 * Calculates total days based on membership duration and multiplier
 *
 * @param duration - Duration of membership in days (per period)
 * @param multiplier - Number of periods
 * @returns Total days
 */
export function calculateTotalDays(duration: number, multiplier: number): number {
  return duration * multiplier;
}