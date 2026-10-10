import { useCallback, useMemo, useEffect, useRef } from 'react';
import { useForm } from 'react-hook-form';
import type { AsignarMemberShips } from '@/model/asignarMemberShips.model';
import type { Miembro } from '@/model/member.model';
import type { FormData } from '@/types/MemberFormTypes';
import { formatDateForInput } from '../../utils/dateUtils';

interface UseMemberFormUIStateParams {
    // Data hook
    asignacion: AsignarMemberShips | null;
    miembros: Miembro[];

    // validation hook
    watch: ReturnType<typeof useForm<FormData>>['watch'];
    isEditing: boolean;

    // pricing hook
    discountPercent: number;    
};

const useMemberFormUIState = ({
    asignacion,
    miembros,
    watch,
    isEditing,
    discountPercent,    
}: UseMemberFormUIStateParams) => {
        // Compute editing values and membership status
    const editingMembresiaId = useMemo(() => {
        if (!asignacion) return '';
        const membresiaId = asignacion.membresia?.id ?? asignacion.membresia_details?.id;
        return membresiaId?.toString() ?? '';
    }, [asignacion]);

    const editingDateInitial = useMemo(() => {
        if (!asignacion) return '';
        return formatDateForInput(asignacion.dateInitial);
    }, [asignacion]);

    const isMembershipActive = useMemo(() => {
        if (!asignacion) return false;
        const today = new Date();
        today.setHours(0, 0, 0, 0);
        const dateFinal = new Date(asignacion.dateFinal);
        dateFinal.setHours(0, 0, 0, 0);
        // Active if dateFinal >= today AND not fully paid
        return dateFinal >= today && asignacion.estado_pago !== 'paid';
    }, [asignacion]);

    // ============ DIRTY TRACKING ============
    // Track initial values from asignacion for dirty comparison
    const initialValuesRef = useRef<{
        member: { name: string; lastname: string; phone: string; address: string };
        assignment: { membresia: string; dateInitial: string; multiplier: number; discount_percent: number };
    } | null>(null);

    const computeInitialValues = useCallback(() => {
        if (!asignacion) return;

        const memberDetails = asignacion.miembro_details;
        const currentMiembro = miembros.find(m => m.id === (asignacion.miembro?.id ?? asignacion.miembro_details?.id));

        initialValuesRef.current = {
            member: {
                name: memberDetails?.name ?? currentMiembro?.name ?? '',
                lastname: memberDetails?.lastname ?? currentMiembro?.lastname ?? '',
                phone: currentMiembro?.phone ?? '',
                address: currentMiembro?.address ?? '',
            },
            assignment: {
                membresia: (asignacion.membresia?.id ?? asignacion.membresia_details?.id)?.toString() ?? '',
                dateInitial: formatDateForInput(asignacion.dateInitial),
                multiplier: Number(asignacion.multiplier) || 1,
                discount_percent: Number(asignacion.discount_percent) || 0,
            },
        };
    }, [asignacion, miembros]);

    // Update initial values when asignacion loads
    useEffect(() => {
        computeInitialValues();
    }, [computeInitialValues]);

    // watch() without args returns all form values and subscribes to all changes
    const formValues = watch();

    const memberDirty = useMemo(() => {
        if (!initialValuesRef.current || !isEditing) return false;

        const currentName = formValues?.nuevoName ?? '';
        const currentLastname = formValues?.nuevoLastname ?? '';
        const currentPhone = formValues?.nuevoPhone ?? '';
        const currentAddress = formValues?.nuevoAddress ?? '';

        const { name, lastname, phone, address } = initialValuesRef.current.member;

        return (
            currentName !== name ||
            currentLastname !== lastname ||
            currentPhone !== phone ||
            currentAddress !== address
        );
    }, [formValues, isEditing]);

    const assignmentDirty = useMemo(() => {
        if (!initialValuesRef.current || !isEditing) return false;

        const currentMembresia = formValues?.membresia ?? '';
        const currentDateInitial = formValues?.dateInitial ?? '';
        const currentMultiplier = parseInt(formValues?.multiplier ?? '1', 10);
        const currentDiscount = discountPercent;

        const { membresia, dateInitial, multiplier, discount_percent } = initialValuesRef.current.assignment;

        return (
            currentMembresia !== membresia ||
            currentDateInitial !== dateInitial ||
            currentMultiplier !== multiplier ||
            currentDiscount !== discount_percent
        );
    }, [formValues, discountPercent, isEditing]);

    // Can edit assignment only when estado_pago === 'pending'
    const canEditAssignment = useMemo(() => {
        if (!asignacion) return true; // New assignments are always editable
        return asignacion.estado_pago === 'pending';
    }, [asignacion]);
    
    
    return {

        // Editing values (for display in disabled fields)
        editingMembresiaId,
        editingDateInitial,
        isMembershipActive,
        
        // Dirty tracking
        memberDirty,
        assignmentDirty,

        // Editability
        canEditAssignment,

        initialValuesRef,
        computeInitialValues
    
    }
}
export default useMemberFormUIState;