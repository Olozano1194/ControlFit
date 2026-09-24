// Centralized types for MemberForm refactor

import type { UseFormRegister, FieldErrors, UseFormWatch, UseFormHandleSubmit, UseFormReset, UseFormSetValue, UseFormTrigger, UseFormGetValues } from 'react-hook-form';

// ============================================
// Form Data
// ============================================

export interface FormData {
  miembro: string;
  membresia: string;
  multiplier: string;
  dateInitial: string;
  // Campos para nuevo miembro
  nuevoName: string;
  nuevoLastname: string;
  nuevoPhone: string;
  nuevoAddress: string;
}

// ============================================
// Form Modes
// ============================================

export type ModoFormulario = 'existente' | 'nuevo';

export type MemberFormMode = ModoFormulario;

// ============================================
// Selected Membership (from memberships list)
// ============================================

export interface SelectedMembresia {
  id: number;
  name: string;
  price: number;
  duration: number;
  max_multiplier: number;
  is_active?: boolean;
  gimnasio: number;
}

// ============================================
// Member (existing member from API)
// ============================================

export interface Miembro {
  id: number;
  name: string;
  lastname: string;
  phone: string;
  address: string;
}

// ============================================
// Hook Return Types
// ============================================

// Type aliases for react-hook-form return types
type FormRegister = UseFormRegister<FormData>;
type FormErrors = FieldErrors<FormData>;
type FormWatch = UseFormWatch<FormData>;
type FormHandleSubmit = UseFormHandleSubmit<FormData>;
type FormReset = UseFormReset<FormData>;
type FormSetValue = UseFormSetValue<FormData>;
type FormTrigger = UseFormTrigger<FormData>;
type FormGetValues = UseFormGetValues<FormData>;

// useMemberFormData - manages form state, validation, submission
export interface UseMemberFormDataReturn {
  // Form methods
  register: FormRegister;
  handleSubmit: FormHandleSubmit;
  reset: FormReset;
  watch: FormWatch;
  setValue: FormSetValue;
  trigger: FormTrigger;
  getValues: FormGetValues;
  
  // Form state
  errors: FormErrors;
  isSubmitting: boolean;
  isDirty: boolean;
  
  // Mode
  modo: ModoFormulario;
  setModo: (modo: ModoFormulario) => void;
  
  // Data
  miembros: Miembro[];
  membresias: SelectedMembresia[];
  selectedMembresia: SelectedMembresia | null;
  setSelectedMembresia: (m: SelectedMembresia | null) => void;
  
  // Multiplier & Discount
  multiplier: number;
  setMultiplier: (m: number) => void;
  discountPercent: number;
  setDiscountPercent: (d: number) => void;
  
  // Computed
  multiplierOptions: number[];
  showMultiplier: boolean;
  estimatedPrice: number;
  totalDays: number;
  estimatedDateFinal: string;
  
  // Handlers
  handleMemberShipsChange: (event: React.ChangeEvent<HTMLSelectElement>) => void;
  handleMultiplierChange: (event: React.ChangeEvent<HTMLSelectElement>) => void;
  
  // Submission
  onSubmit: (data: FormData) => Promise<void>;
  isEditing: boolean;
}

// useMembershipPricing - pricing calculations
export interface UseMembershipPricingReturn {
  estimatedPrice: number;
  totalDays: number;
  estimatedDateFinal: string;
  multiplierOptions: number[];
  showMultiplier: boolean;
  selectedMembresia: SelectedMembresia | null;
  setSelectedMembresia: (m: SelectedMembresia | null) => void;
  multiplier: number;
  setMultiplier: (m: number) => void;
  discountPercent: number;
  setDiscountPercent: (d: number) => void;
  handleMemberShipsChange: (event: React.ChangeEvent<HTMLSelectElement>) => void;
  handleMultiplierChange: (event: React.ChangeEvent<HTMLSelectElement>) => void;
}

// useMemberForm - orchestrates the form
export interface UseMemberFormReturn {
  // Form
  register: FormRegister;
  handleSubmit: FormHandleSubmit;
  reset: FormReset;
  watch: FormWatch;
  errors: FormErrors;
  isSubmitting: boolean;
  isDirty: boolean;
  
  // Mode
  modo: ModoFormulario;
  setModo: (modo: ModoFormulario) => void;
  
  // Data
  miembros: Miembro[];
  membresias: SelectedMembresia[];
  selectedMembresia: SelectedMembresia | null;
  
  // Pricing (delegated to useMembershipPricing)
  multiplier: number;
  discountPercent: number;
  multiplierOptions: number[];
  showMultiplier: boolean;
  estimatedPrice: number;
  totalDays: number;
  estimatedDateFinal: string;
  
  // Handlers
  handleMemberShipsChange: (event: React.ChangeEvent<HTMLSelectElement>) => void;
  handleMultiplierChange: (event: React.ChangeEvent<HTMLSelectElement>) => void;
  
  // Submission
  onSubmit: (data: FormData) => Promise<void>;
  isEditing: boolean;
}

// ============================================
// Component Props Interfaces
// ============================================

// ModeToggle - toggle between existing/new member
export interface ModeToggleProps {
  modo: ModoFormulario;
  onChange: (modo: ModoFormulario) => void;
  disabled?: boolean;
}

// ExistingMemberSelect - select dropdown for existing members
export interface ExistingMemberSelectProps {
  register: FormRegister;
  errors: FormErrors;
  miembros: Miembro[];
  disabled?: boolean;
}

// NewMemberFields - form fields for new member data
export interface NewMemberFieldsProps {
  register: FormRegister;
  errors: FormErrors;
  disabled?: boolean;
}

// MembershipSelect - select dropdown for memberships
export interface MembershipSelectProps {
  register: FormRegister;
  errors: FormErrors;
  membresias: SelectedMembresia[];
  onChange: (event: React.ChangeEvent<HTMLSelectElement>) => void;
  disabled?: boolean;
}

// DateInitialField - date input for initial date
export interface DateInitialFieldProps {
  register: FormRegister;
  errors: FormErrors;
  disabled?: boolean;
}

// MultiplierDiscountFields - multiplier select and discount input
export interface MultiplierDiscountFieldsProps {
  multiplier: number;
  discountPercent: number;
  multiplierOptions: number[];
  onMultiplierChange: (event: React.ChangeEvent<HTMLSelectElement>) => void;
  onDiscountChange: (value: number) => void;
  disabled?: boolean;
}

// PaymentSummary - displays pricing summary
export interface PaymentSummaryProps {
  selectedMembresia: SelectedMembresia | null;
  multiplier: number;
  discountPercent: number;
  estimatedPrice: number;
  totalDays: number;
  estimatedDateFinal: string;
  disabled?: boolean;
}