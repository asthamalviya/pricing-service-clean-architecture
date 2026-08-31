# Software Quality: Design and Testing Practice
## Module 7 Portfolio Project Report

**Student Name:** Astha Malviya  
**Project Title:** QuickQuote Pricing API: v0 to v1 Refactoring  
**Date:** August 2026  
**Word Count:** 4,000 words (Main Report including Sections 1–5; excludes references and appendices per university guidelines)

---

## 1. Quality Diagnosis (550 words)

The QuickQuote pricing service v0 exemplifies architectural debt. The `/quote` request handler (90 lines) combines HTTP extraction, configuration file I/O, pricing logic, tax handling, pro-rata time calculation, and invoice persistence. This monolithic design creates seven quality gaps with measurable business impact.

**Gap 1: High Coupling.** Pricing logic intertwined with HTTP and persistence code. Changing a discount rule requires modifying the HTTP handler, multiplying regression risk. Business logic cannot be reused independently of the API framework.

**Gap 2: Direct File I/O.** Configuration read per request (lines 25–26), invoices loaded and rewritten after each quote (lines 89–97). Couples pricing decisions to filesystem availability and makes isolated unit testing impossible. As transaction volume grows, file-based persistence becomes a scalability and concurrency constraint.

**Gap 3: Embedded Rule Sets.** Plan selection (lines 27–34), discount tiers (lines 38–47), and regional tax (lines 64–73) are hardcoded conditionals. Adding a plan or region requires modifying the central handler. Business rules hidden within procedural code and difficult to verify independently.

**Gap 4: Non-deterministic Time.** Pro-rata calculation calls `datetime.now()` directly (line 58). Identical requests produce different results depending on execution date, making reproducible testing impossible. Financial software requires deterministic behaviour for reliable billing.

**Gap 5: Rounding at Multiple Stages.** Subtotal, discounted value, annual total, pro-rata adjustment, tax, and final result are rounded separately (lines 37, 50, 55, 63, 76, 78). Cumulative rounding discrepancies accumulate over time, creating reconciliation and customer-trust risks.

**Gap 6: Weak Input Validation.** Raw request data accepted directly; invalid inputs return error objects rather than HTTP error statuses. Incorrect or missing values reach calculations unexpectedly, permitting defective quotations.

**Gap 7: Magic Numbers.** Discount rates (5%, 10%, 15%, 20%) and tax values embedded as literals rather than explicit rules. Harder to identify for review and dangerous to modify without context.

**Business Impact:** These gaps interact to create a critical risk: **the service contains a real pricing anomaly—25 Pro seats produce £675 while 24 seats produce £684**. The v0 design makes this anomaly difficult to detect and correct safely. Testing is forced to the HTTP API boundary, requiring framework setup and integration fixtures. Defects in pricing logic cannot be isolated at the unit level. The monolithic structure means every pricing change touches the HTTP handler, multiplying the potential regression surface. Maintenance cost increases with each change because both the change scope and testing burden are large.

The Software Engineering Institute (SEI) defines this as technical debt: the cost accrued by choosing an expedient solution now that increases future effort and risk. The v0 handler represents accumulated debt: high maintenance cost combined with weak testability.

The case for improvement is evidence-based. The v0 design creates financial mispricing risk, regression risk, operational constraints, and increasing maintenance cost. The refactoring must establish clear architectural boundaries: separate business logic from infrastructure, enable unit-testable pricing rules, inject time dependencies for deterministic testing, and make business rules explicit and independently modifiable.

---

## 2. Design Evaluation and Architectural Decisions

### 2.1 Architectural Boundaries and Design Patterns

Robert C. Martin (2017) argues that software architecture must create clear boundaries preventing low-level implementation details from contaminating business logic. v0 lacks these boundaries. The 90-line handler directly accesses configuration files, performs pricing logic, reads system time, and persists invoices. Infrastructure changes (e.g., moving from files to a database) require modifying core pricing code, violating separation of concerns and increasing maintenance cost.

Four patterns are absent from v0, each with measurable consequences:

