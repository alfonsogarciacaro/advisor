export interface NewsItem {
    title: string;
    summary: string;
    url: string;
    source: string;
    time_published: string;
}

export async function getLatestNews(): Promise<NewsItem[]> {
    try {
        const response = await fetch('/api/news');
        if (!response.ok) {
            throw new Error('Failed to fetch news');
        }
        return await response.json();
    } catch (error) {
        console.error('Error fetching news:', error);
        return [];
    }
}
