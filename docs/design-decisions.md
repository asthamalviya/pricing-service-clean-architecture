# QuickQuote Design Decisions

## Document Purpose

This document records the architectural decisions, trade-offs, and technical reasoning behind the QuickQuote v0 to v1 redesign. It serves as supporting material for portfolio presentation and technical interviews.

---

## Phase 1: Characterisation Testing

### Decision: Lock v0 behaviour before refactoring

**What:** Before making any structural changes, we built a comprehensive test suite that captures v0's current output for a wide range of inputs, including edge cases and known bugs.

**Why:** Characterisation tests prove that refactoring changes *structure* without changing *behaviour*. They provide objective evidence that business logic survived the redesign intact. This is critical when refactoring a system without formal specifications—the existing implementation *is* the specification, bugs and all.

**Trade-offs:**
- **Pro:** Confidence that refactoring preserves business logic. Clear before/after comparison for stakeholders.
- **Pro:** Documents current behaviour, including anomalies, for business review.
- **Con:** Effort invested in testing code that will be restructured. However, this effort is necessary—without it, we have no proof the redesign is correct.

**Coverage targets:**
- All volume discount boundaries: 9, 10, 24, 25, 49, 50, 99, 100 seats
- All plans: basic, pro, enterprise
- All billing cycles: monthly, annual
- All regions: UK, IE, DE, US
- Error cases: unknown plan, unknown region
- Pro-rata scenarios: first day, mid-month, last day

---

## Known Business Logic Anomaly: 25 Pro Seats

### The anomaly

In v0, purchasing **25 pro seats costs less** than purchasing **24 pro seats**:
- 24 seats: £600 subtotal → 5% discount = £570 → 20% UK tax = **£684 total**
- 25 seats: £625 subtotal → 10% discount = £562.50 → 20% UK tax = **£675 total**

### Why this occurs

The volume discount threshold jumps from 5% (10-24 seats) to 10% (25-49 seats) at exactly 25 seats. When a customer adds one seat, they cross this threshold and their total price *decreases* by £9.

### Why we're not fixing it in this refactor

**Refactoring changes structure, not requirements.** This anomaly is a business logic issue that requires stakeholder input:
- Should the discount thresholds be adjusted?
- Should pricing tiers be revised?
- Is this intentional behaviour (a promotional "sweet spot")?

Silently "fixing" this during a technical refactor would be:
1. Changing requirements without authorisation
2. Potentially breaking existing customer expectations
3. Mixing business decisions with technical work

**Documentation strategy:** The anomaly is captured in a dedicated test (`test_anomaly_25_pro_seats_cheaper_than_24`) with clear comments explaining the cause and recommended action. This demonstrates professional discipline—recognising the difference between technical and business correctness.

---

## Phase 1 Deliverables

- ✅ 40+ characterisation tests covering all boundaries and error cases
- ✅ Dedicated test documenting the 25-seat pricing anomaly
- ✅ Test infrastructure: `pytest`, `pytest-cov`, `httpx`
- ✅ Baseline coverage report for v0

---

*Document to be updated as design progresses through Phases 2-4.*
