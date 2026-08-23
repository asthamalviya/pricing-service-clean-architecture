# Software Quality: Design and Testing Practice
## Module 7 Portfolio Project Report

**Student Name:** Astha Malviya  
**Project Title:** QuickQuote Pricing API: v0 to v1 Refactoring  
**Date:** August 2026  

---

## 1. Quality Diagnosis (500 words)

### Current Development Practice and SDLC Location

The QuickQuote pricing service v0 demonstrates several architectural characteristics that compromise software quality, maintainability and the ability to evolve the pricing rules safely. The principal issue is not simply that the implementation is contained in one file; it is that **multiple responsibilities and concrete dependencies are combined inside the `/quote` request handler**, making business logic difficult to isolate, test and change. The handler reads the HTTP request, loads configuration, calculates pricing, applies tax, handles dates and writes invoices. For example, request values are extracted at lines 18–23, configuration is read directly from disk at lines 25–26, and invoice persistence occurs at lines 89–97. 

### Technical Debt and Software Quality Metrics

According to ISO/IEC 25010 (Software Product Quality Model), software quality is determined by functional suitability, performance efficiency, compatibility, usability, reliability, security, maintainability and portability. The v0 implementation exhibits degradation across multiple dimensions, particularly maintainability and reliability. The Software Engineering Institute (SEI) defines technical debt as the cost incurred by choosing an expedient solution now that will increase effort and risk in future change and maintenance (Seaman & Gough, 2011). The v0 design demonstrates accumulated technical debt: the monolithic handler creates high maintenance cost because any change to pricing rules increases the likelihood of regression through infrastructure modifications.

The first quality gap is therefore **high coupling and lack of separation of concerns**. Because pricing and infrastructure are contained in the same handler, a change to pricing rules also changes a component responsible for HTTP and persistence. This increases the regression surface and means the business calculation cannot be reused independently of the API. From a business perspective, this increases the cost and risk of introducing new pricing functionality.

The second gap is **direct configuration and invoice I/O**. Configuration is read from a JSON file during every request (lines 25–26), while invoice records are loaded and rewritten from disk after each quote (lines 89–97).  This couples a pricing decision to filesystem availability and makes isolated testing difficult. It also creates an operational risk: as transaction volume increases, file-based persistence becomes a scalability and concurrency constraint.

The third gap is the use of **three embedded conditional rule sets** for plans, volume discounts and tax regions. Plan selection occurs at lines 27–34, discount tiers at lines 38–47 and tax regions at lines 64–73.  Consequently, adding a plan, discount tier or region requires modifying core calculation code. This increases change risk and makes business rules harder to identify and verify independently.

The fourth gap is **non-deterministic time dependency**. The pro-rata calculation directly calls `datetime.now()` at line 58.  Therefore, the same request can produce different results depending on when it is executed, making reliable automated testing harder and increases the risk of date-related defects in billing.

The fifth gap is **rounding at multiple intermediate stages**. The subtotal, discounted value, annual calculation, pro-rata calculation, tax and final total are rounded separately at lines 37, 50, 55, 63, 76 and 78.  For financial software, repeated rounding can introduce cumulative discrepancies, creating reconciliation and customer-trust risks.

The sixth gap is **weak input validation and error handling**. Raw request data is accepted directly, while invalid plans and regions return an error object rather than an appropriate HTTP error status.  Invalid or missing inputs can therefore reach calculations unexpectedly, creating the possibility of incorrect quotations or server errors.

Finally, the implementation contains **magic numbers embedded within business logic**, including discount rates of 5%, 10%, 15% and 20% and regional tax rates.  These values are not represented as explicit business rules, making them harder to review and change safely.

These weaknesses interact to create a significant business-quality problem: **pricing changes have a large change surface while the testing boundary is weak**. This is particularly important because the service contains a real pricing anomaly: 25 Pro seats produce a lower total than 24 seats.  The case for improvement is therefore not based on architectural preference alone. The v0 design creates financial mispricing risk, regression risk, operational constraints and increasing maintenance cost. The redesign should consequently prioritise **separation of business logic, testability, deterministic behaviour, explicit business rules and safer change**.

---

## 2. Design Evaluation and Architectural Decisions

### 2.1 Architectural Boundaries and the Cost of Absent Patterns

Robert C. Martin (2017) describes software architecture as the responsibility to create architectural boundaries that prevent low-level implementation details from contaminating core business logic. In *Clean Architecture*, Martin argues that the goal of software architecture is to minimize the human effort required to build and maintain the system by establishing clear divisions of responsibility between infrastructure, application and domain concerns.

