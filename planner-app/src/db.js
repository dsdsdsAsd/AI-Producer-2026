import Dexie from 'dexie';

export const db = new Dexie('PlannerDB');

db.version(1).stores({
    ideas: '++id, title, status, createdAt, coverType' // Primary key and indexed props
});

// Helper to get initial data or seed if empty
db.on('populate', () => {
    // Optional: Seed with example data if needed
});
