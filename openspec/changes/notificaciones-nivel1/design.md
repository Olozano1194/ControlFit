# Design: notificaciones-nivel1 — Persistent Notification Foundation

## Technical Approach

Replace ephemeral per-request notification computation with a persistent `Notification` model. Generation is lazy (inside the list endpoint), idempotent via `get_or_create` on a `UniqueConstraint`, and scoped to two sources: membership expirations (≤3d / expired) and same-day calendar events. A `NotificationViewSet` replaces two legacy function-based views. The frontend switches to the new API, fixes broken links, and adds calendar deep-linking.

## Architecture Decisions

| Decision | Choice | Alternatives | Rationale |
|---|---|---|---|
| Generation trigger | Lazy in list endpoint | Celery/cron, management command only, signal on save | No task queue in project; bounded windows (single-digit rows); management command kept as opt-in convenience but list endpoint is primary |
| Source reference | Polymorphic `relacion_tipo`/`relacion_id` | Direct FK per type, GenericForeignKey | Matches `EventoCalendario` pattern already in codebase; one unique key covers all types; rows are self-contained → orphaned rows harmless |
| Legacy endpoints | Delete (not wrap) | Deprecate + redirect | Frontend rewired same change; single source of truth; avoids drift with deprecated `notified_at` |
| Event window | Same day (`__date=today`) | Multi-day configurable, 24h rolling | Confirmed business decision; simple to implement; defers config complexity to Nivel 2 |
| List semantics | Unread only (read disappears) | Show all with read indicator | Confirmed UX decision; simplifies pagination and badge |
| Generation location | `gimnasioApp/services/notifications.py` | Inline in views.py, management command only | Repo has no services/ dir yet; generation logic is ~60 lines and deserves isolation; ViewSets stay thin |
| Timezone rule | `date.today()` (UTC) | `zoneinfo`-aware local date | Backend uses `USE_TZ=True`, `TIME_ZONE='UTC'` (default). `EventoCalendario.fecha_inicio` stores UTC datetimes. `date.today()` gives UTC date. Events created for "today" in Colombia (UTC-5) are stored as UTC datetimes whose `.date()` matches Bogotá's calendar date. This is correct because the calendar frontend already normalizes to local wall-clock time via `dateTime.ts`. |
| Backfill | No backfill (fresh start) | Migrate `notified_at` rows to Notification table | Justified: `notified_at` marks "dismissed" not "existed"; creating read notifications for stale data adds noise; one-time reappearance of expirations is documented and accepted |

## Data Flow

```
GET /Notificaciones/
  │
  ├─ NotificationViewSet.list()
  │    ├─ NotificationManager.generate_for_gimnasio(gimnasio)  ← lazy idempotent
  │    │    ├─ MembresiaAsignada.filter(dateFinal__gt=today, dateFinal__lte=today+3d)
  │    │    │    └─ get_or_create(tipo='por_vencer', relacion_tipo='membership', ...)
  │    │    ├─ MembresiaAsignada.filter(dateFinal__lte=today)
  │    │    │    └─ get_or_create(tipo='vencida', relacion_tipo='membership', ...)
  │    │    └─ EventoCalendario.filter(fecha_inicio__date=today)
  │    │         └─ get_or_create(tipo='evento', relacion_tipo='evento', ...)
  │    └─ Return unread only: Notification.objects.filter(gimnasio=..., is_read=False)
  │
POST /Notificaciones/{id}/marcar-leida/
  │    └─ Update is_read=True, read_at=timezone.now()
  │
POST /Notificaciones/marcar-todas-leidas/
  │    └─ Update all unread for gym: is_read=True, read_at=timezone.now()
  │
GET /Notificaciones/no-leidas/
       └─ Return {"count": N}
```

## File Changes