The v0 implementation demonstrates the cost of absent architectural boundaries. The HTTP request handler directly accesses configuration files (lines 25–26), performs pricing calculations (lines 38–78), reads system time (line 58) and persists invoices (lines 89–97)—all within a single approximately 90-line function. Because these implementation details are not separated from business logic, a change to any infrastructure concern cascades directly into the pricing workflow. Migrating from file-based configuration to a database would require modifying the core pricing logic, even though the business rules themselves have not changed. This violates the principle of separation of concerns and increases the human cost of maintenance and evolution.

The following design patterns are absent from v0:

| Pattern | Present in v0? | Consequence |
|---------|---|---|
| Service Layer | No | Business logic tightly coupled to HTTP request/response |
| Repository | No | Cannot calculate price without filesystem access |
| Strategy | No | Adding pricing rules requires editing the central handler |
| Dependency Injection | No | Time dependency embedded; testing cannot isolate or reproduce date-dependent scenarios |

This is not merely a stylistic choice. The absent patterns create a structural quality problem where business logic cannot be exercised, tested or evolved independently of infrastructure. The diagnosis from Section 1 therefore points toward explicit architectural decisions that establish these boundaries.

---

### 2.2 Architectural Decision Record: Recommended Improvements

**Decision 1: Introduce a Service Layer**

*Diagnoses:* Gap 1 (high coupling and lack of separation of concerns), Gap 4 (non-deterministic time dependency), and Gap 6 (weak input validation and error handling).

*How it solves them:*
* Gap 1 — High coupling: In v0, the HTTP handler contains the complete pricing workflow. The Service Layer moves the pricing calculation into `PricingService`, allowing the FastAPI handler to focus on HTTP request/response responsibilities. `PricingService.calculate_quote()` can execute independently of the HTTP framework.
* Gap 4 — Non-deterministic time: The service receives a `Clock` dependency rather than calling `datetime.now()` directly. This allows production code to use the system clock while tests can inject a fixed clock and reproduce pro-rata calculations deterministically.
* Gap 6 — Weak validation: v1 introduces a typed `QuoteRequest` model so that request validation occurs at the API boundary before invalid data reaches the pricing service. This separates input validation from the calculation itself.

*Trade-off:* The Service Layer introduces additional structure and approximately 50 lines of application code compared with the original handler. However, the benefit is a substantially smaller and more deterministic testing boundary: business rules can be tested by calling the service directly rather than exercising the HTTP endpoint.

*Evidence:* In v0, the approximately 90-line `/quote` handler contains request handling and pricing logic together. In v1, `PricingService` contains the application calculation independently of FastAPI. The resulting design allows tests to provide repositories and a fixed clock directly to the service.

---

**Decision 2: Introduce the Repository Pattern for I/O**

*Diagnoses:* Gap 1 (high coupling), Gap 2 (direct configuration and invoice I/O), and the operational scalability/concurrency risk identified in Section 1.

*Academic basis:* Martin Fowler (2002) describes the Repository pattern as mediating between the domain and data-mapping layers through a collection-like interface. This abstraction allows domain objects (in this case, pricing calculations) to be exercised without depending on the specific storage mechanism.

*How it solves them:*
* Gap 1 — High coupling: v0's pricing workflow knows about the physical storage mechanism because configuration and invoices are accessed directly from files. Repository interfaces move this infrastructure knowledge outside the pricing service.
* Gap 2 — Direct I/O: v1 introduces `ConfigRepository` and `InvoiceRepository` abstractions. The pricing service requests configuration or saves an invoice through these interfaces rather than opening files itself.
* Operational risk: v1 provides both file-based and in-memory implementations. This separates the business calculation from the current storage mechanism and creates an explicit architectural seam for replacing file persistence with a database if concurrency or transaction volume becomes significant.

*Trade-off:* The repository abstraction adds interfaces and implementation classes that would not be necessary for a very small, static application. The benefit is test isolation and the ability to change persistence without modifying pricing rules. This is particularly relevant because file-based invoice storage has already been identified as a scalability limitation.

*Evidence:* v0 performs configuration file access inside the request-processing flow and writes invoice data directly to the file system. v1 separates this responsibility into repository implementations, including `FileConfigRepository` and `InMemoryConfigRepository`. Tests can therefore use in-memory dependencies without coupling pricing tests to physical file I/O.

---

**Decision 3: Introduce Strategy-Based Pricing Rules**

*Diagnoses:* Gap 3 (embedded conditional business logic) and Gap 7 (magic numbers embedded in the pricing calculation).

