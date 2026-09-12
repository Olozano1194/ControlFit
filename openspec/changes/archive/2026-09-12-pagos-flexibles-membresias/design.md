# Design: Pagos Flexibles de Membresias

## Technical Approach

Extender el modelo `MembresiaAsignada` existente con campos `multiplier` y `discount_percent`, y crear un nuevo modelo `PagoMembresia` para tracking de abonos. El `save()` de `MembresiaAsignada` se sobreescribe para calcular `price` y `dateFinal` usando multiplier y descuento. El frontend agrega selects de periodo, preview de precio, y un modal de registro de pagos. Las cards del dashboard se amplian con metricas de cobranza.

## Architecture Decisions

| Decision | Choice | Alternatives | Rationale |
|----------|--------|--------------|-----------|
| PagoMembresia como modelo nuevo | Modelo separado con FK a MembresiaAsignada | Agregar campos de pago a MembresiaAsignada | Un solo pago por membresia limitaria el caso de uso real (50% ahora, 50% despues). Modelo separado permite N pagos, historial, y metodo de pago por abono |
| Descuento auto-suggest + override | Select con valores predefinidos + input editable | Solo auto-calcular o solo manual | El recepcionista colombiano necesita flexibilidad para casos especiales (descuento por amigo, promocion) pero tambien rapidez con sugerencias |
| Estado de pago como propiedad calculada | Property en serializer (no campo persistido) | Campo guardado en DB | Evita inconsistencias: el estado siempre refleja la suma real de pagos. No necesita migracion adicional ni sincronizacion |
| Precio calculado en save() | Sobreescribir save() con calculo | Calcular en serializer o signal | Centraliza la logica en el modelo, funciona desde admin, API, y cualquier otro entry point. El serializer solo pasa multiplier y discount |
| Dashboard stats en vista existente | Extender Home/DashboardStatsView | Crear vista nueva | Ya retorna los datos del home; agregar 4 campos mas mantiene un solo endpoint para MetricsSection |

## Data Flow

```
Frontend (AsignarMemberShipsForm)
  │
  ├─ Select multiplicador (1,2,3,6,12)
  ├─ Input descuento (auto-sugerido, editable)
  ├─ Preview: price = base * multiplier * (1 - discount/100)
  │
  └─ POST /MemberShipsAsignada/
       │
       ▼
  MembresiaAsignadaSerializer.create()
       │
       ▼
  MembresiaAsignada.save()
       ├─ price = membresia.price * multiplier * (1 - discount_percent/100)
       ├─ dateFinal = dateInitial + timedelta(days=int(membresia.duration * multiplier))
       └─ DB INSERT
       │
       ▼
  ──── Registro de pago (despues) ────
       │
  POST /MemberShipsAsignada/{id}/pagos/
       │
       ▼
  PagoMembresiaSerializer.create()
       ├─ Validar: monto <= saldo_pendiente
       ├─ Validar: monto > 0
       └─ DB INSERT (monto, metodo_pago, fecha_pago=auto_now_add)
       │
       ▼
  GET /home/ → DashboardStatsView
       ├─ por_cobrar: suma(saldo_pendiente) membresias activas
       ├─ al_dia: count(membresias activas where estado_pago=paid)
       ├─ con_deuda: count(membresias activas where estado_pago!=paid)
       └─ total_month: suma(price) membresias creadas este mes
```

## File Changes

| Archivo | Accion | Descripcion |
|---------|--------|-------------|
| `gimnasioApp/models.py` | Modificar | +multiplier, +discount_percent en MembresiaAsignada; +PagoMembresia model; override save() |
| `gimnasioApp/serializers.py` | Modificar | +multiplier, +discount_percent en MembresiaAsignadaSerializer; +PagoMembresiaSerializer; propiedades calculadas |
| `gimnasioApp/views.py` | Modificar | +PagoMembresiaViewSet; extender Home/DashboardStatsView con datos de cobranza |
| `gimnasioApp/urls.py` | Modificar | +route pagos nested en MemberShipsAsignada |
| `gimnasioReact/src/model/asignarMemberShips.model.ts` | Modificar | +multiplier, +discount_percent, +total_pagado, +saldo_pendiente, +estado_pago |
| `gimnasioReact/src/model/dto/asignarMemberShips.dto.ts` | Modificar | +multiplier, +discount_percent en CreateAsignarMemberShipsDto |
| `gimnasioReact/src/model/pagoMembresia.model.ts` | Crear | Interfaz PagoMembresia con id, monto, fecha_pago, metodo_pago, nota |
| `gimnasioReact/src/api/action/pagoMembresia.api.ts` | Crear | CRUD pagos: createPago, getPagosByMembresia |
| `gimnasioReact/src/api/action/asignarMemberShips.api.ts` | Modificar | Actualizar tipos de respuesta |
| `gimnasioReact/src/pages/admin/asignadaMemberShips/AsignarMemberShipsForm.tsx` | Modificar | +Select multiplier, +input discount, +price preview |
| `gimnasioReact/src/pages/admin/asignadaMemberShips/ListAsignarMemberShips.tsx` | Modificar | +columna estado_pago con badge |
| `gimnasioReact/src/pages/admin/asignadaMemberShips/PagoMembresiaModal.tsx` | Crear | Modal para registrar pago parcial |
| `gimnasioReact/src/pages/admin/registroPorMes/ListMiembro.tsx` | Modificar | +columnas total, pagado, saldo, estado |
| `gimnasioReact/src/components/home/MetricsSection.tsx` | Modificar | +cards Por Cobrar, Al Dia, Con Deuda |

