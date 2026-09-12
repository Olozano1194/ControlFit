# Design: Customizable Memberships

## Technical Approach

Replace the rigid `choices` field on `Membresia.name` with a free-text `CharField(max_length=100)`, add `max_multiplier` to control assignment limits, enforce `unique_together(gimnasio, name)`, and seed default memberships via `post_save` signal on `Gimnasio`. DRF generic views auto-serialize new fields — no view changes needed.

## Architecture Decisions

### Decision: Remove `choices` from `Membresia.name`

| Option | Tradeoff | Decision |
|--------|----------|----------|
| Keep choices + add new values | Limited flexibility, admin must edit code to add plans | Rejected |
| Free-text CharField | Requires unique_together + validation, but fully flexible | **Chosen** |
| Separate `MembresiaTemplate` model | Over-engineered for this scope | Rejected |

**Rationale**: Admins need to create plans like "Mensual $50k" or "Semanal" without code changes. `unique_together(gimnasio, name)` prevents duplicates per gym while allowing different gyms to share names.

### Decision: Seed via `post_save` signal (not view/controller)

| Option | Tradeoff | Decision |
|--------|----------|----------|
| Signal on Gimnasio.save() | Fires on every save, must check if memberships exist | **Chosen** |
| Override GimnasioSerializer.create() | Only fires on API create, not admin or shell | Rejected |
| Management command | Manual step, not automatic for new gyms | Rejected |

**Rationale**: Signal covers all creation paths (API, admin, shell, test). Guard `if not gimnasio.membresias.exists()` prevents re-seeding.

### Decision: Validation in `MembresiaAsignada.save()` + serializer

| Option | Tradeoff | Decision |
|--------|----------|----------|
| Model only (save/clean) | Prevents all bad data, but error messages less user-friendly | Partial |
| Serializer only | Better error messages, but bypassed by shell/script | Partial |
| Both layers | Defense-in-depth, model is safety net, serializer provides UX | **Chosen** |

**Rationale**: Serializer catches bad input early with DRF error format. Model `save()` is the safety net for any path that bypasses serialization.

## Data Flow

```
Admin Form (React)
  │
  ├─ MemberShipsForm ──POST──→ /api/membresias/ ──→ MembresiasSerializer.create()
  │                                                        │
  │                                                   Membresia.save()
  │                                                        │
  │                                                   DB (membresia table)
  │
  └─ AsignarMemberShipsForm ──POST──→ /api/membresia-asignada/
                                              │
                                     MembresiaAsignadaSerializer.validate()
                                              │
                                     multiplier <= max_multiplier?
                                              │
                                     MembresiaAsignada.save()
                                              │
                                     price = base * multiplier * (1 - discount/100)
                                     dateFinal = dateInitial + duration * multiplier
                                              │
                                              DB (membresiaAsignada table)
```

## File Changes

| File | Action | Description |
|------|--------|-------------|
| `gimnasioApp/models.py` | Modify | `Membresia`: remove `OPCIONES_NAME`, change `name` to `CharField(max_length=100)`, add `max_multiplier = PositiveIntegerField(default=1)`, add `unique_together = ('gimnasio', 'name')`. `MembresiaAsignada.save()`: add multiplier <= max_multiplier validation |
| `gimnasioApp/serializers.py` | Modify | `MembresiasSerializer`: add `max_multiplier` to fields, add `duration` validation (1–365). `MembresiaAsignadaSerializer.validate()`: add multiplier <= membresia.max_multiplier check |
| `gimnasioApp/signals.py` | Create | New file: `seed_default_memberships` signal handler for `post_save` on `Gimnasio` |
| `gimnasioApp/apps.py` | Modify | Import signals in `ready()` |
| `gimnasioApp/migrations/0003_membresia_max_multiplier_and_more.py` | Create | Schema migration: alter `name` field, add `max_multiplier`, add `unique_together` |
| `gimnasioApp/migrations/0004_seed_max_multiplier_data.py` | Create | Data migration: set `max_multiplier` for existing memberships based on name |
| `gimnasioReact/src/model/memberShips.model.ts` | Modify | Add `max_multiplier`, `is_active`, `gimnasio` to `Membresia` interface |
| `gimnasioReact/src/model/dto/memberShips.dto.ts` | Modify | Add `max_multiplier` to `CreateMemberShipsDTO` |
| `gimnasioReact/src/pages/admin/memberShips/MemberShipsForm.tsx` | Modify | Replace `<Select>` with `<Input>` for name, add `max_multiplier` number input, add `is_active` toggle, change duration validation from [15,30,45] to range 1–365 |
| `gimnasioReact/src/pages/admin/asignadaMemberShips/AsignarMemberShipsForm.tsx` | Modify | Generate multiplier `<Select>` options dynamically from `selectedMembresia.max_multiplier`, hide field when max_multiplier=1 |

## Interfaces / Contracts

### Model: `Membresia` (after migration)