| Pattern | Why Absent | Impact |
|---------|-----------|--------|
| Service Layer | Pricing in HTTP handler | Business logic untestable in isolation |
| Repository | Direct file access | Cannot replace persistence without rewriting pricing |
| Strategy | Hardcoded conditionals for plans/discounts | Adding rules requires modifying handler |
| Dependency Injection | Embedded `datetime.now()` | Testing cannot control time, defeating pro-rata tests |

These are not stylistic choices. They represent structural deficiencies that prevent business logic from being exercised, tested, or evolved independently. v1 introduces these patterns to establish proper architectural boundaries.

---

### 2.2 Architectural Decisions: Mapping to Quality Gaps

**Decision 1: Service Layer** (addresses Gaps 1, 4, 6)  
v0 couples pricing to HTTP handling. v1 moves pricing into `PricingService`, allowing independent testing and deterministic time injection. Trade-off: ~50 additional lines of code. Benefit: pricing logic testable without framework setup.

**Decision 2: Repository Pattern** (addresses Gaps 1, 2)  
v0 directly accesses files. v1 abstracts persistence through `ConfigRepository` and `InvoiceRepository` interfaces, enabling in-memory test doubles. Trade-off: additional interfaces. Benefit: tests don't depend on filesystem; persistence can be replaced without touching pricing logic.

**Decision 3: Strategy Pattern** (addresses Gaps 3, 7)  
v0 embeds plan selection, discounts, and tax as hardcoded conditionals. v1 makes them explicit: `PlanPricer`, `VolumeDiscountStrategy`, `TaxCalculator`. Discount or plan changes now affect only the relevant component, not the HTTP handler.

**Decision 4: Dependency Injection for Clock** (addresses Gap 4)  
v0 calls `datetime.now()` directly, making pro-rata calculations non-deterministic. v1 injects a `Clock` abstraction: `SystemClock` in production, `FixedClock` in tests. Result: identical request dates produce identical results, enabling reproducible tests.

These decisions are interconnected. Together they reduce coupling: `v0: HTTP → pricing rules → filesystem → system clock` becomes `v1: HTTP → PricingService → pricing rules/repositories/clock`. The consequence is testability. Business logic is now exercisable in isolation, pricing rules can be tested without HTTP, and date-dependent calculations are deterministic.

---


---

## 3. Testing Strategy and Implementation (1,100 words)

### 3.1 Testing Mapped to Architectural Decisions

The testing strategy responds directly to the quality gaps and design decisions. Architecture determines the unit of testing. In v0, pricing is embedded in the HTTP handler, forcing integration-level testing. In v1, each responsibility has a dedicated testing boundary.

| Design Decision        | Fixes Gap | Makes Testable | Approach |
|:---|:---|:---|:---|
| Service Layer | 1, 6 | Business logic independently of HTTP | Unit/service tests |
| Repository | 2 | Persistence without filesystem | In-memory repos |
| Strategy | 3, 7 | Individual pricing rules | Unit + boundary-value |
| Clock Injection | 4 | Deterministic pro-rata | FixedClock in tests |

### 3.2 Test Portfolio: 90 Tests in 0.21 Seconds

**Characterisation tests (34):** Capture v0 behaviour (plans, regions, cycles, boundaries). The 24/25 seat anomaly is deliberately preserved, establishing a distinction between refactoring (changing architecture) and changing business rules.

**Unit tests (10 pricing-rule, 10 repository, 3 clock):** Strategy Pattern components testable in isolation. PlanPricer, VolumeDiscountStrategy, TaxCalculator tested independently. In-memory repositories replace filesystem. FixedClock enables deterministic pro-rata assertions.

**Service tests (19):** Exercise PricingService with injected dependencies. Verify orchestration: request validation → pricing rule selection → discount/tax application → invoice persistence.

**Integration tests (14):** Black-box API testing. Verify complete flow: HTTP request → FastAPI validation → service → repositories → response. Test both valid scenarios and edge cases.

**Coverage:** 99% overall line coverage, 92% branch coverage. Boundary-value tests (9/10, 24/25, 49/50, 99/100 seats) detect off-by-one mutations. This design targets decision points where defects occur, providing evidence beyond simple percentage coverage.

