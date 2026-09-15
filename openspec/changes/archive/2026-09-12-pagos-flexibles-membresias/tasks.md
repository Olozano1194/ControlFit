# Tasks: Pagos Flexibles de Membresias

## Review Workload Forecast

| Field | Value |
|-------|-------|
| Estimated changed lines | 350-500 |
| 400-line budget risk | Medium |
| Chained PRs recommended | No |
| Suggested split | Single PR |
| Delivery strategy | ask-on-risk |

Decision needed before apply: No
Chained PRs recommended: No
Chain strategy: size-exception
400-line budget risk: Medium

## Phase 1: Backend Foundation (Modelos y Migracion)

- [x] 1.1 Agregar campos `multiplier` (Decimal, default=1) y `discount_percent` (Decimal, default=0) a MembresiaAsignada
- [x] 1.2 Sobreescribir `save()` en MembresiaAsignada: calcular `price = membresia.price * multiplier * (1 - discount_percent/100)` y `dateFinal = dateInitial + timedelta(days=int(membresia.duration * multiplier))`
- [x] 1.3 Agregar propiedades calculadas: `total_pagado` (sum pagos), `saldo_pendiente` (price - total_pagado), `estado_pago` (paid/partial/pending)
- [x] 1.4 Crear modelo `PagoMembresia` con FK a MembresiaAsignada, monto, fecha_pago, metodo_pago, nota
- [x] 1.5 Generar migracion de base de datos y ejecutarla

## Phase 2: Backend API (Serializers y Views)

- [x] 2.1 Actualizar `MembresiaAsignadaSerializer`: agregar multiplier y discount_percent como writables; agregar total_pagado, saldo_pendiente, estado_pago como read-only; limpiar `create()` de price manual
- [x] 2.2 Crear `PagoMembresiaSerializer`: validar monto > 0 y monto <= saldo_pendiente
- [x] 2.3 Crear `PagoMembresiaViewSet` (o View anidado) en `MemberShipsAsignada/{id}/pagos/` con POST y GET
- [x] 2.4 Registrar ruta anidada en urls.py
- [x] 2.5 Extender `Home` / `DashboardStatsView` con `por_cobrar`, `al_dia`, `con_deuda`
- [x] 2.6 Migrar price manual en `MembresiaAsignadaSerializer.create()` al save() del modelo

## Phase 3: Frontend Types y API

- [x] 3.1 Actualizar `asignarMemberShips.dto.ts`: +multiplier?, +discount_percent?
- [x] 3.2 Actualizar `asignarMemberShips.model.ts`: +multiplier, +discount_percent, +total_pagado, +saldo_pendiente, +estado_pago
- [x] 3.3 Crear `pagoMembresia.model.ts`: interfaz con id, membresia_asignada, monto, metodo_pago, fecha_pago, nota
- [x] 3.4 Crear `api/action/pagoMembresia.api.ts`: funciones createPago y getPagosByMembresia

## Phase 4: Frontend UI

- [x] 4.1 Modificar `AsignarMemberShipsForm.tsx`: agregar Select de multiplier (1,2,3,6,12), input de discount_percent auto-sugerido, y preview de precio calculado en tiempo real
- [x] 4.2 Crear `PagoMembresiaModal.tsx`: modal para registrar pago parcial con monto, metodo_pago, nota; validar que no exceda saldo
- [x] 4.3 Modificar `ListAsignarMemberShips.tsx`: agregar columna estado_pago con badge (verde/amarillo/rojo) y boton "Registrar Pago"
- [x] 4.4 Modificar `ListMiembro.tsx`: agregar columnas de total membresia, total pagado, saldo pendiente, estado
- [x] 4.5 Modificar `MetricsSection.tsx`: agregar cards de Por Cobrar, Al Dia, Con Deuda

## Phase 5: Testing

- [x] 5.1 Test unitario: `MembresiaAsignada.save()` calcula price y dateFinal con multiplier=3 y discount=5%
- [x] 5.2 Test unitario: `MembresiaAsignada.save()` con multiplier=12 y discount=20%
- [x] 5.3 Test unitario: validacion PagoMembresia monto no excede saldo_pendiente
- [x] 5.4 Test unitario: propiedades total_pagado, saldo_pendiente, estado_pago
- [x] 5.5 Test integracion: POST pago registra abono y actualiza estado
- [x] 5.6 Test integracion: GET /home/ retorna por_cobrar, al_dia, con_deuda correctos
