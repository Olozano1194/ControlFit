# Pago Multimensual Specification

## Purpose

Permitir que un miembro pague por adelantado multiples periodos consecutivos de una membresia (2, 3, 6, 12 meses) con descuento progresivo por volumen, manteniendo el precio total y la fecha final calculados automaticamente.

## Requirements

### Requirement: Asignacion con multiplicador de periodos

El sistema MUST permitir especificar un multiplicador de periodos (1, 2, 3, 6, 12) al asignar una membresia a un miembro. El valor por defecto MUST ser 1 (comportamiento actual).

#### Scenario: Asignacion normal sin multiplicador

- GIVEN un miembro sin membresia activa
- WHEN se asigna una membresia de 30 dias con precio 50.000 sin especificar multiplier
- THEN el sistema calcula price = 50.000, dateFinal = dateInitial + 30 dias
- AND multiplier queda registrado como 1

#### Scenario: Asignacion con 3 meses de anticipo

- GIVEN un miembro sin membresia activa
- WHEN se asigna una membresia de 30 dias con precio 50.000 y multiplier = 3
- THEN el sistema calcula price = 50.000 * 3 = 150.000
- AND dateFinal = dateInitial + 90 dias

#### Scenario: Asignacion con 12 meses de anticipo

- GIVEN un miembro sin membresia activa
- WHEN se asigna una membresia de 30 dias con precio 50.000 y multiplier = 12
- THEN el sistema calcula price = 50.000 * 12 = 600.000
- AND dateFinal = dateInitial + 360 dias

### Requirement: Descuento automatico por volumen

El sistema SHOULD sugerir un descuento porcentual automatico segun la tabla definida: 1-2 meses = 0%, 3 meses = 5%, 6 meses = 10%, 12 meses = 20%. El recepcionista MAY modificar el descuento manualmente.

#### Scenario: Descuento sugerido para 6 meses

- GIVEN una membresia con precio 50.000
- WHEN se asigna con multiplier = 6
- THEN el sistema sugiere discount_percent = 10%
- AND price calculado = 50.000 * 6 * 0.9 = 270.000

#### Scenario: Descuento editado manualmente

- GIVEN una membresia con precio 50.000
- WHEN se asigna con multiplier = 6 y el recepcionista cambia discount_percent a 15%
- THEN el sistema calcula price = 50.000 * 6 * 0.85 = 255.000

### Requirement: Validacion de multiplicador

El sistema MUST rechazar valores de multiplier menores a 1 o que no esten en la lista permitida (1, 2, 3, 6, 12).

#### Scenario: Multiplicador invalido

- GIVEN el formulario de asignacion de membresia
- WHEN se ingresa multiplier = 0
- THEN el sistema MUST rechazar con error "El multiplicador debe ser al menos 1"

#### Scenario: Multiplicador no soportado

- GIVEN el formulario de asignacion de membresia
- WHEN se ingresa multiplier = 5
- THEN el sistema SHOULD advertir que no hay descuento definido para ese valor pero permitir la operacion

### Requirement: Migracion de registros existentes

El sistema MUST asignar multiplier = 1 y discount_percent = 0 a todos los registros existentes de MembresiaAsignada que no tengan estos campos.

#### Scenario: Registro legacy sin multiplicador

- GIVEN un MembresiaAsignada creado antes de esta migracion
- WHEN se ejecuta la migracion
- THEN multiplier = 1 y discount_percent = 0
- AND price y dateFinal existentes NO se modifican