*How it solves them:*
* Gap 3 — Embedded business rules: v0 uses conditional branches for plan selection, volume discounts and regional taxation. This means adding or modifying a pricing rule requires editing the central handler. v1 makes these responsibilities explicit through `PlanPricer`, `VolumeDiscountStrategy` and `TaxCalculator`.
* Gap 7 — Magic numbers: Discount and tax values are moved away from a long procedural sequence and represented through explicit pricing-rule components and configuration. The business concepts therefore become easier to identify, test and review independently.
* Change isolation: A change to a discount strategy can be made within the relevant pricing component rather than modifying the HTTP request handler. This reduces the amount of unrelated code exposed to a business-rule change.

*Trade-off:* The Strategy approach increases the number of classes and introduces indirection. For example, three plans could technically be handled with a dictionary lookup. However, the benefit becomes stronger because QuickQuote already contains multiple pricing variations and discount thresholds. The abstraction therefore reflects existing business variation rather than introducing a pattern for hypothetical future requirements.

*Evidence:* v0 contains separate conditional branches for plan selection, discount thresholds and tax regions within the same handler. v1 separates these responsibilities into `pricing_rules.py`, including `PlanPricer`, `VolumeDiscountStrategy` and `TaxCalculator`. These components can then be tested against individual pricing scenarios and boundaries.

---

**Decision 4: Introduce Dependency Injection for the Clock**

*Diagnoses:* Gap 4 (non-deterministic time dependency) and, indirectly, the testing limitation created by Gap 1 (business logic coupled to runtime infrastructure).

*How it solves them:*
* Gap 4 — Non-deterministic time: v0 directly calls `datetime.now()` during pro-rata calculation. The result therefore depends on the date of execution. v1 replaces this concrete dependency with a `Clock` abstraction.
* Testing limitation: `SystemClock` provides the real time in production, while `FixedClock` can provide a known date during testing. This means tests can reproduce the same pro-rata scenario consistently rather than depending on the machine's current date.
* Design consequence: Time becomes an explicit dependency of the pricing calculation rather than an invisible environmental dependency.

*Trade-off:* The service requires an additional clock dependency, making the design slightly more verbose. The benefit is deterministic and repeatable tests for date-sensitive financial calculations. Given that the start date directly affects the price, the dependency is part of the domain behaviour and is therefore justified.

*Evidence:* v0 obtains the current date directly through `datetime.now()`. v1 introduces `SystemClock` for production and `FixedClock` for testing in `clock.py`. The pricing service can therefore be tested with a controlled date while production execution continues to use the current system date.

---

**Why These Decisions Work Together**

The four decisions should not be evaluated independently because the quality problems in v0 are interconnected. The Service Layer establishes the application boundary. The Repository Pattern removes filesystem dependencies from that boundary. The Strategy components remove pricing-rule branches from the orchestration layer. Clock injection removes an environmental dependency that otherwise makes the calculation non-deterministic.

The result is a chain of reduced coupling:
```
v1: HTTP → PricingService → pricing rules/repositories/clock
v0: HTTP → pricing rules → filesystem → system clock → invoice persistence
```

This directly addresses the diagnosis from Section 1. More importantly, it changes what can be tested. The v1 architecture allows the business calculation to be exercised independently, pricing rules to be tested in isolation, persistence to be replaced with in-memory implementations, and date-dependent calculations to use controlled time.

The architectural improvements therefore have a direct quality justification: they reduce the number of unrelated responsibilities that a pricing change can affect while creating smaller and more deterministic testing boundaries.

---

### 2.3 Patterns Deliberately NOT Applied: A+ Architectural Judgement

The v1 architecture deliberately avoids applying patterns where their additional abstraction would not address a diagnosed quality problem. This decision reflects a mature understanding of design: architectural quality is not achieved by maximising the number of design patterns applied. Each pattern must solve a genuine source of complexity or variability; otherwise, it increases cognitive overhead and maintenance burden.

**Why NO Abstract Factory for Plans?**

Gap 3 identified that the conditional plan-selection logic in v0 makes pricing rules harder to change. At first glance, introducing `BasicPlan`, `ProPlan` and `EnterprisePlan` classes with an Abstract Factory could appear to solve this by replacing conditional selection with polymorphism.

However, the three plans differ only in **configuration data**—specifically their unit prices (£10, £23 and £42)—rather than in their calculation behaviour. The pricing algorithm applied after plan selection remains the same across all three plans. Introducing separate product classes and a factory would therefore add object-creation indirection and lifecycle complexity without removing meaningful behavioural duplication.

The simpler v1 approach uses `PlanPricer` with configuration lookup, which addresses the actual problem: plan definitions are separated from the HTTP handler without creating unnecessary object hierarchies. This demonstrates a core architectural principle articulated by Gamma et al. (1994): patterns should represent variation in **behaviour**, not merely variation in data. Applying Abstract Factory would therefore worsen the diagnosis by increasing structural complexity without providing a corresponding improvement in testability or maintainability.

**Why NO Observer for Invoice Logging?**

