import type { QueryKey } from '@tanstack/react-query';

/**
 * TanStack Query key factory for ControlFit
 * Centralized keys for cache invalidation and type safety
 */

// ============================================
// KEY FACTORY PATTERN
// ============================================

const queryKeys = {
  // Root keys by domain
  memberships: {
    all: ['memberships'] as const,
    lists: () => [...queryKeys.memberships.all, 'list'] as const,
    list: (filters: Record<string, unknown>) => [...queryKeys.memberships.lists(), filters] as const,
    details: () => [...queryKeys.memberships.all, 'detail'] as const,
    detail: (id: string) => [...queryKeys.memberships.details(), id] as const,
    assigned: (memberId: string) => ['memberships', 'assigned', memberId] as const,
    expiring: (days: number, gymId: string) => ['memberships', 'expiring', days, gymId] as const,
  },

  payments: {
    all: ['payments'] as const,
    lists: () => [...queryKeys.payments.all, 'list'] as const,
    list: (membershipId: string, filters?: Record<string, unknown>) => 
      [...queryKeys.payments.lists(), membershipId, filters] as const,
    detail: (id: string) => [...queryKeys.payments.all, 'detail', id] as const,
    byMember: (memberId: string) => ['payments', 'member', memberId] as const,
  },

  members: {
    all: ['members'] as const,
    lists: () => [...queryKeys.members.all, 'list'] as const,
    list: (gymId: string, filters?: Record<string, unknown>) => 
      [...queryKeys.members.lists(), gymId, filters] as const,
    detail: (id: string) => [...queryKeys.members.all, 'detail', id] as const,
    search: (gymId: string, query: string) => ['members', 'search', gymId, query] as const,
  },

  notifications: {
    all: ['notifications'] as const,
    unread: (gymId: string) => ['notifications', 'unread', gymId] as const,
    count: (gymId: string) => ['notifications', 'count', gymId] as const,
  },

  gym: {
    all: ['gym'] as const,
    current: () => [...queryKeys.gym.all, 'current'] as const,
    settings: (gymId: string) => ['gym', 'settings', gymId] as const,
  },

  // Generic helpers
  createListKey: <T extends Record<string, unknown>>(domain: string, filters?: T) => 
    filters ? [domain, 'list', filters] as const : [domain, 'list'] as const,
  
  createDetailKey: (domain: string, id: string) => 
    [domain, 'detail', id] as const,
} as const;

// ============================================
// TYPE EXPORTS
// ============================================

export type MembershipQueryKeys = typeof queryKeys.memberships;
export type PaymentQueryKeys = typeof queryKeys.payments;
export type MemberQueryKeys = typeof queryKeys.members;
export type NotificationQueryKeys = typeof queryKeys.notifications;
export type GymQueryKeys = typeof queryKeys.gym;

// ============================================
// INVALIDATION HELPERS
// ============================================

export const invalidationKeys = {
  // Invalidate all membership queries
  allMemberships: () => queryKeys.memberships.all,
  
  // Invalidate specific membership + related
  membership: (id: string) => [
    queryKeys.memberships.detail(id),
    queryKeys.memberships.assigned('*'), // wildcard for all members
  ],
  
  // Invalidate payments for a membership
  membershipPayments: (membershipId: string) => [
    queryKeys.payments.byMember('*'), // will match all
    queryKeys.payments.list(membershipId),
  ],
  
  // Invalidate member-related queries
  member: (memberId: string) => [
    queryKeys.members.detail(memberId),
    queryKeys.memberships.assigned(memberId),
    queryKeys.payments.byMember(memberId),
  ],
  
  // Invalidate notifications
  notifications: (gymId: string) => [
    queryKeys.notifications.unread(gymId),
    queryKeys.notifications.count(gymId),
  ],
} as const;

export default queryKeys;