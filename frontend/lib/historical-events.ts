/**
 * Historical events data for backtesting context
 */

export interface HistoricalEvent {
    date: string;
    name: string;
    icon: string;
    description: string;
}

export const HISTORICAL_EVENTS: HistoricalEvent[] = [
    {
        date: '2008-09-15',
        name: 'Lehman Collapse',
        icon: '🏦',
        description: 'Lehman Brothers bankruptcy triggers global financial crisis'
    },
    {
        date: '2020-03-11',
        name: 'COVID Declared',
        icon: '🦠',
        description: 'WHO declares COVID-19 pandemic'
    },
    {
        date: '2020-03-23',
        name: 'Market Bottom',
        icon: '📉',
        description: 'S&P 500 hits bottom, down 34% from peak'
    },
    {
        date: '2022-02-24',
        name: 'Ukraine War',
        icon: '💥',
        description: 'Russia invades Ukraine, market volatility spikes'
    },
    {
        date: '2022-03-16',
        name: 'Fed Rate Hikes',
        icon: '📈',
        description: 'Federal Reserve begins aggressive rate hike cycle'
    },
];

export function getHistoricalEvents(startDate: string, endDate: string): HistoricalEvent[] {
    const start = new Date(startDate);
    const end = new Date(endDate);

    return HISTORICAL_EVENTS.filter(event => {
        const eventDate = new Date(event.date);
        return eventDate >= start && eventDate <= end;
    });
}

export const PRESET_PERIODS = [
    {
        label: 'Pre-COVID (Jan 2020)',
        date: '2020-01-01',
        icon: '🦠',
        description: 'Test how strategy would perform through COVID crash'
    },
    {
        label: 'Pre-2008 Crisis (Jan 2008)',
        date: '2008-01-01',
        icon: '📉',
        description: 'Test through global financial crisis'
    },
    {
        label: 'Post-COVID Recovery (Jan 2022)',
        date: '2022-01-01',
        icon: '💉',
        description: 'Test through inflation and rate hike period'
    },
    {
        label: '5 Years Ago',
        date: new Date(Date.now() - 5 * 365 * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
        icon: '📅',
        description: '5-year historical performance'
    },
    {
        label: '10 Years Ago',
        date: new Date(Date.now() - 10 * 365 * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
        icon: '📅',
        description: '10-year historical performance'
    },
];

export const ACCOUNT_TYPES = [
    { value: 'taxable', label: 'Taxable', taxRate: 20, icon: '💵' },
    { value: 'nisa_growth', label: 'NISA Growth', taxRate: 0, icon: '🆓' },
    { value: 'nisa_general', label: 'NISA General', taxRate: 0, icon: '🆓' },
    { value: 'ideco', label: 'iDeCo', taxRate: 0, icon: '🏛️' },
];
