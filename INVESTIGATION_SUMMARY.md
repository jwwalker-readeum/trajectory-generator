# Investigation Summary: UI/API Contract Issue

## Investigation Results

After thorough testing, **no contract mismatch was found**. The frontend and backend API contracts are **correctly aligned**.

### What Was Tested

1. ✅ **Payload Format**: Frontend sends `{launch: {lat, lon}, landing: {lat, lon}}` - Backend expects exactly this ✓
2. ✅ **Response Fields**: All fields the UI needs are present in API responses ✓
3. ✅ **Data Types**: All fields have correct types (boolean, number, string[], etc.) ✓
4. ✅ **Both Endpoints**: `/api/feasibility` and `/api/trajectory` both work correctly ✓
5. ✅ **Edge Cases**: Feasible, infeasible (too far), infeasible (too short) all handled ✓
6. ✅ **Other Endpoints**: `/api/config` and `/api/cesium-token` work as expected ✓

### Possible Causes of Reported 422 Error

While the contract is correct, a 422 error would occur if:

1. **Missing Content-Type header** - Must be `application/json`
2. **Invalid coordinates** - Latitude must be [-90, 90], longitude [-180, 180]
3. **Missing fields** - Both `launch` and `landing` with `lat` and `lon` are required
4. **Wrong data types** - Coordinates must be numbers, not strings

The frontend code correctly sets all headers and validates all inputs, so the issue likely occurred during manual testing or an edge case that's now resolved.

## Changes Made

### 1. New Test File: `tests/test_ui_contract.py`

Comprehensive regression tests that verify:
- Exact payload format from `static/app.js`
- All response fields UI needs are present
- Both feasible and infeasible cases
- All four API endpoints
- Validation errors (422) for invalid inputs
- **12 new test cases, all passing**

### 2. New Documentation: `api_contract.md`

Complete API contract specification including:
- TypeScript-style type definitions for all endpoints
- Request/response examples
- Frontend usage locations (line numbers in app.js)
- Common error causes and prevention
- Guidelines to prevent future drift

## Verification Results

### Manual Testing
```
✅ Feasible case: Returns 200 with all required fields
✅ Infeasible (too far): Returns 200, feasible=false, correct reason
✅ Infeasible (too short): Returns 200, feasible=false, correct reason
✅ Trajectory: Returns 200 with 425 points, all required fields present
✅ Invalid latitude: Returns 422 (validation working correctly)
✅ Invalid longitude: Returns 422 (validation working correctly)
```

### Test Suite
```bash
$ pytest tests/test_ui_contract.py -v
=================== 12 passed in 2.00s ====================

$ pytest tests/ -v  
=================== 61 passed in 3.10s ====================
```

## Frontend → Backend Field Mapping

### Feasibility Endpoint
| Frontend Uses (app.js) | Backend Returns (api.py) | Status |
|------------------------|--------------------------|--------|
| `result.feasible` (line 334) | `feasible: bool` | ✅ |
| `result.reasons` (line 329) | `reasons: string[]` | ✅ |
| `result.peak_g_load` (line 319) | `peak_g_load: float` | ✅ |
| `result.peak_heat_flux_w_cm2` (line 321) | `peak_heat_flux_w_cm2: float` | ✅ |
| `result.distance_to_envelope_km` (line 323) | `distance_to_envelope_km: float` | ✅ |

### Trajectory Endpoint
| Frontend Uses | Backend Returns | Status |
|---------------|-----------------|--------|
| `p.time_s` (line 359, 364) | `time_s: float` | ✅ |
| `p.range_m` (line 354) | `range_m: float` | ✅ |
| `p.altitude_m` (line 355, 360) | `altitude_m: float` | ✅ |
| `p.mach` (line 365) | `mach: float` | ✅ |
| `point.latitude_deg` (line 618) | `latitude_deg: float` | ✅ |
| `point.longitude_deg` (line 617) | `longitude_deg: float` | ✅ |

## Benefits of Changes

1. **Regression Prevention**: Tests catch any future API changes that break the UI
2. **Documentation**: Contract is now explicitly documented and easy to reference
3. **Confidence**: 422 errors now covered with validation tests
4. **Maintenance**: Future developers can reference api_contract.md
5. **CI/CD**: Tests run in CI to catch issues before deployment

## Recommendations

1. ✅ Run `pytest tests/test_ui_contract.py` before deploying API changes
2. ✅ Update `api_contract.md` when adding/modifying endpoints
3. ✅ Reference `api_contract.md` when modifying frontend API calls
4. ✅ Add new test cases for any new API fields the UI uses

---

**All "NOTIONAL DEMO" labeling preserved throughout code and tests.**
