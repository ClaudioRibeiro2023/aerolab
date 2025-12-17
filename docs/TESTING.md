# AeroLab - Test Coverage Documentation

> **Last Updated:** 2024-12-17  
> **Status:** Active Development

---

## Overview

AeroLab uses a multi-layer testing strategy covering unit tests, integration tests, and end-to-end tests.

---

## Test Suites

### Backend (apps/api)

| Test File | Tests | Description |
|-----------|-------|-------------|
| `test_health.py` | 10 | Health, docs, OpenAPI endpoints |
| `test_api.py` | ~20 | Core API endpoints |
| `test_flow_studio.py` | ~15 | Flow Studio workflows |
| `test_modules.py` | ~30 | Domain modules |
| `test_v2_modules.py` | ~50 | V2 enhanced modules |
| `test_enterprise.py` | ~40 | Enterprise features |
| `test_billing_marketplace.py` | ~60 | Billing & marketplace |
| `test_integrations.py` | ~25 | External integrations |
| `test_validation.py` | ~30 | Input validation |
| `test_new_components.py` | ~20 | New components |
| `test_stress.py` | ~30 | Load/stress tests |
| `e2e/test_smoke.py` | ~15 | E2E smoke tests |

**Total: ~380 tests**

#### Running Backend Tests

```bash
cd apps/api
.venv\Scripts\activate  # Windows
source .venv/bin/activate  # Linux/Mac

# Run all tests
pytest tests/ -v

# Run specific file
pytest tests/test_health.py -v

# Run with coverage
pytest tests/ --cov=src --cov-report=html
```

---

### Frontend Shared (packages/shared)

| Test File | Tests | Description |
|-----------|-------|-------------|
| `auth/__tests__/auth.test.ts` | 16 | Auth utilities |
| `api/__tests__/client.test.ts` | 12 | API client |
| `utils/__tests__/formatters.test.ts` | 17 | Formatters |
| `utils/__tests__/helpers.test.ts` | 30 | Helper functions |

**Total: 75 tests**

#### Running Frontend Tests

```bash
# From root
pnpm --filter @template/shared run test

# With coverage
pnpm --filter @template/shared run test:coverage
```

---

### E2E Tests (apps/studio)

| Test File | Tests | Description |
|-----------|-------|-------------|
| `e2e/smoke.spec.ts` | 12 | Smoke tests |

**Categories:**
- Studio Smoke Tests (3 tests)
- API Integration (1 test)
- Navigation (2 tests)
- UI Components (2 tests)
- Responsive Design (3 tests)

#### Running E2E Tests

```bash
cd apps/studio

# Install Playwright browsers first
npx playwright install

# Run tests
pnpm test:e2e

# Run with UI
pnpm test:e2e:ui
```

---

## Coverage Goals

| Layer | Current | Target |
|-------|---------|--------|
| Backend Unit | ~60% | 80% |
| Frontend Unit | ~50% | 70% |
| E2E Critical Paths | ~30% | 60% |

---

## CI Integration

Tests run automatically via GitHub Actions:

- **lint job**: ESLint, TypeScript
- **test job**: Unit tests (pnpm test)
- **python-api job**: Backend tests (pytest)
- **security-audit job**: npm audit, pip-audit

---

## Adding New Tests

### Backend (Python)

```python
# tests/test_example.py
import pytest

class TestExample:
    def test_something(self, client):
        response = client.get("/endpoint")
        assert response.status_code == 200
```

### Frontend (TypeScript)

```typescript
// __tests__/example.test.ts
import { describe, it, expect } from 'vitest';

describe('Example', () => {
  it('should work', () => {
    expect(true).toBe(true);
  });
});
```

### E2E (Playwright)

```typescript
// e2e/example.spec.ts
import { test, expect } from '@playwright/test';

test('example', async ({ page }) => {
  await page.goto('/');
  await expect(page).toHaveTitle(/./);
});
```

---

## Test Commands Summary

| Command | Description |
|---------|-------------|
| `pnpm test` | Run all tests |
| `pnpm test:e2e` | Run E2E tests (apps/web) |
| `pnpm --filter @template/shared run test` | Shared package tests |
| `cd apps/api && pytest` | Backend tests |
| `cd apps/studio && pnpm test:e2e` | Studio E2E tests |
