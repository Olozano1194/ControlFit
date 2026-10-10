import { useState, useMemo, useEffect } from 'react';
import { useForm } from 'react-hook-form';
import { useNavigate, useParams } from 'react-router-dom';
import { useMembershipPricing } from './useMembershipPricing';
import { useMemberFormData } from './useMemberFormData';
import { type ModoFormulario } from '../schemas/memberFormSchemas';
import type { FormData, Miembro } from '../types/MemberFormTypes';
import type { Membresia } from '../model/memberShips.model';
import type { AsignarMemberShips } from '../model/asignarMemberShips.model';
import useMemberFormValidation  from './memberForm/useMemberFormValidation';
import useMemberFormUIState from './memberForm/useMemberFormUIState';
import useMemberFormActions from './memberForm/useMemberFormActions';

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

  const { register, setValue, handleSubmit, reset, watch,errors, isSubmitting, isDirty, } = useMemberFormValidation({ modo, isEditing }); 

  const {
    membresias,
    miembros,
    asignacion,
  } = useMemberFormData({ id: params.id });

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

  const estimatedDateFinal = useMemo(() => {
    if (!dateInitial || !selectedMembresia) return '';
    return estimatedDateFinalFromPricing;
  }, [dateInitial, selectedMembresia, estimatedDateFinalFromPricing]);

  //aca va el UIState
  const {
    editingMembresiaId,
    editingDateInitial,
    isMembershipActive,
    memberDirty,
    assignmentDirty,
    canEditAssignment,
    initialValuesRef,
  } = useMemberFormUIState({
    asignacion,
    miembros,
    watch,
    isEditing,
    discountPercent,
  });

  const {
    handleMemberShipsChange,
    handleMultiplierChange,
    onSubmit,
    initializeFormFromAsignacion,
    setModo,
  } = useMemberFormActions({
    miembros,
    membresias,
    asignacion,

    modo,
    setModo: setModoState,

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
  });

  useEffect(() => {
    if (asignacion) {
      initializeFormFromAsignacion();
    }
  }, [asignacion, initializeFormFromAsignacion]);

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