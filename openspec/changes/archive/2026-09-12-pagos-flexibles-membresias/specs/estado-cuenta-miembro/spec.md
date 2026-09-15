# Estado de Cuenta del Miembro Specification

## Purpose

Proporcionar visibilidad del estado financiero de cada miembro en el modulo de miembros: total de membresia, total pagado, saldo pendiente, y estado de pago.

## Requirements

### Requirement: Propiedades calculadas en MembresiaAsignada

El sistema MUST exponer las siguientes propiedades calculadas en cada MembresiaAsignada: total_pagado, saldo_pendiente, y estado_pago.

#### Scenario: Miembro al dia

- GIVEN una MembresiaAsignada con price = 100.000 y pagos registrados por 100.000
- WHEN se consulta la membresia
- THEN total_pagado = 100.000, saldo_pendiente = 0, estado_pago = "paid"

#### Scenario: Miembro con pago parcial

- GIVEN una MembresiaAsignada con price = 100.000 y pagos registrados por 50.000
- WHEN se consulta la membresia
- THEN total_pagado = 50.000, saldo_pendiente = 50.000, estado_pago = "partial"

#### Scenario: Miembro sin pagos

- GIVEN una MembresiaAsignada con price = 100.000 y ningun pago registrado
- WHEN se consulta la membresia
- THEN total_pagado = 0, saldo_pendiente = 100.000, estado_pago = "pending"

### Requirement: Vista en modulo de miembros

El sistema MUST mostrar en la lista de miembros las siguientes columnas: membresia (tipo + periodos), total a pagar, total pagado, saldo pendiente, y estado de pago.

#### Scenario: Lista de miembros con estado

- GIVEN dos miembros: uno al dia y otro con deuda parcial
- WHEN se accede al listado de miembros
- THEN cada fila muestra nombre, membresia, total, pagado, saldo, y un badge de estado
- AND el miembro al dia muestra badge verde "Al dia"
- AND el miembro con deuda muestra badge amarillo "Parcial"

### Requirement: Badge de estado de pago

El sistema MUST mostrar un indicador visual del estado de pago: verde para "paid", amarillo para "partial", rojo para "pending".

#### Scenario: Miembro sin pagar

- GIVEN un miembro con MembresiaAsignada en estado "pending"
- WHEN se lista en la tabla
- THEN se muestra un badge rojo con texto "Pendiente"

### Requirement: Detalle de pagos por miembro

El sistema SHOULD permitir acceder al detalle de pagos de un miembro especifico, mostrando cada abono registrado con fecha, monto, metodo, y nota.

#### Scenario: Ver historial de pagos

- GIVEN un miembro con MembresiaAsignada que tiene 2 pagos registrados
- WHEN se hace clic en ver detalle del miembro
- THEN se muestra tabla con fecha, monto, metodo, y nota de cada pago
