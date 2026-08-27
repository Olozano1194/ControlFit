export interface User {
    id: number;
    name: string;
    lastname: string;
    email: string;
    roles: string;
    password: string;
    avatar?: string | File;
    repeatPass?: string;
    gimnasio?: number;
    gimnasio_name?: string;
    must_change_password?: boolean;
};