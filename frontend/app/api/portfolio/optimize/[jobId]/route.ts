import { NextResponse } from 'next/server';
import { fetchOptimizationStatus } from '@/lib/backend-client';

export async function GET(
    request: Request,
    { params }: { params: Promise<{ jobId: string }> }
) {
    try {
        const jobId = (await params).jobId;
        const result = await fetchOptimizationStatus(jobId);
        return NextResponse.json(result);
    } catch (error: any) {
        console.error('Optimization status error:', error);
        return NextResponse.json(
            { error: error.message || 'Failed to fetch optimization status' },
            { status: 500 }
        );
    }
}
