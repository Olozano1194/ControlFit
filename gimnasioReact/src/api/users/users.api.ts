import { axiosPrivate } from "../axios/axios.private";
import { axiosPublic } from "../axios/axios.public";
//Models
import { User } from "../../model/user.model";
//DTO
import { CreateUserDto } from "../../model/dto/user.dto";

// Registro público (sin token) - crea usuario Y gimnasio automáticamente
export const registerUser = async (user: CreateUserDto) => {
  const response = await axiosPublic.post("/register/", user);
  return response.data;
};

// Creamos un usuario (requiere estar logueado)
export const CreateUsers = async (user: CreateUserDto) => {
  const formData = new FormData();

  if (user.name) formData.append("name", user.name);
  if (user.lastname) formData.append("lastname", user.lastname);
  if (user.email) formData.append("email", user.email);
  if (user.password) formData.append("password", user.password);
  if (typeof user.roles === "string") formData.append("roles", user.roles);
  if (user.avatar) formData.append("avatar", user.avatar);  

  const response = await axiosPrivate.post("/User/", formData);    
  return response.data;
};

//function profile
export const getUserProfile = async (): Promise<{ user: User }> => {
 const response = await axiosPrivate.get(`/me/`);
  return response.data;
};

//Lista de usuarios
export const getUsers = async () => {
  const response = await axiosPrivate.get<User[]>("/User/");
  return response.data; 
};

//Actualizar Usuario
export const updateUser = async (
  id: number,
  user: CreateUserDto
) => {
  const formData = new FormData();

  if (user.name) formData.append("name", user.name);
  if (user.lastname) formData.append("lastname", user.lastname);
  // if (typeof user.roles === "string") formData.append("roles", user.roles);
  //if (user.email) formData.append('email', user.email);

  if (user.avatar) {
    formData.append("avatar", user.avatar);
  }

  const response = await axiosPrivate.put<User>(`/User/${id}/`, formData);
  return response.data;
};
