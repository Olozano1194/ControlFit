import { useState, useCallback, useMemo, useEffect, useRef } from 'react';
import { useForm, type Resolver, type FieldErrors } from 'react-hook-form';
import { useNavigate, useParams } from 'react-router-dom';
import { toast } from 'react-hot-toast';
import { useMembershipPricing } from './useMembershipPricing';
import { useMemberFormData } from './useMemberFormData';
import { memberFormSchema, type ModoFormulario } from '../schemas/memberFormSchemas';
import type { FormData, Miembro } from '../types/MemberFormTypes';
import type { Membresia } from '../model/memberShips.model';
import type { AsignarMemberShips } from '../model/asignarMemberShips.model';
import { createMember, updateMember } from '../api/action/userGym.api';
import { updateAsignarMemberShips } from '../api/action/asignarMemberShips.api';
import type { CreateMemberDto } from '../model/dto/member.dto';
import type { CreateAsignarMemberShipsDto } from '../model/dto/asignarMemberShips.dto';
import { formatDateForInput } from '../utils/dateUtils';

export interface UseMemberFormReturn {
  // Form
  register: ReturnType<typeof useForm<FormData>>['register'];
  handleSubmit: ReturnType<typeof useForm<FormData>>['handleSubmit'];
  reset: ReturnType<typeof useForm<FormData>>['reset'];
  watch: ReturnType<typeof useForm<FormData>>['watch'];
  errors: ReturnType<typeof useForm<FormData>>['formState']['errors'];
  isSubmitting: boolean;
  isDirty: boolean;

  // Mode
  modo: ModoFormulario;
  setModo: (modo: ModoFormulario) => void;

  // Data
  miembros: Miembro[];
  membresias: Membresia[];
  selectedMembresia: Membresia | null;
  asignacion: AsignarMemberShips | null;

  // Pricing (delegated to useMembershipPricing)
  multiplier: number;
  discountPercent: number;
  multiplierOptions: number[];
  showMultiplier: boolean;
  estimatedPrice: number;
  totalDays: number;
  estimatedDateFinal: string;

  // Editing values (for display in disabled fields)
  editingMembresiaId: string;
  editingDateInitial: string;
  isMembershipActive: boolean;

  // Dirty tracking
  memberDirty: boolean;
  assignmentDirty: boolean;

  // Editability
  canEditAssignment: boolean;

  // Handlers
  handleMemberShipsChange: (event: React.ChangeEvent<HTMLSelectElement>) => void;
  handleMultiplierChange: (event: React.ChangeEvent<HTMLSelectElement>) => void;
  setDiscountPercent: (val: number) => void;

  // Submission
  onSubmit: (data: FormData) => Promise<void>;
  isEditing: boolean;
}

