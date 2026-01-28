import { LoggerService } from './services/logger-service';
import { AuthService } from './services/auth-service';
import { StorageService } from './services/storage-service';

import { ConsoleLogger } from './infrastructure/logging/console-logger';
import { MockAuthService } from './infrastructure/auth/mock-auth';
import { FirestoreStorage } from './infrastructure/storage/firestore-storage';

class DIContainer {
    private static instance: DIContainer;

    public logger: LoggerService;
    public auth: AuthService;
    public storage: StorageService;

    private constructor() {
        this.logger = new ConsoleLogger();
        this.auth = new MockAuthService();
        this.storage = new FirestoreStorage();
    }

    public static getInstance(): DIContainer {
        if (!DIContainer.instance) {
            DIContainer.instance = new DIContainer();
        }
        return DIContainer.instance;
    }
}

export const container = DIContainer.getInstance();
