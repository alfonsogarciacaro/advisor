import { NextResponse } from 'next/server';
import { fetchNewsFromBackend } from '@/lib/backend-client';

export async function GET() {
    try {
        const data = await fetchNewsFromBackend();
        return NextResponse.json(data);
    } catch (error) {
        console.error('Error in news API route:', error);
        return NextResponse.json(
            { error: 'Failed to fetch news from backend' },
            { status: 500 }
        );
    }
}
