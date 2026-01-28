import { NextRequest, NextResponse } from 'next/server';
import { fetchAgentRunStatus } from '@/lib/backend-client';

export async function GET(
    request: NextRequest,
    { params }: { params: Promise<{ id: string }> }
) {
    try {
        const { id } = await params;
        const data = await fetchAgentRunStatus(id);
        return NextResponse.json(data);
    } catch (error) {
        console.error('Error in agent status API route:', error);
        return NextResponse.json(
            { error: error instanceof Error ? error.message : 'Failed to fetch run status' },
            { status: 500 }
        );
    }
}
