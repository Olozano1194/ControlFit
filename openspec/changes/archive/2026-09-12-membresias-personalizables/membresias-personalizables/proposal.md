# Propuesta: Membresías Personalizables

## Intento

Cada gimnasio necesita crear sus propios planes de membresía (nombres, duraciones, precios) sin estar limitado a 3 opciones fijas. Hoy `Membresia.name` usa choices rígidos (`básico`, `premium`, `VIP`) y `duration` solo acepta 15/30/45.

## Alcance

### Incluido
- Modelo `Membresia` sin choices: `name` libre, `duration` 1–365, `max_multiplier` configurable
- Defaults automáticos al crear un gimnasio (editables después)
- Validación en backend: `multiplier ≤ max_multiplier` en `MembresiaAsignada.save()`
- Formulario de membresías: `<Input>` texto + `max_multiplier` + `is_active` toggle
- Formulario de asignación: multiplier dinámico según `max_multiplier` seleccionado
- Migración de datos existentes (`básico`→max_multiplier=1, `premium`→12, `VIP`→8)

### Excluido
- Precios sugeridos por defecto (se crean con precio 0, el admin los edita)
- Regla de negocio de descuento por volumen (ya existe en el cambio anterior)

## Capacidades

### Nuevas Capacidades
- `membresia-personalizable`: CRUD de membresías con name libre, duración 1–365, max_multiplier configurable, unique_together(gimnasio, name)
- `siembra-membresias-default`: creación automática de membresías base al crear un gimnasio

### Capacidades Modificadas
- Ninguna (no hay specs previas en `openspec/specs/`)

## Enfoque

### Modelo
```
Membresia:
  name = CharField(max_length=100)       # Sin choices
  price = DecimalField(max_digits=10, decimal_places=2)
  duration = PositiveIntegerField(1..365)
  max_multiplier = PositiveIntegerField(default=1)  # 1 = no multiplicable
  is_active = BooleanField(default=True)
  gimnasio = FK(Gimnasio)
  Meta: unique_together = (gimnasio, name)
```

### Defaults por gimnasio nuevo

| Membresía | Duración | max_multiplier |
|-----------|----------|---------------|
| Básico | 15 | 1 |
| Premium | 30 | 12 |
| VIP | 45 | 8 |

### Validaciones clave
- `MembresiaAsignada.save()`: rechazar si `multiplier > membresia.max_multiplier`
- Serializer: `duration` entre 1 y 365, `max_multiplier ≥ 1`
- Frontend AsignarMemberShipsForm: ocultar/limitar select de multiplier según `max_multiplier` de la membresía seleccionada

### Seed
- Señal `post_save` de Gimnasio: crear 3 defaults si no existen membresías para ese gimnasio
- Migración para gimnasios existentes: actualizar `max_multiplier` según el name actual

## Archivos afectados

| Archivo | Impacto | Cambio |
|---------|---------|--------|
| `gimnasioApp/models.py` | Modificado | Membresia: eliminar choices, +max_multiplier, +unique_together; MembresiaAsignada.save(): validar multiplier |
| `gimnasioApp/serializers.py` | Modificado | +max_multiplier en MembresiasSerializer; validar multiplier contra max_multiplier |
| `gimnasioApp/views.py` | Sin cambio | CRUD genérico, los nuevos campos se serializan automáticamente |
| `gimnasioApp/tests.py` | Modificado | Tests que validaban contra choices |
| `gimnasioReact/src/model/memberShips.model.ts` | Modificado | +max_multiplier, is_active, gimnasio |
| `gimnasioReact/src/model/dto/memberShips.dto.ts` | Modificado | +max_multiplier |
| `gimnasioReact/src/pages/admin/memberShips/MemberShipsForm.tsx` | Modificado | <Select>→<Input> texto, +max_multiplier, +is_active, validación 1–365 |
| `gimnasioReact/src/pages/admin/asignadaMemberShips/AsignarMemberShipsForm.tsx` | Modificado | Multiplier dinámico según max_multiplier |

## Riesgos

| Riesgo | Prob. | Mitigación |
|--------|-------|------------|
| Membresías existentes sin max_multiplier | Baja | Migración asigna según name actual |
| Nombres duplicados por gimnasio | Baja | unique_together + validación en form |
| Multiplier > max_multiplier en asignaciones previas | Baja | Solo se valida en creates nuevos |

## Rollback

Revertir migraciones: eliminar columna `max_multiplier`, restaurar `choices` en `name`, revertir `unique_together`. Restaurar frontend desde git.

## Dependencias

- Migración de base de datos (3 gimnasios existentes aprox.)

## Criterios de éxito

- [ ] Admin crea membresía "Mensual $50k" con duration=30, max_multiplier=6
- [ ] Admin crea membresía "Semanal $15k" con duration=7, max_multiplier=4
- [ ] Al asignar "Semanal", el multiplier máximo en frontend es 4
- [ ] Al asignar "Básico" (max_multiplier=1), el campo multiplier se oculta
- [ ] Backend rechaza asignación con multiplier > max_multiplier
- [ ] Gimnasio nuevo tiene 3 membresías por defecto
- [ ] Gimnasio existente migra sus membresías con max_multiplier correcto