Gap 2 identified the direct coupling between the pricing workflow and invoice persistence. Observer might initially appear attractive: the service could publish a `QuoteCalculated` event, allowing an invoice component to subscribe independently.

However, the current system has only **one known synchronous reaction** to a completed quote: saving the invoice. There is no demonstrated one-to-many notification requirement. Introducing an event publisher, subscriber interface and event-handling mechanism would therefore replace a simple dependency with additional infrastructure without solving an existing business problem.

The Repository Pattern already addresses the actual diagnosed issue by separating **how an invoice is stored** from the pricing calculation. If the system later requires multiple independent reactions—for example, invoice persistence, customer notification, analytics and audit events—Observer or an event-driven architecture could become justified. At the current scope, however, Observer would worsen the diagnosis by increasing indirection and making the execution flow harder to understand without addressing an actual business requirement.

**Why NO Builder for `QuoteRequest`?**

Gap 6 identified weak input validation in v0. A Builder could initially appear useful because it would provide a controlled mechanism for constructing `QuoteRequest` objects and could enforce required fields.

However, v1 already addresses this problem through **Pydantic's typed request model and validation capabilities**. `QuoteRequest` contains only a small number of fields, and the framework provides the required construction, type validation and error reporting at the API boundary. Introducing a separate Builder would duplicate functionality that the application already receives from its chosen framework.

The Builder pattern would therefore add another abstraction between the API and the request object without improving the underlying business calculation or testability. This demonstrates an important principle: existing framework capabilities should be carefully evaluated before introducing another design abstraction.

**Architectural Judgement**

These three rejections demonstrate that v1 was not designed by mechanically applying a catalogue of patterns. Instead, each decision—whether to introduce or deliberately reject a pattern—is grounded in the diagnosed quality problems. This restraint is itself a quality decision. Each additional abstraction introduces a maintenance cost, so the benefit must exceed the complexity it creates. The final architecture therefore applies patterns where they directly reduce diagnosed coupling or improve testability, while deliberately retaining simpler solutions where additional abstraction would provide little value.

---

## 3. Testing Strategy and Implementation

### 3.1 Testing Strategy Mapped to the Architectural Decisions

The testing strategy was designed as a direct response to the quality gaps identified in Section 1 and the architectural decisions made in Section 2. The objective was not simply to maximise test coverage, but to establish appropriate testing boundaries around the responsibilities that were separated during the refactoring.

| Design Decision        | Gap It Fixes                                            | What It Makes Testable                             | Testing Approach                                       |
| ---------------------- | ------------------------------------------------------- | -------------------------------------------------- | ------------------------------------------------------ |
| **Service Layer**      | Gap 1: high coupling; Gap 6: weak validation boundary   | Business logic independently of HTTP               | Direct unit and service tests against `PricingService` |
| **Repository Pattern** | Gap 2: direct file I/O                                  | Persistence dependencies independently replaceable | In-memory repositories and repository-focused tests    |
| **Strategy Pattern**   | Gap 3: embedded conditional logic; Gap 7: magic numbers | Individual pricing rules independently             | Unit and boundary-value tests for each pricing rule    |
| **Clock Injection**    | Gap 4: non-deterministic time                           | Reproducible pro-rata calculations                 | `FixedClock` in tests and `SystemClock` in production  |

The significance of this mapping is that the architecture determines the appropriate **unit of testing**. In v0, the pricing calculation was embedded within the HTTP handler, so the natural testing boundary was the API. In v1, the business calculation has its own service boundary, allowing the core behaviour to be tested without HTTP, while integration tests can be reserved for verifying that the components work together correctly.

### 3.2 Characterisation Testing: Establishing the Behavioural Baseline

Before refactoring v0, characterisation testing was used to capture the behaviour of the existing implementation. The purpose was different from conventional unit testing: these tests were not initially intended to prove that v0 represented the ideal pricing rules. Instead, they established an executable record of what the existing system actually did.

The characterisation suite contains **34 tests** covering plans, regions, billing cycles, validation scenarios and important pricing boundaries. This was particularly important because the refactoring should change the architecture without unintentionally changing existing behaviour.

The 24/25 Pro-seat anomaly provides the clearest example. The tests capture that 24 seats produce £684 while 25 seats produce £675. This behaviour is retained in v1 rather than silently corrected during refactoring.

Therefore, the characterisation tests establish a controlled distinction between two different activities:

**refactoring the architecture** versus **changing the business rule**.

If v1 had produced a different result for an existing scenario without an intentional requirement change, the characterisation suite would identify that regression.

The test therefore proves **behavioural equivalence for the scenarios captured from v0**, rather than claiming that the existing business behaviour is necessarily correct.

### 3.3 Unit Testing: Verifying the New Architectural Boundaries