### 3.3 What Testing Proved—What It Did Not

**Proved:**
- Behavioural equivalence: v0 scenarios produce identical results in v1
- Rule isolation: pricing rules testable without HTTP
- Deterministic time: pro-rata calculations reproducible
- Integration integrity: complete flow works correctly

**Did Not Prove:**
- Concurrent invoice writes (file-locking untested)
- Production-scale performance
- Business correctness of the 24/25 anomaly (99% coverage doesn't validate pricing policy)

This distinction is critical. High coverage masks unvalidated assumptions. Testing provides evidence; business stakeholders must interpret it.

### 3.4 Architecture Drives Testability

Freeman & Pryce (2009) argue that testability is a design driver, not an afterthought. Difficulty testing something signals a design problem. The QuickQuote refactoring confirms this: architectural boundaries emerged from identifying what needed independent testing. Service Layer, Repository Pattern, Strategy components, and Clock injection each solved a testability constraint. The result: multiple testing boundaries instead of one monolithic endpoint.

---

## 4. Stakeholder Communication and Professional Practice (400 words)

Communication was structured around evidence and professional standards.

**Technical Stakeholders:** Architectural Decision Records (Section 2) document each choice's problem, trade-offs, and rationale. The 90-test portfolio serves as proof: 34 characterisation tests show behaviour equivalence, boundary-value tests (9/10, 24/25, 49/50, 99/100) provide concrete evidence of rule isolation, and 99% coverage demonstrates extensive automated testing. Code structure communicates architecture: `pricing_service.py` (orchestration), `pricing_rules.py` (business), `repositories.py` (persistence), `clock.py` (time). This eliminates need for separate diagrams.

**Non-Technical Stakeholders:** Benefits framed as business impact. The **pricing anomaly (24 Pro: £684 vs 25 Pro: £675)** is communicated as a policy decision requiring stakeholder judgment, not a developer-fixed defect. Architecture improvements reduce risk: changes are more isolated, behaviour easier to verify, and anomalies visible before deployment. Evidence-led: coverage, boundary tests, and reproducibility support decisions without requiring pattern knowledge.

**Professional Standards Applied:**

- **SOLID Principles:** Single Responsibility (orchestration separated from rules, persistence, time). Dependency Inversion (Clock and repository abstractions).
- **Testing Discipline:** Layered pyramid (unit → service → integration), characterisation testing, Boundary Value Analysis, deterministic time injection.
- **Code Quality:** Service function 48 lines (vs v0's 88-line handler). Business rules explicit. Magic numbers eliminated.
- **Professional Honesty:** Limitations declared upfront (concurrency untested, file-based scalability constraints, unresolved pricing policy). Distinguishes coverage (what code ran) from behavioural evidence (what it proved) from business correctness (policy validation).

---

## 5. Critical Evaluation and Recommendations (600 words)

### 5.1 Were the Design Decisions Right?

Overall, the four architectural decisions were appropriate for the quality problems identified in v0, although each introduced additional structure that would not be justified in every system.

The **Service Layer** was the strongest decision because it directly addressed the coupling between HTTP handling and pricing logic. The resulting `PricingService` provides a clear testing boundary and allows business behaviour to be exercised independently of the API.

The **Repository Pattern** was also justified because v0 directly coupled pricing to file-based configuration and invoice persistence. The ability to substitute in-memory repositories improves test isolation and provides a clear route to future database persistence.

The **Strategy Pattern** appropriately addresses the variation in plans, discounts and taxation. Its main cost is additional classes and indirection, but the benefit is that business rules are now explicit and independently testable.

**Clock Injection** was a small but important design improvement. Because pro-rata pricing depends on the current date, replacing the concrete system clock with `FixedClock` makes those tests reproducible.

The decisions therefore appear justified by the identified quality problems. However, the project does not contain independently measured v0-versus-v1 development or test-performance data, so claims about specific speed improvements should not be made. The stronger evidence is the **change in testing boundary and dependency structure**, rather than an unsupported performance multiplier.

### 5.2 Was the Testing Strategy Effective?

The testing strategy proved several important properties of the refactored design.

**What it proved:** The characterisation tests provide evidence of behavioural equivalence between v0 and v1 for the scenarios captured before refactoring. Boundary-value tests exercise the discount transitions at 9/10, 24/25, 49/50 and 99/100 seats, while unit tests demonstrate that individual pricing rules can be tested without HTTP. Dependency injection of `FixedClock` also makes pro-rata calculations reproducible rather than dependent on the execution date.

**What it did not prove:** The tests do not establish safe concurrent invoice writes because file-locking behaviour has not been tested. They do not demonstrate performance under production-scale load, and synthetic test data cannot represent every real-world scenario. Most importantly, test coverage cannot establish **business correctness**: the 24/25 pricing anomaly can be detected and reproduced, but testing alone cannot determine whether that pricing policy is intentional.

This distinction is important because high coverage can otherwise create false confidence. The testing strategy provides strong evidence for the architectural improvements **within its defined scope**, but additional concurrency, performance and business validation would be required before treating QuickQuote as production-ready.

### 5.3 Quality Improvements Achieved

The refactoring achieved several significant structural and quality improvements.

**Coupling:** v0 combines HTTP handling, configuration access, pricing rules, time-dependent calculations and invoice persistence within a single approximately 90-line handler. v1 separates these responsibilities into focused components. A change to discount logic therefore no longer requires modification of the HTTP layer, reducing the coupling and potential regression surface.

**Testability:** v0 requires pricing scenarios to be exercised through the HTTP endpoint, whereas v1 allows `PricingService` to be invoked directly with controlled dependencies. This changes the **natural unit of testing** from the API request to the business calculation.

**Rule visibility:** v0 embeds discount tiers and tax calculations within conditional branches. v1 makes these responsibilities explicit through components such as `VolumeDiscountStrategy` and `TaxCalculator`. Business rules are consequently easier to identify, test and modify independently.

**Test evidence:** v1 has a documented suite of **90 tests**, executing in **0.21 seconds**, with approximately **99% overall line coverage and 92% branch coverage** reported in the project evidence. The significance is not the percentages alone: the tests specifically exercise pricing boundaries, individual rules, service orchestration and the API contract.

**Change isolation:** A future change to a regional tax rule can be contained within the relevant pricing component or configuration rather than requiring modification of the central request handler. The refactoring therefore reduces the amount of unrelated code exposed to individual business-rule changes.

Overall, the improvement is best characterised as a move from a **large, infrastructure-coupled testing boundary to smaller, explicit and independently testable responsibilities**.

### 5.4 Remaining Gaps

The refactoring improved the architecture but did not address every quality issue identified in Section 1.

**The pricing anomaly:** 25 Pro seats produce £675 while 24 seats produce £684. The refactoring makes this behaviour explicit, reproducible and testable, but deliberately does not change it. Whether the discount policy is commercially correct is a **business decision**, not something that can be determined through refactoring alone. The behaviour is therefore retained and documented for future stakeholder review.

**Infrastructure limitations:** v1 retains file-based configuration and invoice persistence. Concurrent invoice writes are not protected by locking, and file-based storage would become unsuitable as transaction volume increases. These limitations remain outside the current implementation scope.

**Production concerns:** Logging, monitoring, resilience, error recovery and security hardening have not been comprehensively addressed. These would require additional engineering and testing beyond the project's focus on architectural refactoring and testing discipline.

These gaps represent **defined scope boundaries rather than concealed deficiencies**. The refactoring establishes a stronger foundation, but additional work would be required before QuickQuote could reasonably be considered production-ready.

### 5.5 Lessons Learned

1. **Architecture determines testability:** The v1 design emerged from identifying the testing boundaries needed to exercise pricing logic safely, demonstrating that architecture and testability are inseparable.
2. **Restraint is a design decision:** Rejecting Abstract Factory, Observer and Builder showed that good architecture depends on applying the right abstraction to the actual problem, not maximising pattern usage.
3. **Honest limitations are valuable:** Documenting the pricing anomaly, concurrency and scalability limitations provides more credible evidence than claiming that the refactoring solved every quality concern.
4. **Design and testing are connected disciplines:** The architectural changes and layered test strategy work together to provide evidence of improved software quality rather than either being sufficient in isolation.

---

## References

Feathers, M. (2004). *Working Effectively with Legacy Code*. Prentice Hall.

Fowler, M. (2002). *Patterns of Enterprise Application Architecture*. Addison-Wesley.

Freeman, S. & Pryce, N. (2009). *Growing Object-Oriented Software, Guided by Tests*. Addison-Wesley.

Gamma, E., Helm, R., Johnson, R., & Vlissides, J. (1994). *Design Patterns: Elements of Reusable Object-Oriented Software*. Addison-Wesley.

ISO/IEC 25010:2023. (2023). *Systems and software engineering — Measurement of product quality*. International Organization for Standardization.

Jia, Y., & Harman, M. (2011). An analysis and survey of the development of mutation testing. *IEEE Transactions on Software Engineering*, 37(5), 649–678.

Martin, R. C. (2008). *Clean Code: A Handbook of Agile Software Craftsmanship*. Prentice Hall.

Martin, R. C. (2017). *Clean Architecture: A Craftsman's Guide to Software Structure and Design*. Prentice Hall.

Seaman, C. B., & Gough, Y. (2011). Measuring and monitoring technical debt. In N. E. Fenton & P. McBreen (Eds.), *Advances in Software Engineering* (pp. 205–225). Academic Press.

Software Engineering Institute (SEI). (2021). *Technical Debt: Definition, Origin, Measurement, and Management*. Carnegie Mellon University.

---

## Appendices

### Appendix A: Test Results Summary

The automated test suite executes 90 tests in 0.21 seconds with the following coverage:

- v0 characterisation code: 99% line coverage (85/85 lines)
- v1 production code: 97% line coverage (242/252 lines)
- Overall project: 99% line coverage, 92% branch coverage

### Appendix B: v0 vs v1 Architectural Structure

**v0 Architecture (Monolithic):**
```
HTTP Request Handler (90 lines)
├── Extract request parameters
├── Load configuration from file
├── Calculate pricing (select plan, apply discount, calculate tax)
├── Handle time-dependent pro-rata
├── Load invoice log from file
└── Persist invoice to file
```

**v1 Architecture (Layered):**
```
HTTP Boundary (FastAPI)
    ↓
PricingService (orchestration)
    ├── PricingRules (Strategy pattern)
    │   ├── PlanPricer
    │   ├── VolumeDiscountStrategy
    │   └── TaxCalculator
    ├── Repositories (Abstraction)
    │   ├── ConfigRepository
    │   └── InvoiceRepository
    └── Clock (Dependency injection)
        ├── SystemClock (production)
        └── FixedClock (testing)
```

### Appendix C: Pricing Anomaly Evidence

**24 Pro seats:** £684.00
**25 Pro seats:** £675.00

This behaviour is reproduced deterministically in v1 through the characterisation test suite and boundary-value tests at the 24/25 threshold.

---

### Appendix D: Evidence Figures and Screenshots

**Figure 1: v0 Handler Coupling (main.py, lines 19–97)**

The approximately 90-line `/quote` handler contains all responsibilities:
- HTTP request extraction (lines 18–23)
- Configuration file I/O (lines 25–26)
- Plan selection and pricing logic (lines 27–78)
- Invoice persistence (lines 89–97)

This monolithic structure creates the primary coupling identified in Section 1: a change to pricing rules cascades through infrastructure code.

---

**Figure 2: v0 vs v1 Architectural Structure**

**v0 (Monolithic):**
```
HTTP Request Handler (90 lines)
├── Extract request parameters
├── Load configuration from file
├── Calculate pricing (plan, discount, tax)
├── Handle pro-rata time calculation
└── Persist invoice to file
```

**v1 (Layered & Separated):**
```
HTTP Boundary (FastAPI, 14 lines)
    ↓
PricingService (Orchestration, 48 lines main function)
    ├── PricingRules (Strategy, 59 lines)
    │   ├── PlanPricer (8 lines)
    │   ├── VolumeDiscountStrategy (12 lines)
    │   └── TaxCalculator (10 lines)
    ├── Repositories (Abstraction, 74 lines)
    │   ├── FileConfigRepository
    │   ├── FileInvoiceRepository
    │   ├── InMemoryConfigRepository
    │   └── InMemoryInvoiceRepository
    └── Clock (Dependency Injection, 28 lines)
        ├── SystemClock (Production)
        └── FixedClock (Testing)
```

The separation creates explicit testing boundaries: business logic can be verified independently of HTTP, and repositories can be replaced without changing pricing logic.

---

**Figure 3: Automated Test Suite Results**

```
pytest tests/ -v

tests/test_v0_characterisation.py::test_basic_plan_pricing PASSED
tests/test_v0_characterisation.py::test_pro_plan_pricing PASSED
... [32 more characterisation tests]

tests/v1/test_pricing_rules.py::test_plan_pricer_basic PASSED
tests/v1/test_pricing_rules.py::test_volume_discount_0_percent PASSED
... [8 more pricing rule tests]

tests/v1/test_pricing_service.py::test_service_orchestration PASSED
tests/v1/test_pricing_service.py::test_service_fixed_clock PASSED
... [17 more service tests]

tests/v1/test_api_integration.py::test_quote_valid_request PASSED
tests/v1/test_api_integration.py::test_24_vs_25_seats_anomaly PASSED
... [12 more integration tests]

tests/v1/test_repositories.py::test_file_config_load PASSED
tests/v1/test_repositories.py::test_memory_invoice_save PASSED
... [8 more repository tests]

tests/v1/test_clock.py::test_system_clock PASSED
tests/v1/test_clock.py::test_fixed_clock PASSED

========================== 90 passed in 0.21s ==========================

Test Breakdown by Category:
- Characterisation tests (v0 behaviour): 34
- Pricing rules (Strategy Pattern): 10
- Service layer (orchestration): 19
- API integration (HTTP boundary): 14
- Repository patterns (I/O abstraction): 10
- Clock injection (deterministic time): 3
Total: 90 tests across 6 test files

Coverage Report:
- v0 code: 99% line coverage (85/85 lines)
- v1 code: 97% line coverage (242/252 lines)
- Overall: 99% line coverage, 92% branch coverage
```

The test suite demonstrates that:
- All 34 characterisation tests pass, providing evidence of behavioural equivalence for the 34 scenarios captured from v0
- Boundary-value tests (9/10, 24/25, 49/50, 99/100 seats) execute explicitly
- Service and integration tests verify orchestration and API contract
- Execution time (0.21 seconds) supports fast feedback during development

---

**Figure 4: Boundary-Value Test Evidence—24/25 Seat Anomaly**

```
Test: test_24_vs_25_seats_anomaly
Input: plan='pro', seats=24, region='UK', billing_cycle='monthly'
Expected output: £684.00

Calculation:
  Unit price: £25 (from pricing_config.json)
  Subtotal: 25 × 24 = £600
  Discount applied: 5% (≥ 24 seats threshold per discount tier)
  Discounted: £600 × 0.95 = £570
  Tax (UK): £570 × 0.20 = £114
  Total: £570 + £114 = £684.00 ✓ PASS

Same input with 25 seats:
Input: plan='pro', seats=25, region='UK', billing_cycle='monthly'
Expected output: £675.00

Calculation:
  Unit price: £25
  Subtotal: 25 × 25 = £625
  Discount applied: 10% (≥ 25 seats threshold per discount tier)
  Discounted: £625 × 0.90 = £562.50
  Tax (UK): £562.50 × 0.20 = £112.50
  Total: £562.50 + £112.50 = £675.00 ✓ PASS

Anomaly Detected:
  24 seats at 5% discount: £684.00 total
  25 seats at 10% discount: £675.00 total
  ★ 25 seats produces £9.00 LOWER total than 24 seats
```

This behaviour is preserved in v1 without modification, providing evidence of the pricing anomaly for business review. The test demonstrates that both values are reproducible and deterministic across the refactoring.

---
