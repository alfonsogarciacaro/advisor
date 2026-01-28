import { NextResponse } from 'next/server';
import { startOptimization } from '@/lib/backend-client';

export async function POST(request: Request) {
    try {
        const body = await request.json();
        const { amount, currency } = body;

        if (!amount || !currency) {
            return NextResponse.json(
                { error: 'Amount and currency are required' },
                { status: 400 }
            );
        }

        const result = await startOptimization(amount, currency);
        return NextResponse.json(result);
    } catch (error: any) {
        console.error('Available optimization error:', error);
        return NextResponse.json(
            { error: error.message || 'Failed to start optimization' },
            { status: 500 }
        );
    }
}