| File | Action | Description |
|------|--------|-------------|
| `gimnasioApp/models.py` | Modify | +`Notification` model + `NotificationManager`; deprecate `notified_at` help_text on `MembresiaAsignada` |
| `gimnasioApp/migrations/000X_notification.py` | Create | New migration for Notification table |
| `gimnasioApp/services/__init__.py` | Create | Empty init for new services package |
| `gimnasioApp/services/notifications.py` | Create | `NotificationManager` with `generate_for_gimnasio()` — get_or_create logic for both sources |
| `gimnasioApp/serializers.py` | Modify | +`NotificationSerializer` |
| `gimnasioApp/views.py` | Modify | +`NotificationViewSet` (4 actions); delete `membership_notifications` (L713-803) and `mark_notifications_read` (L806-832) |
| `gimnasioApp/urls.py` | Modify | +router.register for Notificaciones; remove legacy path entries (L31-32) |
| `gimnasioApp/tests.py` | Modify | +notification test classes |
| `gimnasioReact/src/model/notifications.model.ts` | Modify | Replace interface to match new backend fields |
| `gimnasioReact/src/api/action/notifications.api.ts` | Modify | Replace with 4 new API functions |
| `gimnasioReact/src/components/headerNav/NotificationMenu.tsx` | Modify | Use `getUnreadCount()`, per-item read, stable keys, correct field names |
| `gimnasioReact/src/pages/admin/notifications/NotificationsPage.tsx` | Modify | Use new API, per-item read, stable keys, link fixes |
| `gimnasioReact/src/pages/admin/calendario/CalendarioPage.tsx` | Modify | Read `?evento=<id>` on mount, fetch event, open detail modal |

## Interfaces / Contracts

### Backend: Notification Model

```python
class Notification(models.Model):
    TIPO_CHOICES = [
        ('por_vencer', 'Por vencer'),
        ('vencida', 'Vencida'),
        ('evento', 'Evento'),
    ]
    gimnasio = models.ForeignKey(Gimnasio, on_delete=models.CASCADE, related_name='notifications')
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES)
    titulo = models.CharField(max_length=200)
    mensaje = models.TextField()
    fecha = models.DateField()
    relacion_tipo = models.CharField(max_length=50, null=True, blank=True, default='')
    relacion_id = models.IntegerField(null=True, blank=True)
    link = models.TextField()
    whatsapp_link = models.TextField(null=True, blank=True)
    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'notification'
        ordering = ['-created_at']
        constraints = [
            models.UniqueConstraint(
                fields=['gimnasio', 'relacion_tipo', 'relacion_id', 'tipo'],
                name='uq_notification_idempotency'
            )
        ]
```

### Backend: NotificationSerializer

```python
class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = ['id', 'tipo', 'titulo', 'mensaje', 'fecha', 'relacion_tipo',
                  'relacion_id', 'link', 'whatsapp_link', 'is_read', 'read_at', 'created_at']
        read_only_fields = ('id', 'gimnasio', 'is_read', 'read_at', 'created_at')
```

### Backend: ViewSet actions

- `list` → `GET /Notificaciones/` — triggers generation, returns unread, ordered `-created_at`
- `marcar_leida` → `POST /Notificaciones/{id}/marcar-leida/` — sets `is_read=True`, `read_at=now()`
- `marcar_todas_leidas` → `POST /Notificaciones/marcar-todas-leidas/` — bulk update
- `no_leidas` → `GET /Notificaciones/no-leidas/` — returns `{"count": N}`

### Backend: Generation keys

| Source | get_or_create lookup |
|---|---|
| Expiring membership | `gimnasio=g, tipo='por_vencer', relacion_tipo='membership', relacion_id=ma.id` |
| Expired membership | `gimnasio=g, tipo='vencida', relacion_tipo='membership', relacion_id=ma.id` |
| Same-day event | `gimnasio=g, tipo='evento', relacion_tipo='evento', relacion_id=ev.id` |

### Frontend: Notification interface (new)

```typescript
export interface Notification {
    id: number;
    tipo: 'por_vencer' | 'vencida' | 'evento';
    titulo: string;
    mensaje: string;
    fecha: string;
    relacion_tipo: string;
    relacion_id: number | null;
    link: string;
    whatsapp_link: string | null;
    is_read: boolean;
    read_at: string | null;
    created_at: string;
}
```

