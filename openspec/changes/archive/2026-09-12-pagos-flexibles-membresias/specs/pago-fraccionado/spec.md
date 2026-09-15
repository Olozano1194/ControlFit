# Pago Fraccionado Specification

## Purpose

Permitir registrar pagos parciales contra una membresia asignada, de modo que un miembro pueda pagar en cuotas (ej. 50% ahora, 50% despues). Cada abono queda registrado con metodo de pago y fecha.

## Requirements

### Requirement: Registro de pagos parciales

El sistema MUST permitir registrar uno o mas pagos parciales contra una MembresiaAsignada existente a traves del modelo PagoMembresia.

#### Scenario: Pago del 50% inicial

- GIVEN una MembresiaAsignada con price = 100.000 y saldo_pendiente = 100.000
- WHEN se registra un PagoMembresia con monto = 50.000
- THEN el pago se guarda con fecha actual
- AND saldo_pendiente se actualiza a 50.000
- AND estado_pago cambia a "partial"

#### Scenario: Pago completo del saldo restante

- GIVEN una MembresiaAsignada con price = 100.000, saldo_pendiente = 50.000
- WHEN se registra un PagoMembresia con monto = 50.000
- THEN saldo_pendiente = 0
- AND estado_pago cambia a "paid"

#### Scenario: Pago unico del total

- GIVEN una MembresiaAsignada con price = 100.000
- WHEN se registra un PagoMembresia con monto = 100.000
- THEN estado_pago = "paid" inmediatamente

### Requirement: Validacion de monto

El sistema MUST rechazar un PagoMembresia cuyo monto exceda el saldo_pendiente de la MembresiaAsignada.

#### Scenario: Intento de sobrepago

- GIVEN una MembresiaAsignada con price = 100.000 y saldo_pendiente = 30.000
- WHEN se intenta registrar un PagoMembresia con monto = 50.000
- THEN el sistema MUST rechazar con error "El monto excede el saldo pendiente"

#### Scenario: Monto cero o negativo

- GIVEN una MembresiaAsignada con saldo_pendiente = 100.000
- WHEN se intenta registrar un PagoMembresia con monto = 0
- THEN el sistema MUST rechazar con error "El monto debe ser mayor a cero"

### Requirement: Metodo de pago

El sistema MUST permitir seleccionar el metodo de pago al registrar un PagoMembresia: efectivo, transferencia, o nequi.

#### Scenario: Pago por Nequi

- GIVEN el formulario de registro de pago
- WHEN se registra un PagoMembresia por 50.000 con metodo "nequi"
- THEN el pago se guarda con metodo_pago = "nequi"

### Requirement: Nota opcional

El sistema MAY permitir agregar una nota textual al PagoMembresia para registrar informacion adicional.

#### Scenario: Pago con nota

- GIVEN el formulario de registro de pago
- WHEN se registra un pago con nota "Abono de Juan, queda debiendo 50mil"
- THEN la nota se guarda asociada al pago

### Requirement: Historial de pagos

El sistema MUST exponer el historial completo de pagos asociado a cada MembresiaAsignada, ordenado por fecha descendente.

#### Scenario: Consultar pagos de una membresia

- GIVEN una MembresiaAsignada con 3 pagos registrados
- WHEN se consultan los pagos de esa membresia
- THEN se listan los 3 pagos ordenados del mas reciente al mas antiguo
