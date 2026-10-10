import { useCallback, type MutableRefObject } from 'react';
import { toast } from 'react-hot-toast';
import { type ModoFormulario } from '../../schemas/memberFormSchemas';
import type { FormData, Miembro } from '../../types/MemberFormTypes';
import type { Membresia } from '../../model/memberShips.model';
import type { AsignarMemberShips } from '../../model/asignarMemberShips.model';
import { createMember, updateMember } from '../../api/action/userGym.api';
import { updateAsignarMemberShips } from '../../api/action/asignarMemberShips.api';
import type { CreateMemberDto } from '../../model/dto/member.dto';
import type { CreateAsignarMemberShipsDto } from '../../model/dto/asignarMemberShips.dto';
import { formatDateForInput } from '../../utils/dateUtils';


interface UseMemberFormActionsParams {
    // Data
    miembros: Miembro[];
    membresias: Membresia[];
    asignacion: AsignarMemberShips | null;

    // Mode
    modo: ModoFormulario;
    setModo: (modo: ModoFormulario) => void;

    // State
    multiplier: number;
    discountPercent: number;
    setMultiplier: (val: number) => void;
    setDiscountPercent: (val: number) => void;
    setSelectedMembresia: (membresia: Membresia | null) => void;
    setDateInitial: (date: string) => void;

    // UI State
    memberDirty: boolean;
    assignmentDirty: boolean;
    canEditAssignment: boolean;
    initialValuesRef: MutableRefObject<{
        member: { name: string; lastname: string; phone: string; address: string };
        assignment: { membresia: string; dateInitial: string; multiplier: number; discount_percent: number };
    } | null>;

    // Form helpers (una sola instancia del orquestador)
    setValue: ReturnType<typeof import('react-hook-form').useForm<FormData>>['setValue'];
    reset: ReturnType<typeof import('react-hook-form').useForm<FormData>>['reset'];

    // router
    params: { id?: string };
    navigate: (path: string) => void;
}

