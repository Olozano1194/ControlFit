import { axiosPublic } from "../axios/axios.public";
import {
  LoginUserDto,
  LoginResponse,
} from "../../model/dto/user.dto";

export const login = async (
  credentials: LoginUserDto
): Promise<LoginResponse> => {
  const { data } = await axiosPublic.post<LoginResponse>("/token/", credentials);
  return data;
};
