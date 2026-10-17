import axios from 'axios';

const isRecord = (value: unknown): value is Record<string, unknown> =>
    typeof value === 'object' && value !== null;

/**
 * Extrae el primer mensaje legible de un body de error de DRF.
 * DRF devuelve strings, listas de strings, o dicts anidados según el serializer:
 *   { detail: "..." }, { non_field_errors: ["..."] }, { campo: ["..."] },
 *   { campo: { nested: ["..."] } }
 */
const firstMessage = (value: unknown): string | null => {
    if (Array.isArray(value)) {
        for (const item of value) {
            const message = firstMessage(item);
            if (message) return message;
        }
        return null;
    }

    if (isRecord(value)) {
        for (const item of Object.values(value)) {
            const message = firstMessage(item);
            if (message) return message;
        }
        return null;
    }

    if (typeof value === 'string' && value.trim()) {
        return value;
    }

    return null;
};

/**
 * Mensaje user-facing para un error de una request.
 * Orden importa: AxiosError extiende Error, así que debe chequearse primero.
 */
export const getApiErrorMessage = (error: unknown, fallback: string): string => {
    if (axios.isAxiosError(error)) {
        // Sin response = error de red o timeout: el detalle técnico no le sirve
        // al usuario.
        if (!error.response) return fallback;

        const data: unknown = error.response.data;

        // Un body string suele ser HTML (500 con DEBUG=True), no un mensaje.
        if (typeof data !== 'string') {
            const message = firstMessage(data);
            if (message) return message;
        }

        return fallback;
    }

    if (error instanceof Error && error.message) return error.message;

    return fallback;
};