```python
class Membresia(models.Model):
    name = models.CharField(max_length=100)  # Free-text, no choices
    price = models.DecimalField(max_digits=10, decimal_places=2)
    duration = models.PositiveIntegerField(help_text="Duration in days (1-365)")
    max_multiplier = models.PositiveIntegerField(default=1)  # 1 = non-multipliable
    is_active = models.BooleanField(default=True)
    gimnasio = models.ForeignKey(Gimnasio, on_delete=models.CASCADE, related_name='membresias')

    class Meta:
        unique_together = ('gimnasio', 'name')
```

### Validation in `MembresiaAsignada.save()`

```python
def save(self, *args, **kwargs):
    if not self.gimnasio_id and self.miembro_id:
        self.gimnasio = self.miembro.gimnasio
    if not self.pk:  # Only on creation
        if self.multiplier > self.membresia.max_multiplier:
            raise ValidationError(
                f"Multiplier {self.multiplier} exceeds maximum allowed ({self.membresia.max_multiplier})"
            )
        mult = Decimal(str(self.multiplier))
        disc = Decimal(str(self.discount_percent or 0))
        dias_totales = int(self.membresia.duration * mult)
        self.dateFinal = self.dateInitial + timedelta(days=dias_totales)
        self.price = self.membresia.price * mult * (Decimal('1') - disc / Decimal('100'))
    super().save(*args, **kwargs)
```

### Validation in `MembresiaAsignadaSerializer.validate()`

```python
def validate(self, data):
    # ... existing validations ...
    multiplier = data.get('multiplier', 1)
    membresia = data.get('membresia')
    if multiplier > membresia.max_multiplier:
        raise serializers.ValidationError(
            f"Multiplier {multiplier} exceeds the maximum allowed ({membresia.max_multiplier})"
        )
    return data
```

### TypeScript Interface

```typescript
export interface Membresia {
    id: number;
    name: string;
    price: number;
    duration: number;
    max_multiplier: number;
    is_active: boolean;
    gimnasio: number;
}
```

## Testing Strategy

| Layer | What to Test | Approach |
|-------|-------------|----------|
| Unit | MembresiaAsignada.save() rejects multiplier > max_multiplier | Create membership with max_multiplier=4, assign with multiplier=5, expect ValidationError |
| Unit | Membresia unique_together per gym | Create two memberships with same name for same gym, expect IntegrityError |
| Unit | Default seed on Gimnasio creation | Create Gimnasio, assert 3 memberships exist with correct names/durations |
| Unit | Seed does not re-seed existing gym | Create Gimnasio, add custom membership, save Gimnasio again, assert count unchanged |
| Integration | DRF serializer accepts valid data | POST to /api/membresias/ with max_multiplier, assert 201 |
| Integration | DRF serializer rejects multiplier > max | POST assignment with multiplier exceeding max, assert 400 |
| E2E | Admin creates custom membership | Fill form with custom name, duration, max_multiplier, submit, verify in list |
| E2E | Assignment hides multiplier when max=1 | Select membership with max_multiplier=1, verify multiplier field hidden |

## Migration / Rollout

### Schema Migration (`0003`)

1. Alter `Membresia.name`: remove `choices`, set `max_length=100`
2. Add `Membresia.max_multiplier` with `default=1`
3. Add `unique_together = ('gimnasio', 'name')`

### Data Migration (`0004`)

```python
def forwards(apps, schema_editor):
    Membresia = apps.get_model('gimnasioApp', 'Membresia')
    Membresia.objects.filter(name__iexact='básico').update(max_multiplier=1)
    Membresia.objects.filter(name__iexact='premium').update(max_multiplier=12)
    Membresia.objects.filter(name__iexact='VIP').update(max_multiplier=8)
```

Idempotent — `update()` on empty queryset is a no-op.

### Signal Seed

```python
# gimnasioApp/signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Gimnasio, Membresia

DEFAULT_MEMBERSHIPS = [
    {'name': 'Básico', 'duration': 15, 'max_multiplier': 1, 'price': 0},
    {'name': 'Premium', 'duration': 30, 'max_multiplier': 12, 'price': 0},
    {'name': 'VIP', 'duration': 45, 'max_multiplier': 8, 'price': 0},
]

@receiver(post_save, sender=Gimnasio)
def seed_default_memberships(sender, instance, created, **kwargs):
    if created and not instance.membresias.exists():
        Membresia.objects.bulk_create([
            Membresia(gimnasio=instance, **m) for m in DEFAULT_MEMBERSHIPS
        ])
```

## Open Questions

- [ ] Should `is_active` filter memberships from the assignment dropdown (hide inactive) or just prevent new assignments? Recommendation: filter from dropdown entirely.
- [ ] Should `discount_percent` tiers (`DISCOUNT_TIERS`) be made configurable per-membership in a future iteration, or keep them hardcoded? Out of scope for this change.
