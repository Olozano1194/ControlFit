import { axiosPrivate } from "../axios/axios.private";
import type {
    PlatformStats,
    GimnasioPlatform,
    GimnasioPlatformDetail,
    GimnasioCreateDto,
    PaginatedResponse,
} from "../../model/dto/platform.dto";

export const getPlatformStats = async (): Promise<PlatformStats> => {
    const response = await axiosPrivate.get<PlatformStats>('/platform/stats/');
    return response.data;
};

export const getGimnasios = async (page?: number, search?: string): Promise<PaginatedResponse<GimnasioPlatform>> => {
    const params: { page?: number; search?: string } = {};
    if (page) params.page = page;
    if (search) params.search = search;
    const response = await axiosPrivate.get<PaginatedResponse<GimnasioPlatform>>('/platform/gimnasios/', { params });
    return response.data;
};

export const getGimnasioDetail = async (id: number): Promise<GimnasioPlatformDetail> => {
    const response = await axiosPrivate.get<GimnasioPlatformDetail>(`/platform/gimnasios/${id}/`);
    return response.data;
};

export const toggleGimnasioActive = async (id: number, is_active: boolean): Promise<GimnasioPlatform> => {
    const response = await axiosPrivate.patch<GimnasioPlatform>(`/platform/gimnasios/${id}/`, { is_active });
    return response.data;
};

export const createGimnasio = async (dto: GimnasioCreateDto): Promise<GimnasioPlatform> => {
    const response = await axiosPrivate.post<GimnasioPlatform>('/platform/gimnasios/', dto);
    return response.data;
};