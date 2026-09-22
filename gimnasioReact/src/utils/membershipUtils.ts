/**
 * Membership utility functions for MemberForm
 */

/**
 * Generates an array of multiplier options from 1 to maxMultiplier (inclusive)
 *
 * @param maxMultiplier - Maximum multiplier value
 * @returns Array of numbers from 1 to maxMultiplier, empty array if maxMultiplier < 1
 */
export function generateMultiplierOptions(maxMultiplier: number): number[] {
  if (maxMultiplier < 1) return [];
  return Array.from({ length: maxMultiplier }, (_, i) => i + 1);
}

/**
 * Filters memberships to return only active ones (is_active === true)
 * Excludes memberships where is_active is false or undefined
 *
 * @param memberships - Array of memberships
 * @returns Array of active memberships
 */
export function filterActiveMemberships<T extends { is_active?: boolean }>(memberships: T[]): T[] {
  return memberships.filter(m => m.is_active === true);
}