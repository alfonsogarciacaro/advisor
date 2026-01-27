export interface PubSubService {
    publish(topic: string, data: Record<string, any>): Promise<string>;
}