export function useMemberForm(): UseMemberFormReturn {
  const params = useParams<{ id?: string }>();
  const navigate = useNavigate();
  const isEditing = !!params.id;

  const [modo, setModoState] = useState<ModoFormulario>('existente');

  const {
    membresias,
    miembros,
    asignacion,
  } = useMemberFormData({ id: params.id });

  const form = useForm<FormData>({
    // Custom resolver that reacts to modo/isEditing changes
    resolver: (async (values) => {
      const schema = memberFormSchema(modo, isEditing);
      const result = await schema.safeParseAsync(values);
      if (result.success) {
        return { values: result.data, errors: {} };
      }
      return { values: {}, errors: result.error.flatten().fieldErrors as FieldErrors<FormData> };
    }) as Resolver<FormData>,
    shouldUnregister: true,
    defaultValues: {
      miembro: '',
      membresia: '',
      multiplier: '1',
      dateInitial: '',
      nuevoName: '',
      nuevoLastname: '',
      nuevoPhone: '',
      nuevoAddress: '',
    },
  });

  const {
    register,
    handleSubmit,
    reset,
    watch,
    formState: { errors, isSubmitting, isDirty },
    setValue,
  } = form;

  const dateInitial = watch('dateInitial');

  const {
    selectedMembresia,
    setSelectedMembresia,
    multiplier,
    setMultiplier,
    discountPercent,
    setDiscountPercent,
    multiplierOptions,
    showMultiplier,
    estimatedPrice,
    totalDays,
    estimatedDateFinal: estimatedDateFinalFromPricing,
    setDateInitial,
  } = useMembershipPricing(null);

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

  const setModo = useCallback(
    (newModo: ModoFormulario) => {
      setModoState(newModo);
      reset(undefined, { keepValues: false });
      setSelectedMembresia(null);
      setMultiplier(1);
      setDiscountPercent(0);
    },
    [reset, setSelectedMembresia, setMultiplier, setDiscountPercent]
  );

  const estimatedDateFinal = useMemo(() => {
    if (!dateInitial || !selectedMembresia) return '';
    return estimatedDateFinalFromPricing;
  }, [dateInitial, selectedMembresia, estimatedDateFinalFromPricing]);

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

  // Dirty tracking - compare current form values with initial values
  const memberDirty = useMemo(() => {
    if (!initialValuesRef.current || !isEditing) return false;

    const currentName = watch('nuevoName') ?? '';
    const currentLastname = watch('nuevoLastname') ?? '';
    const currentPhone = watch('nuevoPhone') ?? '';
    const currentAddress = watch('nuevoAddress') ?? '';

    const { name, lastname, phone, address } = initialValuesRef.current.member;

    return (
      currentName !== name ||
      currentLastname !== lastname ||
      currentPhone !== phone ||
      currentAddress !== address
    );
  }, [watch, isEditing]);

  const assignmentDirty = useMemo(() => {
    if (!initialValuesRef.current || !isEditing) return false;

    const currentMembresia = watch('membresia') ?? '';
    const currentDateInitial = watch('dateInitial') ?? '';
    const currentMultiplier = parseInt(watch('multiplier') ?? '1', 10);
    const currentDiscount = discountPercent;

    const { membresia, dateInitial, multiplier, discount_percent } = initialValuesRef.current.assignment;

    return (
      currentMembresia !== membresia ||
      currentDateInitial !== dateInitial ||
      currentMultiplier !== multiplier ||
      currentDiscount !== discount_percent
    );
  }, [watch, discountPercent, isEditing]);

  // Can edit assignment only when estado_pago === 'pending'
  const canEditAssignment = useMemo(() => {
    if (!asignacion) return true; // New assignments are always editable
    return asignacion.estado_pago === 'pending';
  }, [asignacion]);

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
      setSelectedMembresia(asignacion.membresia_details as unknown as Membresia);
      setMultiplier(Number(asignacion.multiplier) || 1);
      setDiscountPercent(Number(asignacion.discount_percent) || 0);
      setDateInitial(formatDateForInput(asignacion.dateInitial));
    }
  }, [asignacion, miembros, reset, setSelectedMembresia, setMultiplier, setDiscountPercent, setDateInitial]);

  useEffect(() => {
    if (asignacion) {
      initializeFormFromAsignacion();
    }
  }, [asignacion, initializeFormFromAsignacion]);

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
              name: formData.nuevoName || initialValuesRef.current?.member.name || '',
              lastname: formData.nuevoLastname || initialValuesRef.current?.member.lastname || '',
              phone: formData.nuevoPhone || initialValuesRef.current?.member.phone || '',
              address: formData.nuevoAddress || initialValuesRef.current?.member.address || '',
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
    ]
  );

  return {
    // Form
    register,
    handleSubmit,
    reset,
    watch,
    errors,
    isSubmitting,
    isDirty,

    // Mode
    modo,
    setModo,

    // Data
    miembros,
    membresias,
    selectedMembresia,
    asignacion,

    // Pricing
    multiplier,
    discountPercent,
    multiplierOptions,
    showMultiplier,
    estimatedPrice,
    totalDays,
    estimatedDateFinal,

    // Editing values (for display in disabled fields)
    editingMembresiaId,
    editingDateInitial,
    isMembershipActive,

    // Dirty tracking
    memberDirty,
    assignmentDirty,

    // Editability
    canEditAssignment,

    // Handlers
    handleMemberShipsChange,
    handleMultiplierChange,
    setDiscountPercent,

    // Submission
    onSubmit,
    isEditing,
  };
}