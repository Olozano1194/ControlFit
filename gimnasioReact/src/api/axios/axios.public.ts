import axios from "axios";

const baseURL = import.meta.env.MODE === 'development' 
              ? import.meta.env.VITE_API_URL_DEV
              : import.meta.env.VITE_API_URL_PROD;

export const axiosPublic = axios.create({   
    baseURL, 
    withCredentials: true,  // Necesario para enviar la cookie HTTP-only del refresh token
    headers: {
        'Content-Type': 'application/json',
    },
});  

// Re-export for axios.private.ts to avoid circular imports
export { baseURL };  