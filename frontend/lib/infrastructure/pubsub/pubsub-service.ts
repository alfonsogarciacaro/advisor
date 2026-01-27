import { PubSub } from '@google-cloud/pubsub';
import { PubSubService } from '../../services/pubsub-service';

export class GCPPubSubService implements PubSubService {
    private pubsub: PubSub;

    constructor() {
        this.pubsub = new PubSub({
            projectId: process.env.GCP_PROJECT_ID || 'local-project',
            // The client library automatically detects PUBSUB_EMULATOR_HOST
        });
    }

    async publish(topic: string, data: Record<string, any>): Promise<string> {
        const dataBuffer = Buffer.from(JSON.stringify(data));
        try {
            const messageId = await this.pubsub.topic(topic).publish(dataBuffer);
            return messageId;
        } catch (error) {
            if (process.env.PUBSUB_EMULATOR_HOST) {
                // Auto-create topic in emulator
                try {
                    // @ts-ignore
                    await this.pubsub.createTopic(topic);
                    // @ts-ignore
                    const messageId = await this.pubsub.topic(topic).publish(dataBuffer);
                    return messageId;
                } catch (innerError) {
                    console.error("Failed to create topic", innerError);
                    throw innerError;
                }
            }
            throw error;
        }
    }
}
