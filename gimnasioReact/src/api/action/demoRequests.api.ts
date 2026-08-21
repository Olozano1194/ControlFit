import { axiosPrivate } from "../axios/axios.private";

export type DemoRequest = {
    id: number;
    nombre: string;
    email: string;
    telefono: string;
    nombre_gimnasio: string;
    estado: 'pendiente' | 'contactado';
    fecha_solicitud: string;
};

export const getDemoRequests = async (): Promise<DemoRequest[]> => {
    const response = await axiosPrivate.get<DemoRequest[]>('/solicitudes-demo/');
    return response.data;
};

export const updateDemoRequestEstado = async (id: number, estado: 'pendiente' | 'contactado'): Promise<DemoRequest> => {
    const response = await axiosPrivate.patch<DemoRequest>(`/solicitudes-demo/${id}/`, { estado });
    return response.data;
};
