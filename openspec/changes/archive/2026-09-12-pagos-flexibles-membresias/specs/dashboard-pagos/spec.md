# Dashboard de Pagos Specification

## Purpose

Agregar cards informativas en la pagina de inicio (Home/Dashboard) que muestren el resumen financiero de cobranza: total por cobrar, cantidad de miembros al dia, cantidad de miembros con deuda, e ingresos del mes actualizados.

## Requirements

### Requirement: Card "Por Cobrar"

El sistema MUST mostrar una card en el dashboard con la suma total de saldos pendientes de todas las MembresiaAsignada activas del gimnasio.

#### Scenario: Total por cobrar

- GIVEN 3 membresias activas con saldos pendientes de 50.000, 30.000 y 0
- WHEN se carga el dashboard
- THEN la card "Por Cobrar" muestra 80.000

#### Scenario: Sin deudas pendientes

- GIVEN todas las membresias activas con saldo_pendiente = 0
- WHEN se carga el dashboard
- THEN la card "Por Cobrar" muestra 0

### Requirement: Card "Al Dia"

El sistema MUST mostrar una card con el conteo de miembros que tienen membresia activa Y estado_pago = "paid".

#### Scenario: Miembros al dia

- GIVEN 10 membresias activas, de las cuales 7 tienen estado "paid" y 3 "partial"
- WHEN se carga el dashboard
- THEN la card "Al Dia" muestra 7

### Requirement: Card "Con Deuda"

El sistema MUST mostrar una card con el conteo de miembros que tienen membresia activa Y estado_pago = "partial" o "pending".

#### Scenario: Miembros con deuda

- GIVEN 10 membresias activas, 7 "paid" y 3 "partial"
- WHEN se carga el dashboard
- THEN la card "Con Deuda" muestra 3

### Requirement: Card "Ingresos del Mes" actualizada

El sistema MUST actualizar la card existente de "Ingresos del Mes" para que calcule correctamente los ingresos considerando los nuevos campos multiplier y discount_percent. La card MUST sumar el price de todas las MembresiaAsignada creadas en el mes actual.

#### Scenario: Ingresos del mes con descuentos

- GIVEN 2 membresias creadas este mes: una con price = 150.000 (multiplier=3, descuento incluido) y otra con price = 50.000
- WHEN se carga el dashboard
- THEN la card "Ingresos del Mes" muestra 200.000

#### Scenario: Ingresos sin membresias nuevas

- GIVEN ninguna membresia creada este mes
- WHEN se carga el dashboard
- THEN la card "Ingresos del Mes" muestra 0

### Requirement: Cards visibles solo para el gimnasio del usuario

El sistema MUST filtrar todas las cards de dashboard por el gimnasio del usuario autenticado (multi-tenant).

#### Scenario: Multi-gimnasio

- GIVEN dos gimnasios con diferentes miembros y pagos
- WHEN un usuario del Gimnasio A carga el dashboard
- THEN las cards solo muestran datos del Gimnasio A
