"""Test package for gimnasioApp.

Re-exports all test modules for backwards compatibility.
"""

from .test_membresia_asignada_save import MembresiaAsignadaSaveTest
from .test_pago_membresia_validacion import PagoMembresiaValidacionTest
from .test_membresia_asignada_propiedades import MembresiaAsignadaPropiedadesTest
from .test_pago_membresia_integracion import PagoMembresiaIntegracionTest
from .test_membresia_asignada_suspender import MembresiaAsignadaSuspenderTest
from .test_membresia_asignada_cambiar_plan import MembresiaAsignadaCambiarPlanTest
from .test_membresia_asignada_devolucion import MembresiaAsignadaDevolucionTest
from .test_membresia_asignada_renovar import MembresiaAsignadaRenovarTest

__all__ = [
    'MembresiaAsignadaSaveTest',
    'PagoMembresiaValidacionTest',
    'MembresiaAsignadaPropiedadesTest',
    'PagoMembresiaIntegracionTest',
    'MembresiaAsignadaSuspenderTest',
    'MembresiaAsignadaCambiarPlanTest',
    'MembresiaAsignadaDevolucionTest',
    'MembresiaAsignadaRenovarTest',
]