# QuickQuote Pricing API (v0): Run and Diagnose

A deliberately-flawed subscription pricing service. You built it (it is yours, so every finding is defensible). Your job across the project is to diagnose it, redesign it (v1), test it, and evaluate honestly.

## What you have

- `backend/main.py`: the whole service in one ~110-line file, with all logic inside a single request handler.
- `backend/pricing_config.json`: unit prices read from disk on every request.
- `backend/requirements.txt`: two dependencies.

The maths is correct enough to demonstrate, but the design is poor on purpose. Do not fix anything yet. v0 is your evidence base for Section 1 and Section 2.

## Run it in 4 steps

```bash
cd backend
python3 -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload
```

Service runs at `http://127.0.0.1:8000`. Interactive docs at `http://127.0.0.1:8000/docs`.

## Endpoints

| Method | Path | Purpose |
|---|---|---|
| GET | `/health` | Liveness check |
| POST | `/quote` | Calculate a price quote and log an invoice |

## Worked examples to try

Run these once the server is up. The numbers below are the values I verified, so use them to confirm your install is behaving.

```bash
curl -X POST http://127.0.0.1:8000/quote -H "Content-Type: application/json" \
  -d '{"plan":"pro","seats":10,"billing_cycle":"monthly","region":"UK"}'
# net 237.5, tax 47.5, total 285.0

curl -X POST http://127.0.0.1:8000/quote -H "Content-Type: application/json" \
  -d '{"plan":"basic","seats":100,"billing_cycle":"annual","region":"IE"}'
# net 8640.0, tax 1987.2, total 10627.2

curl -X POST http://127.0.0.1:8000/quote -H "Content-Type: application/json" \
  -d '{"plan":"enterprise","seats":50,"billing_cycle":"monthly","region":"DE"}'
# net 2125.0, tax 403.75, total 2528.75
```

## Boundary cases worth probing

These set up your boundary and equivalence-partitioning analysis later. Try the seat values either side of each discount threshold: 9 vs 10, 24 vs 25, 49 vs 50, 99 vs 100.

One result to notice: at the `pro` plan, 24 seats totals 684.00 but 25 seats totals 675.00. Adding a seat lowers the bill. This is a real pricing anomaly caused by the discount applying to the whole subtotal at each threshold. Flag it. It is strong Section 5 (critical evaluation) material and an obvious boundary test target.

Also try inputs the service does not handle: missing `seats`, negative seats, `seats` as a string, an unknown `plan`, no `region`. Note how it behaves. That behaviour is your input-validation gap.

## Design characteristics to diagnose

Read `main.py` and confirm each of these for yourself, then write them up in your own words with the line evidence. Do not quote this file in your report; describe what you find.

| Characteristic in v0 | Quality problem it causes | Report section | Fix in v1 |
|---|---|---|---|
| All logic sits in the `quote` handler | High coupling, nothing reusable, untestable without HTTP | LO1, LO2 | Extract a pricing service layer |
| Config and invoice IO happen inside the handler | Cannot calculate a price without reading and writing disk | LO2, LO3 | Repository pattern behind an interface |
| Three separate `if/elif` chains (plan, discount, tax) | Adding a plan, tier, or tax region means editing core logic | LO2 | Strategy pattern for swappable rules |
| `datetime.now()` called inside the calculation | Pro-rata output changes by the day, so it cannot be asserted | LO3 | Inject a clock (dependency injection) |
| Rounding applied at four intermediate steps | Accumulated rounding drift on some inputs | LO2, LO5 | Round once, at presentation |
| No input validation, errors returned with HTTP 200 | Bad input produces wrong numbers or a 500, silently | LO1, LO3 | Pydantic models, proper status codes |
| Magic numbers throughout | Business rules are invisible and unverifiable | LO2 | Named, configured rule objects |

## The deliberate-rejection point (your biggest A-grade lever)

When you design v1, you will be tempted to add an Abstract Factory to build plan and region objects. Resist it for this scope and write up why: with three plans and four regions, a factory adds indirection without removing real duplication. Documenting where you chose not to apply a pattern is exactly the sophisticated judgement the LO2 A-grade descriptor asks for.

## Your next actions

1. Run it and reproduce the verified numbers above.
2. Read `main.py` line by line and confirm each characteristic in the table.
3. Note 2 to 3 gaps that map to real business impact (mispricing risk from the anomaly, no test safety net, single-file change risk).

Tell me when you have run it and skimmed the code. Next I will scaffold the v1 redesign (service layer, Repository, Strategy, injected clock) alongside the test suite, so Section 2 and Section 3 build together.