const useMemberFormActions = ({
    asignacion,
    modo,
    setModo,
    membresias,
    miembros,
    multiplier,
    discountPercent,
    setMultiplier,
    setDiscountPercent,
    setSelectedMembresia,
    setDateInitial,
    setValue,
    reset,
    memberDirty,
    assignmentDirty,
    canEditAssignment,
    initialValuesRef,
    params,
    navigate,
}: UseMemberFormActionsParams) => {


    const handleMultiplierChange = useCallback(
        (event: React.ChangeEvent<HTMLSelectElement>) => {
            const val = parseInt(event.target.value, 10);
            setMultiplier(val);
            setValue('multiplier', String(val), { shouldValidate: true });
        },
        [setMultiplier, setValue]
    );

    const handleMemberShipsChange = useCallback(
        (event: React.ChangeEvent<HTMLSelectElement>) => {
            const membresiaId = parseInt(event.target.value, 10);
            const found = membresias.find((m) => m.id === membresiaId);
            setSelectedMembresia(found ?? null);
            setValue('membresia', String(membresiaId), { shouldValidate: true });
        },
        [membresias, setSelectedMembresia, setValue]
    );

    const setModoCallback = useCallback(
        (newModo: ModoFormulario) => {
            setModo(newModo);
            reset(undefined, { keepValues: false });
            setSelectedMembresia(null);
            setMultiplier(1);
            setDiscountPercent(0);
        },
        [setModo, reset, setSelectedMembresia, setMultiplier, setDiscountPercent]
    );

    const initializeFormFromAsignacion = useCallback(() => {
        if (asignacion) {
            // Use .id from the nested objects, not .toString() on the whole object
            const miembroId = asignacion.miembro?.id ?? asignacion.miembro_details?.id;
            const membresiaId = asignacion.membresia?.id ?? asignacion.membresia_details?.id;

            // Get member details for editing (name, lastname, phone, address)
            const memberDetails = asignacion.miembro_details;
            const currentMiembro = miembros.find(m => m.id === miembroId);

            reset({
                miembro: miembroId?.toString() ?? '',
                membresia: membresiaId?.toString() ?? '',
                multiplier: asignacion.multiplier?.toString() ?? '1',
                dateInitial: formatDateForInput(asignacion.dateInitial),
                // Member detail fields for editing
                nuevoName: memberDetails?.name ?? currentMiembro?.name ?? '',
                nuevoLastname: memberDetails?.lastname ?? currentMiembro?.lastname ?? '',
                nuevoPhone: currentMiembro?.phone ?? '',
                nuevoAddress: currentMiembro?.address ?? '',
            });

            // Asegurar que initialValuesRef.current existe y actualizarlo sincronizado con el reset
            if (!initialValuesRef.current) {
                initialValuesRef.current = {
                    member: { name: '', lastname: '', phone: '', address: '' },
                    assignment: { membresia: '', dateInitial: '', multiplier: 1, discount_percent: 0 },
                };
            }
            initialValuesRef.current.member = {
                name: memberDetails?.name ?? currentMiembro?.name ?? '',
                lastname: memberDetails?.lastname ?? currentMiembro?.lastname ?? '',
                phone: currentMiembro?.phone ?? '',
                address: currentMiembro?.address ?? '',
            };
            initialValuesRef.current.assignment = {
                membresia: membresiaId?.toString() ?? '',
                dateInitial: formatDateForInput(asignacion.dateInitial),
                multiplier: Number(asignacion.multiplier) || 1,
                discount_percent: Number(asignacion.discount_percent) || 0,
            };

            setSelectedMembresia(asignacion.membresia_details as unknown as Membresia);
            setMultiplier(Number(asignacion.multiplier) || 1);
            setDiscountPercent(Number(asignacion.discount_percent) || 0);
            setDateInitial(formatDateForInput(asignacion.dateInitial));
        }
    }, [asignacion, miembros, reset, setSelectedMembresia, setMultiplier, setDiscountPercent, setDateInitial, initialValuesRef]);

    const onSubmit = useCallback(
        async (data: FormData) => {
            const formData = data as FormData;
            try {
                const membresiaId = parseInt(formData.membresia, 10);
                if (isNaN(membresiaId)) {
                    toast.error('Por favor, selecciona una membresía');
                    return;
                }

                const selectMembresia = membresias.find((m) => m.id === membresiaId);
                if (!selectMembresia) {
                    toast.error('Membresía no encontrada');
                    return;
                }

                const initialDate = new Date(formData.dateInitial);
                const finalDate = new Date(initialDate);
                finalDate.setDate(finalDate.getDate() + selectMembresia.duration * multiplier);

                const dateInitialStr = initialDate.toISOString().split('T')[0];
                const dateFinal = finalDate.toISOString().split('T')[0];

                if (modo === 'nuevo' && !params.id) {
                    // === CREAR MIEMBRO NUEVO + ASIGNAR MEMBRESÍA ===
                    if (!formData.nuevoName || !formData.nuevoLastname) {
                        toast.error('Nombre y apellido son requeridos');
                        return;
                    }

                    const memberData: CreateMemberDto = {
                        name: formData.nuevoName,
                        lastname: formData.nuevoLastname,
                        phone: formData.nuevoPhone || '',
                        address: formData.nuevoAddress || '',
                        initial_membership_id: membresiaId,
                        dateInitial: dateInitialStr,
                        multiplier: multiplier,
                        discount_percent: discountPercent,
                    };

                    await createMember(memberData);
                    toast.success('Miembro creado y membresía asignada', {
                        duration: 3000,
                        position: 'bottom-right',
                        style: { background: '#4b5563', color: '#fff', padding: '16px', borderRadius: '8px' },
                    });
                    reset();
                    setMultiplier(1);
                    setDiscountPercent(0);
                    navigate('/dashboard/miembros');
                } else {
                    // === EDITAR ASIGNACIÓN EXISTENTE ===
                    const miembroId = params.id
                        ? (asignacion?.miembro?.id ?? asignacion?.miembro_details?.id)
                        : parseInt(formData.miembro, 10);

                    if (!miembroId || isNaN(Number(miembroId))) {
                        toast.error('Por favor, selecciona un miembro');
                        return;
                    }

                    // Track what changed
                    const hasMemberChanges = memberDirty;
                    const hasAssignmentChanges = assignmentDirty && canEditAssignment;

                    // 1. If member data changed → update member personal info (always allowed when editing)
                    if (hasMemberChanges) {
                        const memberData: CreateMemberDto = {
                            name: formData.nuevoName ?? initialValuesRef.current?.member.name ?? '',
                            lastname: formData.nuevoLastname ?? initialValuesRef.current?.member.lastname ?? '',
                            phone: formData.nuevoPhone ?? initialValuesRef.current?.member.phone ?? '',
                            address: formData.nuevoAddress ?? initialValuesRef.current?.member.address ?? '',
                        };

                        await updateMember(miembroId, memberData);
                    }

                    // 2. If assignment changed AND can edit assignment (estado_pago === 'pending')
                    //    → update assignment with recalculated dateFinal
                    if (hasAssignmentChanges) {
                        const requestData: CreateAsignarMemberShipsDto = {
                            miembro: miembroId,
                            membresia: membresiaId,
                            multiplier: multiplier,
                            dateInitial: dateInitialStr,
                            dateFinal: dateFinal, // Recalculated ONLY when assignment changes
                            discount_percent: discountPercent,
                        };

                        await updateAsignarMemberShips(parseInt(params.id!, 10), requestData);
                    }

                    // 3. If only member changed (assignment not dirty or not editable), skip assignment call
                    //    dateFinal is NOT recalculated on pure member edits

                    toast.success('Asignación de Membresía Actualizada', {
                        duration: 3000,
                        position: 'bottom-right',
                        style: { background: '#4b5563', color: '#fff', padding: '16px', borderRadius: '8px' },
                    });
                    navigate('/dashboard/asignar-membresia-list');
                }
            } catch (err) {
                const errorMessage = err instanceof Error ? err.message : 'Error desconocido al procesar la solicitud';
                toast.error(`Error: ${errorMessage}`);
            }
        },
        [
            modo,
            params.id,
            asignacion,
            membresias,
            multiplier,
            discountPercent,
            memberDirty,
            assignmentDirty,
            canEditAssignment,
            reset,
            setMultiplier,
            setDiscountPercent,
            navigate,
            initialValuesRef,
        ]
    );

    return {
        // Mode
        setModo: setModoCallback,

        initializeFormFromAsignacion,

        // Handlers
        handleMemberShipsChange,
        handleMultiplierChange,

        // Submission
        onSubmit,
    }
}
export default useMemberFormActions;