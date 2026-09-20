import { axiosPublic } from '../axios/axios.public';  
import { axiosPrivate } from '../axios/axios.private';
import { setCsrfToken } from '../../utils/authStorage';

export const refreshAccessToken = async (): Promise<string> => {
  const { data } = await axiosPublic.post('/token/refresh/');
  if (data.csrf_token) setCsrfToken(data.csrf_token);
  return data.access;
};

export const verifyToken = async (): Promise<{ valid: boolean; exp?: number }> => {
  const { data } = await axiosPrivate.get('/token/verify/');
  return data;
};