import js from '@eslint/js'
import globals from 'globals'
import reactHooks from 'eslint-plugin-react-hooks'
import reactRefresh from 'eslint-plugin-react-refresh'
import tseslint from 'typescript-eslint'

// Deuda técnica: archivos que ya superaban las 250 líneas cuando se introdujo la
// regla `max-lines`. Quedan eximidos temporalmente. NO agregar entradas nuevas;
// al refactorizar uno, quitar su entrada de esta lista.
const LEGACY_LONG_FILES = [
  'src/tests/hooks/useMembershipPricing.test.ts',
  'src/pages/admin/calendario/CalendarioPage.tsx',
  'src/test/PasswordChangeRequiredPage.test.tsx',
  'src/tests/schemas/memberFormSchemas.test.ts',
  'src/hooks/memberForm/useMemberFormActions.ts',
  'src/pages/admin/asignadaMemberShips/ListAsignarMemberShips.tsx',
  'src/pages/admin/registroPorMes/ListMiembro.tsx',
  'src/pages/admin/registroPorDia/MemberFormDay.tsx',
  'src/pages/admin/usuarios/profile/Profile.tsx',
  'src/pages/admin/registroPorMes/MemberForm.tsx',
  'src/pages/admin/memberShips/MemberShipsForm.tsx',
]

export default tseslint.config(
  { ignores: ['dist'] },
  {
    extends: [js.configs.recommended, ...tseslint.configs.recommended],
    files: ['**/*.{ts,tsx}'],
    languageOptions: {
      ecmaVersion: 2020,
      globals: globals.browser,
    },
    plugins: {
      'react-hooks': reactHooks,
      'react-refresh': reactRefresh,
    },
    rules: {
      ...reactHooks.configs.recommended.rules,
      'react-refresh/only-export-components': [
        'warn',
        { allowConstantExport: true },
      ],
      // Regla dura del proyecto: ningún archivo de código supera las 250 líneas.
      'max-lines': ['error', { max: 250 }],
    },
  },
  {
    files: LEGACY_LONG_FILES,
    rules: {
      'max-lines': 'off',
    },
  },
)
