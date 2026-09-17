// Vitest pour la logique pure, en Node, sans DOM simulé (research.md R-14).
import { defineConfig } from 'vitest/config'

export default defineConfig({
  test: {
    environment: 'node',
    include: ['tests/unit/**/*.test.ts', 'tests/portes/**/*.test.ts'],
  },
})