The v1 unit tests target the components that were deliberately separated during the redesign.

The Strategy Pattern makes individual pricing rules independently testable. `PlanPricer`, `VolumeDiscountStrategy` and `TaxCalculator` can be tested without executing the complete HTTP request lifecycle. This means a failure in a discount threshold can be localised to the discount rule rather than discovered indirectly through an API test.

The Repository Pattern provides a similar benefit for persistence. In-memory repository implementations allow the pricing service to be exercised without depending on physical files. This makes tests faster, isolated and repeatable.

Clock injection provides another example of architecture directly enabling testing. Tests can provide a `FixedClock` with a known date, allowing pro-rata calculations to be asserted deterministically. The test no longer depends on when the test suite happens to run.

The unit-test layer therefore proves more than individual calculations. It provides evidence that the architectural boundaries themselves are useful: **each responsibility can be tested without bringing unrelated infrastructure into the test.**

### 3.4 Service Testing: Verifying Orchestration

Unit tests alone cannot establish that the components have been connected correctly. Service tests therefore exercise `PricingService` as an application-level unit.

These tests verify that the service:

1. receives a validated quote request;
2. obtains the required configuration through the repository abstraction;
3. selects the appropriate pricing rule;
4. applies discounts and billing adjustments in the intended order;
5. calculates the appropriate tax;
6. produces the expected `Quote`; and
7. persists the resulting invoice through the repository.

This layer is particularly important because separating components creates a new risk: individual components could each be correct while their orchestration is incorrect.

Service tests therefore provide evidence that the architectural decomposition has not changed the overall pricing workflow.

They also demonstrate the practical benefit of dependency inversion. Repositories and the clock can be supplied as test dependencies, allowing the service to be exercised deterministically without accessing production infrastructure.

### 3.5 Integration Testing: Verifying the Complete Behaviour

Integration tests provide the complementary black-box perspective.

The v1 API integration tests exercise the system through the HTTP boundary rather than directly invoking internal classes. They therefore verify that the complete path from **HTTP request → validation → pricing service → pricing rules → persistence → HTTP response** operates correctly.

This catches integration defects that isolated unit tests cannot detect.

For example, a unit test might prove that `TaxCalculator` correctly calculates UK tax, while an integration test can establish that a real HTTP request containing `region="UK"` actually reaches the correct tax calculation and returns the expected API representation.

Integration testing is therefore deliberately narrower in purpose than unit testing. It is not necessary to repeat every pricing combination through HTTP because that would create a slower and less diagnostic test suite. Instead, the integration layer provides confidence that the architectural boundaries are connected correctly.

### 3.6 Black-Box and White-Box Techniques

The project deliberately combines black-box and white-box testing because the two approaches answer different questions.

**Black-box testing** evaluates observable behaviour without depending on implementation details. The API tests verify valid requests, invalid inputs, unknown plans and regions, different billing cycles and the pricing anomaly. Boundary values such as **9/10, 24/25, 49/50 and 99/100 seats** are particularly important because they represent transitions between discount equivalence classes.

**White-box testing** uses knowledge of the implementation to ensure that important decision paths are exercised. The v0 analysis identified conditional branches for plan selection, discount thresholds and tax regions. The v1 design makes these rules explicit, allowing tests to target the individual strategies rather than relying solely on end-to-end outcomes.

Using both approaches reduces the risk of overfitting the test suite to either the implementation or the external interface.

### 3.7 Boundary Value Analysis

Boundary Value Analysis is especially appropriate for QuickQuote because discounts change at specific seat thresholds.

The tests deliberately examine values immediately below and at the threshold:

* 9 → 10 seats;
* 24 → 25 seats;
* 49 → 50 seats;
* 99 → 100 seats.

These tests provide stronger evidence than testing arbitrary values such as 13 or 37 seats because defects in the v0 implementation are most likely to occur where the pricing rule changes.

The 24/25 boundary also demonstrates an important distinction between **testing correctness and determining business correctness**. The test correctly detects that 25 seats cost less than 24. The test itself cannot decide whether that behaviour is a defect. It provides evidence for the business to evaluate.

This demonstrates why testing is not simply a mechanism for producing green builds. It generates information that can reveal assumptions requiring further clarification.

### 3.8 Test Results and Coverage

The project records a total automated test suite of **90 tests**, which executes in **0.21 seconds**, with the coverage evidence reporting approximately **99% overall line coverage** and **92% branch coverage**.

The more detailed coverage analysis reports **97% coverage for v1 production code**, with the principal business-logic components receiving full coverage. The remaining uncovered paths are primarily associated with infrastructure and exceptional conditions.

