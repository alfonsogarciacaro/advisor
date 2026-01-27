export interface StorageService {
    save(collection: string, id: string, data: Record<string, any>): Promise<string>;
    get(collection: string, id: string): Promise<Record<string, any> | null>;
    update(collection: string, id: string, data: Record<string, any>): Promise<void>;
    delete(collection: string, id: string): Promise<void>;
}