## Interfaces / Contracts

### Endpoint: POST `/MemberShipsAsignada/{id}/pagos/`

```json
// Request
{
  "monto": 50000,
  "metodo_pago": "efectivo|transferencia|nequi",
  "nota": "Abono inicial (opcional)"
}

// Response 201
{
  "id": 1,
  "membresia_asignada": 15,
  "monto": "50000.00",
  "metodo_pago": "efectivo",
  "fecha_pago": "2026-07-13T10:30:00Z",
  "nota": "Abono inicial"
}
```

### Endpoint: GET `/MemberShipsAsignada/{id}/pagos/`

```json
// Response 200
[
  { "id": 2, "monto": "50000.00", "metodo_pago": "nequi", "fecha_pago": "2026-07-13T14:00:00Z" },
  { "id": 1, "monto": "50000.00", "metodo_pago": "efectivo", "fecha_pago": "2026-07-13T10:30:00Z" }
]
```

### MembresiaAsignadaSerializer — campos adicionales

```python
# Campos de entrada (write)
multiplier = DecimalField(default=1, max_digits=4, decimal_places=1)
discount_percent = DecimalField(default=0, max_digits=5, decimal_places=2)

# Campos calculados (read-only)
total_pagado = DecimalField()    # suma pagos
saldo_pendiente = DecimalField() # price - total_pagado
estado_pago = CharField()        # "paid" | "partial" | "pending"
```

### Home/Dashboard — respuesta ampliada

```json
{
  "num_miembros": 15,
  "total_month": 2500000,
  "por_cobrar": 450000,
  "al_dia": 12,
  "con_deuda": 3
}
```

### DTO TypeScript

```typescript
// model/dto/asignarMemberShips.dto.ts
interface CreateAsignarMemberShipsDto {
  membresia: number;
  miembro: number;
  dateInitial: string;
  multiplier?: number;        // default 1
  discount_percent?: number;  // default 0
}

// model/pagoMembresia.model.ts
interface PagoMembresia {
  id: number;
  membresia_asignada: number;
  monto: number;
  metodo_pago: 'efectivo' | 'transferencia' | 'nequi';
  fecha_pago: string;
  nota?: string;
}
```

## Testing Strategy

| Capa | Que probar | Enfoque |
|------|-----------|---------|
| Unit | save() de MembresiaAsignada calcula price/dateFinal con multiplier y discount | TestCase con asserts en precio y fecha |
| Unit | PagoMembresia validacion: monto no excede saldo | TestCase con sobrepago |
| Unit | Propiedades total_pagado, saldo_pendiente, estado_pago | TestCase con diferentes estados de pago |
| Integration | POST pagos crea registro y actualiza estado | APIClient con transacciones |
| Integration | Dashboard stats retornan valores correctos | APIClient mockeando membresias activas |
| E2E | Flujo completo: asignar membresia x3 meses, registrar pago parcial, verificar saldo | Playwright o similar |

## Migration

```python
# Migration para MembresiaAsignada — campos nuevos
# Los defaults (1 y 0) preservan registros existentes
# price y dateFinal NO se recalculan para registros legacy

class Migration(migrations.AddField):
    model_name='membresiaasignada',
    name='multiplier',
    field=models.DecimalField(default=1, max_digits=4, decimal_places=1)

class Migration(migrations.AddField):
    model_name='membresiaasignada',
    name='discount_percent',
    field=models.DecimalField(default=0, max_digits=5, decimal_places=2)

# Nueva tabla PagoMembresia
class Migration(migrations.CreateModel):
    name='PagoMembresia',
    fields=[
        ('id', models.AutoField(...)),
        ('membresia_asignada', models.ForeignKey(..., related_name='pagos')),
        ('monto', models.DecimalField(max_digits=10, decimal_places=2)),
        ('fecha_pago', models.DateTimeField(auto_now_add=True)),
        ('metodo_pago', models.CharField(choices=[...])),
        ('nota', models.TextField(blank=True)),
    ]
```

SQLite maneja estos campos nativamente. Sin cambios de esquema que requieran data migration compleja. Los registros existentes quedan con multiplier=1 y discount_percent=0, comportamiento identico al actual.

## Open Questions

- [ ] Mantener el calculo de price en `create()` del serializer o moverlo exclusivamente al `save()` del modelo? Actualmente `create()` hace `validated_data['price'] = validated_data['membresia'].price`. Con el cambio, `save()` sobreescribe este valor, por lo que `create()` se puede simplificar.
- [ ] Para `ListMiembro`, se necesita un serializer de UsuarioGym que incluya el estado de cuenta de la membresia activa. Actualmente `UsuarioGymSerializer` no trae datos de `MembresiaAsignada`. Se propone un endpoint o serializer anidado.
