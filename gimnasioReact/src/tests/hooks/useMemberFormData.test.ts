import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { renderHook, waitFor, act } from '@testing-library/react';
import { useMemberFormData } from '../../hooks/useMemberFormData';
import type { Membresia } from '../../model/memberShips.model';
import type { Miembro } from '../../model/member.model';
import type { AsignarMemberShips } from '../../model/asignarMemberShips.model';

// Mock the API modules
vi.mock('../../api/action/memberShips.api', () => ({
  getMemberList: vi.fn(),
}));

vi.mock('../../api/action/userGym.api', () => ({
  getMembers: vi.fn(),
}));

vi.mock('../../api/action/asignarMemberShips.api', () => ({
  getAsignarMemberShips: vi.fn(),
}));

import { getMemberList } from '../../api/action/memberShips.api';
import { getMembers } from '../../api/action/userGym.api';
import { getAsignarMemberShips } from '../../api/action/asignarMemberShips.api';

const mockMembresias: Membresia[] = [
  { id: 1, name: 'Basic', price: 10000, duration: 30, max_multiplier: 12, is_active: true, gimnasio: 1 },
  { id: 2, name: 'Premium', price: 20000, duration: 30, max_multiplier: 12, is_active: true, gimnasio: 1 },
  { id: 3, name: 'Inactive', price: 5000, duration: 30, max_multiplier: 6, is_active: false, gimnasio: 1 },
];

const mockMiembros: Miembro[] = [
  { id: 1, name: 'John', lastname: 'Doe', phone: '1234567890', address: '123 St' },
  { id: 2, name: 'Jane', lastname: 'Smith', phone: '0987654321', address: '456 Ave' },
];

const mockAsignacion: AsignarMemberShips = {
  id: 1,
  miembro: mockMiembros[0],
  membresia: mockMembresias[0],
  dateInitial: '15-01-2024',
  dateFinal: '14-02-2024',
  name: 'Basic',
  price: '10000',
  multiplier: '3',
  discount_percent: '5',
  total_pagado: '28500',
  saldo_pendiente: '0',
  estado_pago: 'paid',
  miembro_details: { id: 1, name: 'John', lastname: 'Doe' },
  membresia_details: { id: 1, name: 'Basic', price: 10000 },
};

// Expected active memberships (filtered)
const expectedActiveMembresias = mockMembresias.filter(m => m.is_active === true);

