import { AuthService, User } from '../../services/auth-service';

export class MockAuthService implements AuthService {
    async getCurrentUser(): Promise<User> {
        return {
            id: 'mock-user-123',
            email: 'mock@example.com',
            name: 'Mock User',
        };
    }
}
