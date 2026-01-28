import { NextRequest, NextResponse } from 'next/server';
import { fetchAgentRunLogs } from '@/lib/backend-client';

export async function GET(
    request: NextRequest,
    { params }: { params: Promise<{ id: string }> }
) {
    try {
        const { id } = await params;
        const data = await fetchAgentRunLogs(id);
        return NextResponse.json(data);
    } catch (error) {
        console.error('Error in agent logs API route:', error);
        return NextResponse.json(
            { error: error instanceof Error ? error.message : 'Failed to fetch run logs' },
            { status: 500 }
        );
    }
}
