// Theme constants for Playground modes

// Historical Audit - Red theme for fear testing
export const HISTORICAL_AUDIT_THEME = {
  name: 'Historical Audit',
  colors: {
    primary: 'error',      // Red
    secondary: 'error',
    border: 'border-error',
    bg: 'bg-red-50 dark:bg-red-950',
    text: 'text-error',
  },
  icons: {
    header: 'warning-triangle',
    drawdown: 'trending-down',
    recovery: 'clock',
  },
  heading: 'Historical Audit',
  subheading: 'Calibration & Fear Testing',
  description: 'Would you have sold? Discover your true risk tolerance.',
};

// Scenario Lab - Blue/Green theme for planning
export const SCENARIO_LAB_THEME = {
  name: 'Scenario Lab',
  colors: {
    primary: 'info',       // Blue
    secondary: 'success',  // Green
    border: 'border-info',
    bg: 'bg-blue-50 dark:bg-blue-950',
    text: 'text-info',
  },
  icons: {
    header: 'lightning-bolt',
    bull: 'trending-up',
    bear: 'trending-down',
    base: 'minus',
  },
  heading: 'Scenario Lab',
  subheading: 'Planning & Resilience Testing',
  description: 'Test your plan against different future scenarios.',
};
