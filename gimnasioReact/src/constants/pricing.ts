// Pricing constants for MemberForm

/**
 * Discount tiers based on number of periods (multiplier)
 * Key = multiplier (number of months), Value = discount percentage
 */
export const DISCOUNT_TIERS = {
  1: 0,
  2: 0,
  3: 5,
  6: 10,
  12: 20,
} as const;

/**
 * Default multiplier when no membership is selected or on reset
 */
export const DEFAULT_MULTIPLIER = 1;

/**
 * Default discount percentage when no membership is selected or on reset
 */
export const DEFAULT_DISCOUNT = 0;