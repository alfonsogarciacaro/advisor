import { NextRequest, NextResponse } from 'next/server';
import { createAgentRun } from '@/lib/backend-client';

export async function POST(
    request: NextRequest,
    { params }: { params: Promise<{ name: string }> }
) {
    try {
        const { name } = await params;
        const body = await request.json();

        const data = await createAgentRun(name, body.input);
        return NextResponse.json(data);
    } catch (error) {
        console.error('Error in agent run API route:', error);
        return NextResponse.json(
            { error: error instanceof Error ? error.message : 'Failed to start agent' },
            { status: 500 }
        );
    }
}
