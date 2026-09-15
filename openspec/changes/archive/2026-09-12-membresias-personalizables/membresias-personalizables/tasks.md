# Tasks: Customizable Memberships

## Review Workload Forecast

| Field | Value |
|-------|-------|
| Estimated changed lines | 250–340 |
| 400-line budget risk | Low |
| Chained PRs recommended | No |
| Suggested split | Single PR |
| Delivery strategy | single-pr |
| Chain strategy | size-exception |

Decision needed before apply: Yes
Chained PRs recommended: No
Chain strategy: size-exception
400-line budget risk: Low

## Phase 1: Backend Model + Migrations

- [x] 1.1 `gimnasioApp/models.py`: Remove `OPCIONES_NAME` choices, change `name` to `CharField(max_length=100)`, add `max_multiplier = PositiveIntegerField(default=1)`, add `class Meta: unique_together = ('gimnasio', 'name')`
- [x] 1.2 `gimnasioApp/models.py`: Add multiplier validation in `MembresiaAsignada.save()` — reject if `multiplier > self.membresia.max_multiplier` on creation
- [x] 1.3 Create schema migration `0002_membresia_max_multiplier_and_more.py` (actual) / `0004_alter_membresia_name_unique_together.py` (alter): alter `name` (remove choices, set max_length=100), add `max_multiplier` default=1, add `unique_together`
- [x] 1.4 Create data migration `0003_seed_max_multiplier_data.py`: set `max_multiplier=1` for "básico", `12` for "premium", `8` for "VIP" (idempotent updates)

## Phase 2: Backend Serializers

- [x] 2.1 `gimnasioApp/serializers.py` — `MembresiasSerializer`: add `max_multiplier` to `fields`, add `duration` validation (1–365 range)
- [x] 2.2 `gimnasioApp/serializers.py` — `MembresiaAsignadaSerializer.validate()`: add check `multiplier <= membresia.max_multiplier`, raise ValidationError if exceeded

## Phase 3: Backend Signals + App Config

- [x] 3.1 Create `gimnasioApp/signals.py`: `seed_default_memberships` signal handler on `post_save` of `Gimnasio` — create Básico/Premium/VIP defaults only if `not instance.membresias.exists()`
- [x] 3.2 `gimnasioApp/apps.py`: import signals module in `ready()` method

## Phase 4: Frontend Model + DTO Updates

- [x] 4.1 `gimnasioReact/src/model/memberShips.model.ts`: add `max_multiplier: number`, `is_active: boolean`, `gimnasio: number` to `Membresia` interface
- [x] 4.2 `gimnasioReact/src/model/dto/memberShips.dto.ts`: add `max_multiplier: number` to `CreateMemberShipsDTO`

## Phase 5: Frontend Form Redesign

- [x] 5.1 `MemberShipsForm.tsx`: Replace `<Select>` for name with `<Input>` (free text), add `max_multiplier` number input (min=1), add `is_active` toggle/checkbox, change duration validation from `[15,30,45]` to range `1–365`
- [x] 5.2 `MemberShipsForm.tsx`: Update `MembresiaForm` interface and `onSubmit` to include `max_multiplier` and `is_active` in request data
- [x] 5.3 `AsignarMemberShipsForm.tsx`: Generate multiplier `<Select>` options dynamically from `1..selectedMembresia.max_multiplier`, hide multiplier field when `max_multiplier === 1`

## Phase 6: Tests

- [x] 6.1 Update existing test memberships in `tests.py` to include `max_multiplier` where needed (e.g. `Membresia.objects.create(name="básico", ..., max_multiplier=1)`)
- [x] 6.2 Add test: `MembresiaAsignada.save()` rejects `multiplier > max_multiplier` with ValidationError
- [x] 6.3 Add test: `Membresia` unique_together per gym — two memberships with same name for same gym raises IntegrityError
- [x] 6.4 Add test: seed signal creates 3 default memberships on Gimnasio creation
- [x] 6.5 Add test: seed signal does NOT re-seed when memberships already exist
- [x] 6.6 Add test: `MembresiasSerializer` rejects `duration=0` or `duration=400`
- [x] 6.7 Add test: `MembresiaAsignadaSerializer` rejects `multiplier > max_multiplier`
