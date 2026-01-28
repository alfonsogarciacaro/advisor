import { NextResponse } from 'next/server';

const BACKEND_URL = process.env.BACKEND_URL || 'http://localhost:8000';

export async function GET() {
    try {
        const response = await fetch(`${BACKEND_URL}/api/news`);
        if (!response.ok) {
            return NextResponse.json(
                { error: 'Failed to fetch news from backend' },
                { status: response.status }
            );
        }
        const data = await response.json();
        return NextResponse.json(data);
    } catch (error) {
        console.error('Error in news API route:', error);
        return NextResponse.json(
            { error: 'Internal server error' },
            { status: 500 }
        );
    }
}
