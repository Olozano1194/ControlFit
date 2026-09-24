import type { ModeToggleProps } from '../../types/MemberFormTypes';

export function ModeToggle({ modo, onChange, disabled = false }: ModeToggleProps) {
  return (
    <div role="radiogroup" aria-label="Tipo de miembro" className="flex gap-2">
      <button
        type="button"
        role="radio"
        aria-pressed={modo === 'existente'}
        aria-disabled={disabled}
        disabled={disabled}
        onClick={() => !disabled && modo !== 'existente' && onChange('existente')}
        className={`flex-1 flex items-center justify-center gap-2 py-2 px-4 rounded-lg text-sm font-semibold transition-all ${
          modo === 'existente'
            ? 'bg-primary text-white shadow-md'
            : 'bg-surface-container-high text-on-surface/70 hover:bg-surface-container-high/80'
        } ${disabled ? 'opacity-50 cursor-not-allowed' : ''}`}
      >
        <span className="text-lg" aria-hidden="true">👥</span>
        Miembro existente
      </button>
      <button
        type="button"
        role="radio"
        aria-pressed={modo === 'nuevo'}
        aria-disabled={disabled}
        disabled={disabled}
        onClick={() => !disabled && modo !== 'nuevo' && onChange('nuevo')}
        className={`flex-1 flex items-center justify-center gap-2 py-2 px-4 rounded-lg text-sm font-semibold transition-all ${
          modo === 'nuevo'
            ? 'bg-primary text-white shadow-md'
            : 'bg-surface-container-high text-on-surface/70 hover:bg-surface-container-high/80'
        } ${disabled ? 'opacity-50 cursor-not-allowed' : ''}`}
      >
        <span className="text-lg" aria-hidden="true">➕</span>
        Nuevo miembro
      </button>
    </div>
  );
}