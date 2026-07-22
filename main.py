from fastapi import FastAPI, Request
from datetime import datetime
import json
import os
import calendar

app = FastAPI(title="QuickQuote Pricing API")

CONFIG_PATH = os.path.join(os.path.dirname(__file__), "pricing_config.json")
INVOICE_LOG = os.path.join(os.path.dirname(__file__), "invoices.json")


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/quote")
async def quote(request: Request):
    body = await request.json()
    plan = body.get("plan")
    seats = body.get("seats")
    cycle = body.get("billing_cycle")
    region = body.get("region")
    start_date = body.get("start_date")

    with open(CONFIG_PATH) as f:
        config = json.load(f)

    if plan == "basic":
        unit = config["basic"]
    elif plan == "pro":
        unit = config["pro"]
    elif plan == "enterprise":
        unit = config["enterprise"]
    else:
        return {"error": "unknown plan"}

    subtotal = unit * seats
    subtotal = round(subtotal, 2)

    if seats >= 100:
        discount_rate = 0.20
    elif seats >= 50:
        discount_rate = 0.15
    elif seats >= 25:
        discount_rate = 0.10
    elif seats >= 10:
        discount_rate = 0.05
    else:
        discount_rate = 0.0

    discounted = subtotal - (subtotal * discount_rate)
    discounted = round(discounted, 2)

    if cycle == "annual":
        discounted = discounted * 12
        discounted = discounted - (discounted * 0.10)
        discounted = round(discounted, 2)

    if cycle == "monthly" and start_date:
        sd = datetime.strptime(start_date, "%Y-%m-%d")
        now = datetime.now()
        if sd.year == now.year and sd.month == now.month:
            days_in_month = calendar.monthrange(now.year, now.month)[1]
            remaining = days_in_month - sd.day + 1
            discounted = discounted * (remaining / days_in_month)
            discounted = round(discounted, 2)

    if region == "UK":
        tax_rate = 0.20
    elif region == "IE":
        tax_rate = 0.23
    elif region == "DE":
        tax_rate = 0.19
    elif region == "US":
        tax_rate = 0.0
    else:
        return {"error": "unknown region"}

    tax = discounted * tax_rate
    tax = round(tax, 2)
    total = discounted + tax
    total = round(total, 2)

    result = {
        "plan": plan,
        "seats": seats,
        "billing_cycle": cycle,
        "region": region,
        "net": discounted,
        "tax": tax,
        "total": total,
    }

    records = []
    if os.path.exists(INVOICE_LOG):
        with open(INVOICE_LOG) as f:
            records = json.load(f)
    record = dict(result)
    record["issued_at"] = datetime.now().isoformat()
    records.append(record)
    with open(INVOICE_LOG, "w") as f:
        json.dump(records, f, indent=2)

    return result
