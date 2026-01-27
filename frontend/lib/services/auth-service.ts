export interface User {
    id: string;
    email: string;
    name?: string;
}

export interface AuthService {
    getCurrentUser(): Promise<User>;
}
