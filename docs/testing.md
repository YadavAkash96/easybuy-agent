# Testing

## Commands

All commands run via Docker (see `Makefile`):

```bash
make test              # Run all tests
make test-unit         # Run unit tests only
make test-integration  # Run integration tests only
make lint              # Run ruff linter
make format            # Auto-format with ruff
```

## Test structure

| File | Level | What it tests |
|------|-------|---------------|
| `tests/test_types.py` | Unit | Pydantic validation for spec/product/cart/checkout types |
| `tests/test_ranking.py` | Unit | Deterministic ranking and explanation logic |
| `tests/test_cart.py` | Unit | Cart aggregation and totals |
| `tests/test_retailers.py` | Unit | Mock retailer adapters, filtering invalid items |
| `tests/test_api.py` | Integration | FastAPI endpoints for brief/discover/rank/cart/checkout |

## Approach

- **TDD**: tests written before implementation
- **Mocked retailer catalogs**: no external dependencies
- **httpx + ASGITransport**: tests the full FastAPI app in-process
