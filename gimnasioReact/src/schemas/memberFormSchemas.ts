// Zod validation schemas for MemberForm
import { z } from 'zod';

// ============================================
// Common fields shared by all modes
// ============================================

const commonFields = {
  membresia: z.string().min(1, 'Membresía requerida'),
  dateInitial: z.string().min(1, 'Fecha requerida'),
  multiplier: z.string().optional(),
  nuevoAddress: z.string().max(50, 'La dirección debe tener como máximo 50 caracteres').optional(),
};

// ============================================
// Existing member mode schema (select existing member)
// ============================================

export const existingMemberSchema = z.object({
  ...commonFields,
  miembro: z.string().min(1, 'Miembro requerido'),
  // Fields NOT required for existing member
  nuevoName: z.string().optional(),
  nuevoLastname: z.string().optional(),
  nuevoPhone: z.string().optional(),
});

// ============================================
// New member mode schema (create new member)
// ============================================

const lettersOnlyRegex = /^[a-zA-ZáéíóúÁÉÍÓÚñÑ\s]+$/;
const digitsOnlyRegex = /^[0-9]+$/;

export const newMemberSchema = z.object({
  ...commonFields,
  // Fields NOT required for new member
  miembro: z.string().optional(),
  // Required fields for new member
  nuevoName: z.string()
    .min(4, 'El nombre debe tener como mínimo 4 letras')
    .max(20, 'El nombre debe tener como máximo 20 letras')
    .regex(lettersOnlyRegex, 'Nombre inválido'),
  nuevoLastname: z.string()
    .min(5, 'El apellido debe tener como mínimo 5 letras')
    .max(20, 'El apellido debe tener como máximo 20 letras')
    .regex(lettersOnlyRegex, 'Apellido inválido'),
  nuevoPhone: z.string()
    .min(10, 'El celular debe tener como mínimo 10 números')
    .max(10, 'El celular debe tener como máximo 10 números')
    .regex(digitsOnlyRegex, 'Número celular inválido'),
});

// ============================================
// Editing member mode schema (member ID comes from URL/asignacion)
// ============================================
//
// In edit mode:
// - Member fields (nuevoName, nuevoLastname, nuevoPhone, nuevoAddress) are optional
//   because they're pre-filled from the assignment and user may only change some
// - Assignment fields (membresia, dateInitial, multiplier) are required by schema
//   but the submit logic gates the actual API call via canEditAssignment
// - This allows member-only updates to pass validation even if assignment
//   fields haven't changed (or membership is inactive)

export const editingMemberSchema = z.object({
  ...commonFields,
  // miembro is NOT required - it comes from the asignacion (URL params)
  miembro: z.string().optional(),
  // Member detail fields - optional when editing (pre-filled from asignacion)
  nuevoName: z.string().optional(),
  nuevoLastname: z.string().optional(),
  nuevoPhone: z.string().optional(),
});

// ============================================
// Schema factory
// ============================================

export type ModoFormulario = 'existente' | 'nuevo' | 'edicion';

export function memberFormSchema(modo: ModoFormulario, isEditing = false) {
  if (isEditing) return editingMemberSchema;
  return modo === 'existente' ? existingMemberSchema : newMemberSchema;
}