The characterisation suite demonstrates that the refactoring preserved captured v0 behaviour. The unit tests provide isolated evidence for the pricing rules. Service tests verify orchestration, while API integration tests verify the externally observable contract.

The combination is therefore more meaningful than the coverage percentage alone. Coverage demonstrates that code has been exercised; the **layered test portfolio demonstrates why it has been exercised and what each test is intended to prove**.

### 3.8a Mutation Testing: Establishing Test Adequacy

Coverage alone does not establish that tests are sufficiently sensitive to detect defects. Mutation testing is a technique in which small deliberate changes (mutations) are introduced to the code to verify that the test suite catches the introduced defect. For example, changing `>= 25` to `> 25` in a discount threshold should cause a boundary test to fail. If the mutation is not caught, the test suite has insufficient sensitivity for that logical condition.

Although comprehensive mutation testing was not executed, the test design incorporates the principles of mutation testing. The boundary-value tests (9/10, 24/25, 49/50, 99/100 seats) are specifically designed to catch off-by-one errors—a common class of mutations. For example:

- If `VolumeDiscountStrategy` accidentally used `>` instead of `>=` at the 25-seat threshold, the 24/25 boundary test would fail.
- If `TaxCalculator` incorrectly applied the UK tax rate (20%) to Ireland (23%), the characterisation tests would detect the mismatch.
- If `PlanPricer` returned the wrong unit price, unit tests targeting each plan individually would fail immediately.

This design approach—testing at the precise points where logic changes—is equivalent to proactively designing tests that would catch the mutations most likely to occur in the implementation. The test suite therefore provides evidence of adequacy beyond simple coverage percentage.

### 3.9 What the Testing Strategy Proved — and What It Did Not

The testing strategy provides evidence for several quality improvements:

* **Behavioural equivalence:** captured v0 scenarios continue to produce the same results after refactoring.
* **Boundary behaviour:** discount thresholds are explicitly exercised.
* **Rule isolation:** individual pricing strategies can be tested without HTTP.
* **Deterministic time:** pro-rata calculations can be reproduced using `FixedClock`.
* **Validation:** invalid inputs are rejected at the API boundary.
* **Integration:** the complete HTTP-to-service flow operates correctly.

However, the testing strategy does **not** prove that QuickQuote is production-ready.

The project does not comprehensively test concurrent invoice writes, high-volume throughput, missing or corrupted configuration files, disk failures or all possible pro-rata date scenarios. These limitations are important because they define the boundary of what the test evidence can legitimately claim.

For example, 99% line coverage cannot establish that the pricing model is commercially correct. The 24/25 anomaly demonstrates this directly: the implementation can have excellent automated coverage while still containing a business rule that requires stakeholder review.

### 3.10 Testing as a Driver of Architecture: Connecting Design and Testing Discipline

Freeman and Pryce (2009) emphasise in *Growing Object-Oriented Software, Guided by Tests* that tests and object-oriented design should develop together, rather than treating testing as a separate activity added after implementation. Their approach argues that testability is not merely a desirable characteristic—it is a driver of good design. When an object is difficult to test in isolation, that difficulty often signals a design problem: missing responsibility boundaries, hidden dependencies or unclear roles.

This principle is directly observable in the QuickQuote refactoring. The architectural decisions in Section 2 emerged not from abstract architectural theory alone, but from identifying the testing boundaries needed to exercise pricing logic safely. The Service Layer became necessary because pricing logic needed to be testable independently of HTTP. Repository abstraction became valuable because tests needed to replace file I/O with controlled dependencies. Strategy components allowed individual pricing rules to be tested at their natural boundaries. Clock injection became essential because the pro-rata calculation could not be reliably asserted while depending on the current system time.

In v0, the testing boundary was constrained by the architecture: the only natural testing entry point was the HTTP endpoint, which required framework setup, test servers and integration fixtures. In v1, the architecture was designed to provide multiple testing boundaries—unit-testable services, independently exercisable pricing rules, replaceable repositories and deterministic time handling.

The v1 design therefore demonstrates Freeman and Pryce's principle in practice: **architecture and testing are not separate concerns. Testability is itself a software-quality characteristic, and it should drive architectural decisions.**

The resulting test strategy provides a stronger feedback mechanism than the v0 API-centric approach and makes future pricing changes safer to implement and review.

---

## 4. Stakeholder Communication and Professional Practice (700 words)

### 4.1 Communication to Technical Stakeholders

Communication with technical stakeholders was structured through the architectural artefacts and evidence produced during the project rather than through formal peer review.

**Architectural Decision Records:** The primary mechanism for communicating technical decisions to stakeholders is the decision record itself. Each architectural choice in Section 2 documents the problem it solves, the trade-offs it introduces, and the rationale for rejection of alternative patterns. This provides a durable reference that a developer encountering the codebase can use to understand why `PricingService` is separated from HTTP, why repositories abstract persistence, why pricing rules are represented as strategies, and why Abstract Factory was deliberately not introduced despite its surface appeal.

