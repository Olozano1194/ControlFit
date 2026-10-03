/**
 * Membership utility functions for MemberForm
 */

import type { Membresia } from '../model/memberShips.model';

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

/**
 * Merges current membership into the memberships list if it's missing.
 * Used in edit mode to ensure the currently assigned membership is available
 * for selection even if it's inactive (filtered out by filterActiveMemberships).
 *
 * @param memberships - Array of active memberships
 * @param currentMembership - The membership currently assigned to the member (may be inactive)
 * @returns Union by id, preserving current membership if missing from active list
 */
export function mergeCurrentMembership(
  memberships: Membresia[],
  currentMembership: Membresia | null
): Membresia[] {
  if (!currentMembership) return memberships;

  const hasCurrent = memberships.some(m => m.id === currentMembership.id);
  if (hasCurrent) return memberships;

  // Current membership not in active list - prepend it
  return [currentMembership, ...memberships];
}