import { Firestore } from '@google-cloud/firestore';
import { StorageService } from '../../services/storage-service';

export class FirestoreStorage implements StorageService {
    private db: Firestore;

    constructor() {
        this.db = new Firestore({
            projectId: process.env.GCP_PROJECT_ID || 'local-project',
            // The client library automatically detects FIRESTORE_EMULATOR_HOST
        });
    }

    async save(collection: string, id: string, data: Record<string, any>): Promise<string> {
        await this.db.collection(collection).doc(id).set(data);
        return id;
    }

    async get(collection: string, id: string): Promise<Record<string, any> | null> {
        const doc = await this.db.collection(collection).doc(id).get();
        if (doc.exists) {
            return doc.data() || null;
        }
        return null;
    }

    async update(collection: string, id: string, data: Record<string, any>): Promise<void> {
        await this.db.collection(collection).doc(id).update(data);
    }

    async delete(collection: string, id: string): Promise<void> {
        await this.db.collection(collection).doc(id).delete();
    }
}