### Frontend: API functions (new)

```typescript
export const getNotifications = async (): Promise<Notification[]> => { ... }
export const getUnreadCount = async (): Promise<{ count: number }> => { ... }
export const markOneRead = async (id: number): Promise<void> => { ... }
export const markAllAsRead = async (): Promise<void> => { ... }
```

### Frontend: Calendar deep link

CalendarioPage reads `useSearchParams().get('evento')` on mount. If present, calls `getEvento(id)` from `calendario.api.ts` (already exists) and sets `selectedEvent` to open the existing detail modal. Error toast on 404.

### Frontend: Icon mapping (new)

```
tipo='por_vencer' → RiInformationLine (yellow)  — was 'warning'
tipo='vencida'    → RiCloseLine (red)            — was 'danger'
tipo='evento'     → RiCheckLine (green)          — was 'success'
```

## Testing Strategy

| Layer | What to Test | Approach |
|-------|-------------|----------|
| Backend unit | Idempotency (get_or_create returns existing) | Create notification, call generate again, assert count unchanged |
| Backend unit | Multi-tenant isolation | Create notifications for gym A, query as gym B, assert empty |
| Backend unit | Permission enforcement | Unauthenticated → 401; non-admin/recepcion → 403 |
| Backend unit | Read state | Per-item read sets `is_read`+`read_at`; bulk read marks all; unread count reflects changes |
| Backend unit | Generation triggers | List endpoint creates notifications for qualifying memberships/events |
| Backend unit | Generation edge cases | Empty gym, no qualifying data, already-read items excluded from list |
| Backend integration | Legacy endpoint removal | GET `/membership-notifications/` → 404 |
| Frontend | `tsc -b` | TypeScript compilation passes |
| Frontend | `npm run build` | Production build succeeds |
| Frontend manual | Badge count | Shows unread count, not list length |
| Frontend manual | Per-item read | Click notification → disappears, badge decrements |
| Frontend manual | Membership link | Click → navigates to `/dashboard/asignar-membresia-list` (no 404) |
| Frontend manual | Calendar deep link | Navigate to `?evento=<id>` → modal opens with correct event |
| Frontend manual | Calendar deep link invalid | `?evento=999` → error toast, calendar loads normally |

## Threat Matrix

N/A — no routing, shell, subprocess, VCS/PR automation, executable-file classification, or process-integration boundary.

## Migration / Rollout

Single new migration (`000X_notification.py`) creates the `notification` table. No destructive changes: `notified_at` column kept with deprecated `help_text`. No backfill: fresh start — previously-dismissed expirations may reappear unread once post-deploy (documented, accepted). Rollback: `git revert`, drop migration, restore legacy views.

## Design Decisions Summary

| Option | Tradeoff | Decision |
|---|---|---|
| Generation in list endpoint vs management command | List = always fresh but adds latency per request; command = manual trigger only | Both: list endpoint is primary (lazy), management command exists for manual/backfill scenarios |
| Direct FK vs polymorphic `relacion_tipo/id` | Direct FK = type-safe, no orphan risk; polymorphic = flexible, one constraint, matches existing pattern | Polymorphic — follows `EventoCalendario` convention, single UniqueConstraint, rows self-contained |
| `services/notifications.py` vs inline in views.py | Services = cleaner separation, testable; inline = simpler, no new file | Services — generation logic is ~60 lines, ViewSets stay thin, testable in isolation |
| Timezone-aware local date vs `date.today()` (UTC) | Local = correct for Bogotá; UTC = simpler, works because frontend normalizes | `date.today()` — backend stores UTC, frontend `dateTime.ts` handles local display; both agree on "today" |
| No backfill vs migrate notified_at | Backfill = no reappearance; no backfill = simpler, documented one-time noise | No backfill — `notified_at` means "dismissed" not "existed"; fresh Notifications are cleaner |

## Open Questions

- [ ] None — all design decisions are resolved from proposal + specs + codebase analysis.
