import { z } from 'zod';

/**
 * Zod schema template for React Hook Form
 * Place in src/schemas/ and export from schemas/index.ts
 */

// ============================================
// BRANDED TYPES (optional but recommended)
// ============================================

type Brand<T, B> = T & { readonly __brand: B };

export type Email = Brand<string, 'Email'>;
export type UserId = Brand<string, 'UserId'>;
export type MembershipId = Brand<string, 'MembershipId'>;

// ============================================
// FORM SCHEMA
// ============================================

export const featureNameSchema = z.object({
  // Required fields
  email: z.string().email('Email inválido').min(1, 'Requerido'),
  name: z.string().min(2, 'Mínimo 2 caracteres').max(100),
  
  // Optional fields with defaults
  phone: z.string().regex(/^[\d\s\-\+\(\)]{7,20}$/, 'Teléfono inválido').optional(),
  
  // Enum / discriminated union
  paymentMethod: z.enum(['efectivo', 'transferencia', 'nequi']),
  
  // Nested object
  address: z.object({
    street: z.string().min(1),
    city: z.string().min(1),
    postalCode: z.string().regex(/^\d{5}$/, 'Código postal inválido'),
  }).optional(),
  
  // Array with min items
  tags: z.array(z.string().min(1)).min(1, 'Al menos un tag requerido'),
});

// Infer TypeScript type from schema
export type FeatureNameFormData = z.infer<typeof featureNameSchema>;

// ============================================
// TRANSFORMED / REFINED SCHEMA (for API)
// ============================================

export const featureNameApiSchema = featureNameSchema.transform((data) => ({
  ...data,
  email: data.email.toLowerCase().trim(),
  name: data.name.trim(),
  phone: data.phone?.replace(/\s/g, '') || null,
}));

export type FeatureNameApiData = z.infer<typeof featureNameApiSchema>;

// ============================================
// VALIDATION HELPERS
// ============================================

export function validateFeatureName(data: unknown): FeatureNameFormData {
  return featureNameSchema.parse(data);
}

export function safeValidateFeatureName(data: unknown) {
  return featureNameSchema.safeParse(data);
}