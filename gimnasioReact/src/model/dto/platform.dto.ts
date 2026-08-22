export interface PlatformStats {
    total_gimnasios: number;
    gimnasios_activos: number;
    total_usuarios_staff: number;
    demo_pendientes: number;
    demo_contactados: number;
    ingresos_mes_global: string;
    miembros_activos_global: number;
    retencion_promedio: string;
}

export interface GimnasioPlatform {
    id: number;
    name: string;
    address: string;
    phone: string;
    is_active: boolean;
    created_at: string;
    usuarios_count: number;
    miembros_activos_count: number;
    ingresos_mes: string;
}

export interface UsuarioPlatform {
    id: number;
    email: string;
    name: string;
    lastname: string;
    roles: 'admin' | 'recepcion' | 'superadmin';
    is_active: boolean;
}

export interface MiembroActivo {
    id: number;
    name: string;
    lastname: string;
    membresia: string;
    dateFinal: string;
    saldo_pendiente: string;
}

export interface PagoPlatform {
    id: number;
    monto: string;
    fecha_pago: string;
    metodo_pago: string;
    miembro_name: string;
    miembro_lastname: string;
    membresia_name: string;
}

export interface GimnasioPlatformDetail extends GimnasioPlatform {
    usuarios: UsuarioPlatform[];
    miembros_activos: MiembroActivo[];
    ultimos_pagos: PagoPlatform[];
}

export interface PaginatedResponse<T> {
    count: number;
    next: string | null;
    previous: string | null;
    results: T[];
}

export interface GimnasioCreateDto {
    name: string;
    address?: string;
    phone?: string;
}