describe('useMemberFormData', () => {
  beforeEach(() => {
    vi.resetAllMocks();
  });

  afterEach(() => {
    vi.clearAllMocks();
  });

  describe('initial state', () => {
    it('should return empty arrays and loading true initially', () => {
      const { result } = renderHook(() => useMemberFormData({ id: undefined }));

      expect(result.current.membresias).toEqual([]);
      expect(result.current.miembros).toEqual([]);
      expect(result.current.asignacion).toBeNull();
      expect(result.current.loading).toBe(true);
      expect(result.current.error).toBeNull();
    });
  });

  describe('fetch data (create mode)', () => {
    it('should fetch membresias and miembros in parallel', async () => {
      (getMemberList as vi.Mock).mockResolvedValue(mockMembresias);
      (getMembers as vi.Mock).mockResolvedValue(mockMiembros);
      (getAsignarMemberShips as vi.Mock).mockRejectedValue(new Error('Not found'));

      const { result } = renderHook(() => useMemberFormData({ id: undefined }));

      await waitFor(() => expect(result.current.loading).toBe(false), { timeout: 3000 });

      expect(getMemberList).toHaveBeenCalledTimes(1);
      expect(getMembers).toHaveBeenCalledTimes(1);
      expect(getAsignarMemberShips).not.toHaveBeenCalled();

      // Should filter to only active memberships
      expect(result.current.membresias).toEqual(expectedActiveMembresias);
      expect(result.current.miembros).toEqual(mockMiembros);
      expect(result.current.asignacion).toBeNull();
      expect(result.current.error).toBeNull();
    });

    it('should filter out inactive membresias', async () => {
      (getMemberList as vi.Mock).mockResolvedValue(mockMembresias);
      (getMembers as vi.Mock).mockResolvedValue(mockMiembros);

      const { result } = renderHook(() => useMemberFormData({ id: undefined }));

      await waitFor(() => expect(result.current.loading).toBe(false), { timeout: 3000 });

      // Should only have active memberships (is_active === true)
      expect(result.current.membresias).toHaveLength(2);
      expect(result.current.membresias.every(m => m.is_active === true)).toBe(true);
      expect(result.current.membresias).toEqual(expectedActiveMembresias);
    });
  });

  describe('fetch data (edit mode)', () => {
    it('should fetch asignacion when id provided', async () => {
      (getMemberList as vi.Mock).mockResolvedValue(mockMembresias);
      (getMembers as vi.Mock).mockResolvedValue(mockMiembros);
      (getAsignarMemberShips as vi.Mock).mockResolvedValue(mockAsignacion);

      const { result } = renderHook(() => useMemberFormData({ id: '1' }));

      await waitFor(() => expect(result.current.loading).toBe(false), { timeout: 3000 });

      expect(getAsignarMemberShips).toHaveBeenCalledWith(1);
      // Note: hook formats dates, so they won't match original mockAsignacion exactly
      expect(result.current.asignacion).not.toBeNull();
      expect(result.current.asignacion?.id).toBe(1);
    });

    it('should format dates from API format (DD-MM-YYYY) to input format (YYYY-MM-DD)', async () => {
      (getMemberList as vi.Mock).mockResolvedValue(mockMembresias);
      (getMembers as vi.Mock).mockResolvedValue(mockMiembros);
      (getAsignarMemberShips as vi.Mock).mockResolvedValue({
        ...mockAsignacion,
        dateInitial: '15-01-2024', // DD-MM-YYYY
        dateFinal: '14-02-2024',
      });

      const { result } = renderHook(() => useMemberFormData({ id: '1' }));

      await waitFor(() => expect(result.current.loading).toBe(false), { timeout: 3000 });

      // The hook should format dates for input (YYYY-MM-DD)
      expect(result.current.asignacion?.dateInitial).toBe('2024-01-15');
      expect(result.current.asignacion?.dateFinal).toBe('2024-02-14');
    });

    it('should handle date format with slashes (DD/MM/YYYY)', async () => {
      (getMemberList as vi.Mock).mockResolvedValue(mockMembresias);
      (getMembers as vi.Mock).mockResolvedValue(mockMiembros);
      (getAsignarMemberShips as vi.Mock).mockResolvedValue({
        ...mockAsignacion,
        dateInitial: '15/01/2024',
        dateFinal: '14/02/2024',
      });

      const { result } = renderHook(() => useMemberFormData({ id: '1' }));

      await waitFor(() => expect(result.current.loading).toBe(false), { timeout: 3000 });

      expect(result.current.asignacion?.dateInitial).toBe('2024-01-15');
      expect(result.current.asignacion?.dateFinal).toBe('2024-02-14');
    });
  });

  describe('error handling', () => {
    it('should set error state when fetch fails', async () => {
      (getMemberList as vi.Mock).mockRejectedValue(new Error('Network error'));
      (getMembers as vi.Mock).mockResolvedValue(mockMiembros);

      const { result } = renderHook(() => useMemberFormData({ id: undefined }));

      await waitFor(() => expect(result.current.loading).toBe(false), { timeout: 3000 });

      expect(result.current.error).toBe('Network error');
      expect(result.current.membresias).toEqual([]);
    });

    it('should set error when getAsignarMemberShips fails', async () => {
      (getMemberList as vi.Mock).mockResolvedValue(mockMembresias);
      (getMembers as vi.Mock).mockResolvedValue(mockMiembros);
      (getAsignarMemberShips as vi.Mock).mockRejectedValue(new Error('Not found'));

      const { result } = renderHook(() => useMemberFormData({ id: '999' }));

      await waitFor(() => expect(result.current.loading).toBe(false), { timeout: 3000 });

      expect(result.current.error).toBe('Not found');
    });
  });

  describe('refetch', () => {
    it('should refetch data when refetch is called', async () => {
      (getMemberList as vi.Mock).mockResolvedValue(mockMembresias);
      (getMembers as vi.Mock).mockResolvedValue(mockMiembros);

      const { result } = renderHook(() => useMemberFormData({ id: undefined }));

      await waitFor(() => expect(result.current.loading).toBe(false), { timeout: 3000 });

      // Change mock data - include new active membership
      const newMembresias = [...mockMembresias, { id: 4, name: 'VIP', price: 30000, duration: 30, max_multiplier: 12, is_active: true, gimnasio: 1 }];
      (getMemberList as vi.Mock).mockResolvedValue(newMembresias);

      await act(async () => {
        await result.current.refetch();
      });

      expect(getMemberList).toHaveBeenCalledTimes(2);
      // Should filter to only active memberships
      expect(result.current.membresias).toHaveLength(3); // Basic, Premium, VIP
    });
  });

  describe('stable dependencies', () => {
    it('should have refetch function available', () => {
      (getMemberList as vi.Mock).mockResolvedValue(mockMembresias);
      (getMembers as vi.Mock).mockResolvedValue(mockMiembros);

      const { result } = renderHook(() => useMemberFormData({ id: '1' }));

      // The hook should be stable - we can't easily test internal useCallback
      // but we can verify the hook returns expected data
      expect(result.current.refetch).toBeDefined();
      expect(typeof result.current.refetch).toBe('function');
    });
  });
});