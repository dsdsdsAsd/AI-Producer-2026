import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import PlannerBoard from './PlannerBoard';

// Mock Dexie hooks, as we don't want a real DB in unit tests
vi.mock('dexie-react-hooks', () => ({
    useLiveQuery: () => [], // Return empty array initially
}));

// Mock the db instance
vi.mock('../db', () => ({
    db: {
        ideas: {
            add: vi.fn(),
            delete: vi.fn(),
            update: vi.fn(),
        }
    }
}));

describe('PlannerBoard Component', () => {
    it('renders the board title', () => {
        render(<PlannerBoard />);
        expect(screen.getByText(/Shorts Planner/i)).toBeInTheDocument();
    });

    it('opens the modal when "New" button is clicked', () => {
        render(<PlannerBoard />);

        // Find the button that says "Новый"
        const newButton = screen.getByText('Новый');
        fireEvent.click(newButton);

        // Check if modal title appears
        expect(screen.getByText(/Новый Shorts/i)).toBeInTheDocument();
    });
});