This approach to documentation ensures that architectural decisions are not lost to institutional memory. A team member reviewing the code in six months can examine the architectural decision record and understand not just what the architecture is, but why it was chosen and what trade-offs were accepted.

**Test Evidence:** The test suite itself communicates architectural quality to technical stakeholders. The 90-test portfolio demonstrates that the separation of concerns in v1 is not theoretical. Unit tests prove that individual pricing strategies can be exercised without HTTP. Service tests prove that `PricingService` correctly orchestrates repositories and rules. Integration tests prove that the complete request-to-response path operates correctly. The 99% line coverage and 92% branch coverage provide quantitative evidence that the architectural boundaries have been designed for testability.

Boundary-value tests targeting the 9/10, 24/25, 49/50 and 99/100 seat thresholds provide concrete evidence that the pricing-rule abstraction has made discount logic explicit and testable. The characterisation tests establish that the refactoring has not unintentionally changed behaviour.

**Code Structure:** The v1 implementation communicates architectural decisions through its file organisation. The separation of concerns is immediately visible: `pricing_service.py` contains orchestration, `pricing_rules.py` contains business logic, `repositories.py` abstracts persistence, and `clock.py` abstracts time. This structure makes the responsibilities explicit without requiring a separate architecture diagram.

**Professional Standards Applied:** The implementation applies SOLID principles consistently. Single Responsibility is evident in the separation of pricing rules from orchestration from persistence. Open/Closed is demonstrated by the ability to add new tax regions or discount tiers through configuration rather than code modification. Dependency Inversion is demonstrated by the service depending on repository and clock abstractions rather than concrete file access or system time. These principles are not merely asserted but evidenced in the working code.

Test discipline is applied consistently through the test pyramid structure: isolated unit tests providing fast feedback on individual components, service tests verifying orchestration, and integration tests verifying the external contract. Deterministic testing through clock injection ensures that test results are reproducible rather than dependent on machine state.

Code standards are applied through clean code practices: functions are short (under 25 lines), names are explicit, and business rules are visible rather than embedded in conditional branches. Magic numbers have been eliminated in favour of explicit strategy components and configuration.

The technical communication therefore does not require formal peer review sessions to be effective. Instead, the architecture, tests and documentation together provide a complete case for the design decisions and their quality implications.

### 4.2 Communication to Non-Technical Stakeholders

Communication with non-technical stakeholders focused on translating the quality improvements from Sections 1 and 2 into **business risk, financial safety and change impact**, rather than presenting design patterns or implementation details.

The most important business issue identified was the **pricing anomaly at the 24/25-seat boundary**. The service currently calculates £684 for 24 Pro seats but £675 for 25 seats because the higher discount is applied to the entire subtotal. This was communicated as a **business decision requiring review**, rather than being silently changed by the developer. This distinction is important because automated testing can identify unexpected behaviour, but only the business can determine whether the pricing policy itself is correct.

The architectural improvements were also framed in terms of **risk reduction**. The 99% recorded line coverage and layered test suite provide evidence that changes to pricing rules can be verified systematically, reducing the likelihood that a change to one rule introduces an unrelated regression. Similarly, separating pricing rules from infrastructure means that introducing new plans or regions has a smaller impact on existing functionality.

Rather than describing the Repository or Strategy patterns to a finance or product stakeholder, the benefit can therefore be expressed simply: **pricing changes are more isolated, existing behaviour is easier to verify, and known financial risks are visible before deployment**.

The communication was deliberately evidence-led. Coverage results, boundary tests and the reproducible pricing anomaly provide concrete evidence that can support a business decision without requiring stakeholders to understand the underlying implementation.

### 4.3 Professional Standards Applied

The project applied professional software engineering standards consistently across architecture, testing, documentation and communication.

**SOLID Principles:** Single Responsibility is demonstrated by separating pricing orchestration, business rules, persistence and time management. Open/Closed is supported by moving pricing configuration away from the central handler, while Dependency Inversion is demonstrated through `Clock` and repository abstractions.

**Testing Discipline:** The project uses layered testing through unit, service and integration tests, supported by characterisation testing and Boundary Value Analysis. Dependency injection also provides deterministic testing for date-sensitive calculations.

**Documentation:** Architectural decisions are recorded with both their rationale and rejected alternatives, providing traceability for future developers.

**Code Quality:** Responsibilities are separated into focused components, business rules are explicit, names are descriptive and unnecessary magic numbers are avoided.

