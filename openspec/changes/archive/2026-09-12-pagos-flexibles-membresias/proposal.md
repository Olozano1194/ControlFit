# Propuesta: Pagos Flexibles de Membresias

## Intento

Sistema de pagos flexible para membresias que refleje las practicas reales de gimnasios de barrio colombianos: pago adelantado por multiples meses con descuento, pago fraccionado (mitad ahora, mitad despues), y visibilidad clara de deuda y pagos en el perfil del miembro y en las cards del dashboard.

## Alcance

### Incluido
- **Multiplicador de periodos** (1, 2, 3, 6, 12 meses) en MembresiaAsignada
- **Descuentos por volumen** automaticos segun cantidad de meses
- **Pago fraccionado**: registrar pagos parciales contra una membresia
- **Modelo PagoMembresia** para tracking de cada abono
- **Cards en Dashboard**: Por Cobrar, Al Dia, Con Deuda, Ingresos del Mes
- **Visibilidad en miembros**: total membresia, total pagado, saldo pendiente, estado de pago
- **Validaciones**: que no se pague mas del total, fechas logicas, etc.
- **Dashboard y reportes** actualizados con los nuevos campos

### Excluido
- Pasarela de pago / pago online (PSE, Nequi, etc.)
- Congelamiento / pausa de membresia
- Membresia familiar / descuento por acompanante
- Membresias combinadas (mitad basico + mitad premium)

## Capacidades

### Nuevas Capacidades
- `pago-multimensual`: pago adelantado por multiples periodos (2, 3, 6, 12 meses) con descuento progresivo
- `pago-fraccionado`: registrar pagos parciales contra una membresia (ej. 50% ahora, 50% despues)
- `estado-cuenta-miembro`: vista de total vs pagado vs saldo pendiente por miembro
- `dashboard-pagos`: cards en el home con resumen de cobranza

### Capacidades Modificadas
- Ninguna

## Enfoque Tecnico

### Modelo MembresiaAsignada — campos nuevos
multiplier = DecimalField(default=1, max_digits=4, decimal_places=1)
discount_percent = DecimalField(default=0, max_digits=5, decimal_places=2)

El save() calculara:
dias_totales = int(membresia.duration * multiplier)
price = membresia.price * multiplier * (1 - discount_percent / 100)
dateFinal = dateInitial + timedelta(days=dias_totales)

### Descuentos por volumen
| Meses | Descuento |
|-------|-----------|
| 1     | 0%        |
| 2     | 0%        |
| 3     | 5%        |
| 6     | 10%       |
| 12    | 20%       |

El recepcionista puede aceptar el descuento sugerido o modificarlo manualmente (para casos especiales).

### Nuevo modelo: PagoMembresia
- membresia_asignada FK a MembresiaAsignada (related_name='pagos')
- monto: DecimalField
- fecha_pago: auto_now_add
- metodo_pago: efectivo / transferencia / nequi
- nota: TextField opcional

### Propiedades calculadas en MembresiaAsignada
- total_pagado: suma de PagoMembresia.monto
- saldo_pendiente: price - total_pagado
- estado_pago: paid | partial | pending

### Pago fraccionado ("media membresia")
No es un campo especial. Simplemente:
1. Se asigna la membresia con multiplier=1
2. Se registra un PagoMembresia por el 50%
3. Queda saldo pendiente visible en el modulo de miembros
4. Cuando paga el resto, se registra otro PagoMembresia

### Frontend — Dashboard (Home)
Cards nuevas en el inicio:

- **Por Cobrar**: suma total de saldos pendientes de membresias activas
- **Al Dia**: miembros con membresia activa y saldo en cero
- **Con Deuda**: miembros con membresia activa pero saldo pendiente > 0
- **Ingresos Mes**: la card existente se actualiza para reflejar los nuevos calculos

Esto le da al dueno una vista rapida de la salud financiera del gimnasio.

### Frontend — Modulo de Miembros
En la lista/detalle de miembros se agrega:
- Membresia (tipo + periodos)
- Total a pagar
- Total pagado
- Saldo pendiente
- Estado (al dia / parcial / pendiente)

## Areas Afectadas

| Archivo | Impacto | Cambio |
|---------|---------|--------|
| gimnasioApp/models.py | Modificado | +multiplier, discount_percent en MembresiaAsignada; nuevo PagoMembresia |
| gimnasioApp/serializers.py | Modificado | +multiplier, discount_percent; nuevo PagoMembresiaSerializer |
| gimnasioApp/views.py | Modificado | +PagoMembresiaViewSet; Home/Dashboard con datos de cobranza |
| gimnasioApp/urls.py | Modificado | +ruta pagos |
| gimnasioReact/src/model/*.ts | Modificado | +tipos multiplier, discount, PagoMembresia |
| gimnasioReact/src/api/action/*.ts | Modificado | +API calls pagos |
| gimnasioReact/src/pages/admin/asignadaMemberShips/AsignarMemberShipsForm.tsx | Modificado | +multiplier + descuento + preview precio |
| gimnasioReact/src/pages/admin/asignadaMemberShips/ListAsignarMemberShips.tsx | Modificado | +columnas estado pago |
| gimnasioReact/src/pages/admin/registroPorMes/ListMiembro.tsx | Modificado | +estado de cuenta |
| gimnasioReact/src/components/home/MetricsSection.tsx | Modificado | +cards Por Cobrar, Al Dia, Con Deuda |
| gimnasioApp/views.py (Home, Dashboard, ExportReport) | Modificado | Sumas y stats actualizados |

## Riesgos

| Riesgo | Prob. | Mitigacion |
|--------|-------|------------|
| Registros existentes sin multiplier/discount | Baja | Default=1 y 0; migracion sin perdida |
| Pago fraccionado sin control (pagar de mas) | Baja | Validacion: monto no puede exceder saldo pendiente |
| Multiplier decimal + duraciones non-redondas | Baja | int(duration * multiplier) trunca al dia exacto |

## Plan de Rollback

Revertir migraciones de multiplier, discount_percent y tabla pago_membresia. Registros existentes preservan price y dateFinal. Restaurar frontend a git anterior.

## Dependencias

- Migracion DB (2 campos nuevos en MembresiaAsignada + tabla PagoMembresia)

## Criterios de Exito

- [ ] Asignar membresia x3 meses: precio con 5% descuento, dateFinal a 90 dias
- [ ] Asignar membresia x12 meses: precio con 20% descuento, dateFinal a 360 dias
- [ ] Registrar pago parcial: saldo pendiente se actualiza
- [ ] Pagar el total: estado cambia a "paid"
- [ ] Vista de miembros muestra total, pagado, saldo y estado
- [ ] Dashboard muestra cards de Por Cobrar, Al Dia, Con Deuda
- [ ] No se puede pagar mas del saldo pendiente
