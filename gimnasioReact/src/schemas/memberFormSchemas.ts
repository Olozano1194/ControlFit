// Zod validation schemas for MemberForm
import { z } from 'zod';

// ============================================
// Common fields shared by both modes
// ============================================

const commonFields = {
  membresia: z.string().min(1, 'Membresía requerida'),
  dateInitial: z.string().min(1, 'Fecha requerida'),
  multiplier: z.string().optional(),
  nuevoAddress: z.string().max(50, 'La dirección debe tener como máximo 50 caracteres').optional(),
};

// ============================================
// Existing member mode schema
// ============================================

export const existingMemberSchema = z.object({
  ...commonFields,
  miembro: z.string().min(1, 'Nombre requerido'),
  // Fields NOT required for existing member
  nuevoName: z.string().optional(),
  nuevoLastname: z.string().optional(),
  nuevoPhone: z.string().optional(),
});

// ============================================
// New member mode schema
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
// Schema factory
// ============================================

export type ModoFormulario = 'existente' | 'nuevo';

export function memberFormSchema(modo: ModoFormulario) {
  return modo === 'existente' ? existingMemberSchema : newMemberSchema;
}