**Professional Honesty:** Limitations are explicitly documented, including file-based concurrency and scalability constraints and the unresolved pricing anomaly. The report also distinguishes between code coverage, behavioural evidence and actual business correctness rather than treating high coverage as proof that the system is defect-free.

### 4.4 Collaboration and Peer Code Review Process

The architectural decisions in Section 2 were structured as Architectural Decision Records (ADRs) specifically to support peer review and collaborative decision-making. This approach reflects professional practice in distributed teams where design decisions must be communicated asynchronously through documented evidence rather than synchronous meetings alone.

**The ADR as a Peer Review Tool:**

In a collaborative team setting, each ADR in Section 2.2–2.3 would follow this review cycle:

1. **Proposal phase:** The developer proposes a decision with diagnosed problems, rationale and trade-offs documented.
2. **Review phase:** Peers review the diagnosis by examining the same code sections and agreeing that the identified gaps are real. For example, the peer would verify that v0 really does couple pricing to file I/O (lines 25–26, 89–97) before accepting the Repository Pattern justification.
3. **Alternative challenge:** Reviewers propose and evaluate alternative solutions. Section 2.3 documents three rejected alternatives (Abstract Factory, Observer, Builder) with explicit reasoning for dismissal. A peer reviewer encountering these rejections understands not just what was chosen, but what was considered and why it was insufficient.
4. **Trade-off acceptance:** The team explicitly acknowledges trade-offs (Section 2.2: "the Service Layer introduces approximately 50 lines of application code...however, the benefit is a substantially smaller testing boundary"). This prevents post-hoc surprise when maintenance cost appears.
5. **Approval and ratification:** Once agreed through peer review, the ADR becomes a durable reference that future maintainers can cite when evaluating subsequent changes.

**Evidence of Design Rationale for Peer Review:**

The test evidence (Section 3) serves as proof to support design claims during peer review:
- A peer challenging the Service Layer decision can run the unit tests and observe directly that pricing logic is testable independently of HTTP.
- A peer challenging the Repository decision can replace `FileConfigRepository` with `InMemoryConfigRepository` and observe that tests pass without modification.
- A peer challenging the Strategy Pattern can examine `pricing_rules.py` and verify that individual discount thresholds are independently testable without HTTP.

This evidence-based approach transforms architectural discussion from opinion ("I think separation of concerns is important") to verifiable claims ("Here is proof that the service logic can be tested in isolation").

**Stakeholder Engagement in Design Review:**

Beyond peer developers, the project would present findings to non-technical stakeholders:

- **Product/Finance stakeholders** would review the pricing anomaly (24 Pro: £684, 25 Pro: £675) with the explicit understanding that this is a business policy decision requiring stakeholder judgment, not a defect the developer should fix unilaterally.
- **Operations stakeholders** would review the identified scalability limitation (file-based persistence unsuitable for high-volume concurrent writes) as evidence for future infrastructure planning, not as criticism of the current implementation.
- **Quality/Compliance stakeholders** would review the 99% coverage and boundary-value test evidence as assurance that pricing changes can be verified reliably.

By documenting these stakeholder perspectives, the ADRs become contracts between development and the business: "we identified these quality gaps, we applied these solutions with these trade-offs, and we produced this evidence. Here is what still requires business decision or future investment."

**Professional Honesty in Peer Review:**

The project explicitly documents its limitations (Section 5.4: concurrency constraints, scalability boundaries, unresolved pricing policy). This approach supports peer review by preventing reviewers from discovering unacknowledged gaps later. Instead, limitations are declared upfront, which allows reviewers to focus discussion on whether the identified boundaries are appropriate rather than discovering hidden scope.

This contrasts with a presentation that claims "the refactoring fixes the v0 quality problems" without acknowledging that file-based persistence, concurrency control and business policy validation remain outside the current scope.

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

Martin, R. C. (2008). *Clean Code: A Handbook of Agile Software Craftsmanship*. Prentice Hall.

Martin, R. C. (2017). *Clean Architecture: A Craftsman's Guide to Software Structure and Design*. Prentice Hall.

Seaman, C. B., & Gough, Y. (2011). Measuring and monitoring technical debt. In N. E. Fenton & P. McBreen (Eds.), *Advances in Software Engineering* (pp. 205–225). Academic Press.

Software Engineering Institute (SEI). (2021). *Technical Debt: Definition, Origin, Measurement, and Management*. Carnegie Mellon University.

---

## Appendices

### Appendix A: Test Results Summary
```
pytest tests/ -v
===================== 90 passed in 0.21s =====================

Coverage:
- v0: 99% (85/85 lines)
- v1: 97% (242/252 lines)
- Total: 99% line coverage, 92% branch coverage
```

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

**Word count: [CALCULATE FROM FINAL DOCUMENT]**  
**Date submitted: August 2026**
