import { useEffect, useState, useCallback } from 'react';
import { getMemberList } from '../api/action/memberShips.api';
import { getMembers } from '../api/action/userGym.api';
import { getAsignarMemberShips } from '../api/action/asignarMemberShips.api';
import type { Membresia } from '../model/memberShips.model';
import type { Miembro } from '../model/member.model';
import type { AsignarMemberShips } from '../model/asignarMemberShips.model';
import { filterActiveMemberships, mergeCurrentMembership } from '../utils/membershipUtils';
import { formatDateForInput } from '../utils/dateUtils';

export interface UseMemberFormDataReturn {
  membresias: Membresia[];
  miembros: Miembro[];
  asignacion: AsignarMemberShips | null;
  loading: boolean;
  error: string | null;
  refetch: () => Promise<void>;
}

interface UseMemberFormDataParams {
  id?: string;
}

export function useMemberFormData({ id }: UseMemberFormDataParams): UseMemberFormDataReturn {
  const [membresias, setMembresias] = useState<Membresia[]>([]);
  const [miembros, setMiembros] = useState<Miembro[]>([]);
  const [asignacion, setAsignacion] = useState<AsignarMemberShips | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const fetchData = useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      // Fetch memberships and members in parallel
      const [membresiasResponse, miembrosResponse] = await Promise.all([
        getMemberList(),
        getMembers(),
      ]);

      // Filter active memberships only
      let activeMembresias = filterActiveMemberships(membresiasResponse);

      // If editing, fetch the assignment
      if (id) {
        const asignacionResponse = await getAsignarMemberShips(parseInt(id, 10));

        // Extract current membership from assignment (membresia_details or membresia)
        const currentMembership = (asignacionResponse.membresia_details ?? asignacionResponse.membresia) as Membresia | null;

        // Merge current membership into the list if it's inactive/filtered out
        activeMembresias = mergeCurrentMembership(activeMembresias, currentMembership);

        // Format dates from API (DD-MM-YYYY or DD/MM/YYYY) to input format (YYYY-MM-DD)
        const formattedAsignacion = {
          ...asignacionResponse,
          dateInitial: formatDateForInput(asignacionResponse.dateInitial),
          dateFinal: formatDateForInput(asignacionResponse.dateFinal),
        };

        setAsignacion(formattedAsignacion);
      }

      setMembresias(activeMembresias);
      setMiembros(miembrosResponse);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Error al cargar los datos';
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  }, [id]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const refetch = useCallback(async () => {
    await fetchData();
  }, [fetchData]);

  return {
    membresias,
    miembros,
    asignacion,
    loading,
    error,
    refetch,
  };
}