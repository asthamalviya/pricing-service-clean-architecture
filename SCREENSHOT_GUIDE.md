# 📸 Screenshot Guide for Project Report

Follow these steps to capture screenshots for your project report.

---

## ✅ Already Captured Above

You should have already taken these:

1. ✅ **Screenshot 1:** All 90 tests passing
2. ✅ **Screenshot 2:** 99% coverage report (terminal output)
3. ✅ **Screenshot 3:** HTML coverage report (open `htmlcov/index.html` in browser)

---

## 🚀 Next Steps: Run the API and Capture Screenshots

### Step 1: Start the v1 Server

Open a **NEW terminal** window and run:

```bash
cd /Users/astha.malviya/Desktop/Multiverse/module_7
source .venv/bin/activate
uvicorn main_v1:app --reload
```

You should see output like:
```
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
INFO:     Started reloader process
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

**📸 SCREENSHOT 4: Server startup messages**

---

### Step 2: Open Interactive API Documentation

While the server is running, open your browser and go to:

```
http://127.0.0.1:8000/docs
```

This opens FastAPI's automatic interactive documentation (Swagger UI).

**📸 SCREENSHOT 5: Swagger UI showing both endpoints (/health and /quote)**

---

### Step 3: Test the Health Endpoint in Browser

In the Swagger UI:
1. Click on `GET /health`
2. Click "Try it out"
3. Click "Execute"

You'll see:
```json
{
  "status": "ok",
  "version": "v1"
}
```

**📸 SCREENSHOT 6: Health endpoint response in Swagger UI**

---

### Step 4: Test the Quote Endpoint in Swagger UI

In the Swagger UI:
1. Click on `POST /quote`
2. Click "Try it out"
3. Replace the example JSON with:

```json
{
  "plan": "pro",
  "seats": 10,
  "billing_cycle": "monthly",
  "region": "UK"
}
```

4. Click "Execute"

You'll see Response Code: **200** and response body:
```json
{
  "plan": "pro",
  "seats": 10,
  "billing_cycle": "monthly",
  "region": "UK",
  "net": "237.50",
  "tax": "47.50",
  "total": "285.00"
}
```

**📸 SCREENSHOT 7: Successful quote calculation in Swagger UI**

---

### Step 5: Test Input Validation (Error Handling)

Still in Swagger UI, test with invalid input:

```json
{
  "plan": "basic",
  "seats": -5,
  "billing_cycle": "monthly",
  "region": "UK"
}
```

Click "Execute"

You'll see Response Code: **422** (Unprocessable Entity) with validation error:
```json
{
  "detail": [
    {
      "loc": ["body", "seats"],
      "msg": "ensure this value is greater than 0",
      "type": "value_error.number.not_gt"
    }
  ]
}
```

**📸 SCREENSHOT 8: Input validation error (422) in Swagger UI**

---

### Step 6: Test Unknown Plan Error

Test with unknown plan:

```json
{
  "plan": "premium",
  "seats": 10,
  "billing_cycle": "monthly",
  "region": "UK"
}
```

You'll see Response Code: **400** (Bad Request):
```json
{
  "detail": "Unknown plan: premium"
}
```

**📸 SCREENSHOT 9: Business logic error (400) in Swagger UI**

---

### Step 7: Run API Tests from Command Line

Open a **SECOND NEW terminal** (keep the server running in the first one) and run:

```bash
cd /Users/astha.malviya/Desktop/Multiverse/module_7
source .venv/bin/activate
./test_api.sh
```

This will run 9 different API tests showing:
- Valid requests with different plans/regions
- Volume discounts
- Error handling
- The pricing anomaly (24 vs 25 seats)

**📸 SCREENSHOT 10: Command-line API test results (scroll to show multiple tests)**

---

### Step 8: Test the Pricing Anomaly

In Swagger UI or using curl, test these two requests:

**24 seats:**
```json
{"plan":"pro","seats":24,"billing_cycle":"monthly","region":"UK"}
```
Result: `"total": "684.00"`

**25 seats:**
```json
{"plan":"pro","seats":25,"billing_cycle":"monthly","region":"UK"}
```
Result: `"total": "675.00"` ← **Cheaper!**

**📸 SCREENSHOT 11: Side-by-side showing 25 seats is cheaper than 24 seats**

---

### Step 9: Project Structure

In your terminal, run:

```bash
tree -L 2 -I '.venv|__pycache__|.pytest_cache|htmlcov|.git'
```

Or manually show with:

```bash
ls -la
ls -la v1/
ls -la tests/
ls -la docs/
```

**📸 SCREENSHOT 12: Project directory structure**

---

### Step 10: Git Commit History

```bash
git log --oneline --all --graph
```

**📸 SCREENSHOT 13: Git commit history showing clean progression**

---

### Step 11: Code Quality - Example Component

Show one of your well-structured v1 files. Open in VS Code or display:

```bash
cat v1/pricing_service.py
```

**📸 SCREENSHOT 14: Clean v1 code (pricing_service.py)**

---

### Step 12: Compare v0 vs v1

Show the difference:

```bash
wc -l main.py v1/*.py
```

Output shows:
```
     77 main.py             (v0: monolithic)
    ... v1 files...
    252 total               (v1: organized)
```

**📸 SCREENSHOT 15: Line count comparison showing better organization**

---

### Step 13: Documentation Files

```bash
ls -lh docs/
cat SUBMISSION_SUMMARY.md | head -50
```

**📸 SCREENSHOT 16: Comprehensive documentation files**

---

## 📊 Summary of Screenshots

Your report should include these 16 screenshots:

### Testing & Coverage (3 screenshots)
1. All 90 tests passing
2. 99% coverage report
3. HTML coverage visualization

### API Demonstration (8 screenshots)
4. Server startup
5. Swagger UI overview
6. Health endpoint
7. Successful quote calculation
8. Input validation error (422)
9. Business logic error (400)
10. Command-line API tests
11. Pricing anomaly demonstration

### Code & Structure (5 screenshots)
12. Project structure
13. Git history
14. Clean v1 code example
15. v0 vs v1 comparison
16. Documentation files

---

## 💡 Tips for Good Screenshots

1. **Use high resolution** - Make sure text is readable
2. **Full window** - Show context (terminal prompt, browser tabs)
3. **Highlight key parts** - Use arrows or boxes in your report
4. **Add captions** - Explain what each screenshot shows
5. **Keep consistent** - Same terminal theme, browser zoom level

---

## 🎯 How to Use in Your Report

### Example Report Structure:

#### Section 1: Testing Evidence
- Screenshot 1: "All 90 tests passing in 0.38 seconds"
- Screenshot 2: "Coverage report showing 99% line coverage"
- Screenshot 3: "Interactive HTML coverage report highlighting tested code"

#### Section 2: API Functionality
- Screenshot 4-7: "API running and serving requests"
- Screenshot 8-9: "Proper error handling with correct HTTP status codes"
- Screenshot 10-11: "Known pricing anomaly documented and tested"

#### Section 3: Code Quality
- Screenshot 12-14: "Well-organized code structure with clean architecture"
- Screenshot 15: "v1 has better organization despite more total lines"
- Screenshot 16: "Comprehensive documentation supporting portfolio submission"

---

## 🚀 Quick Command Reference

```bash
# Terminal 1: Run tests
pytest tests/ -v
pytest tests/ --cov=. --cov-report=term-missing
pytest tests/ --cov=. --cov-report=html

# Terminal 2: Start server
uvicorn main_v1:app --reload

# Terminal 3: Test API
./test_api.sh

# Or individual curl commands:
curl -X POST http://127.0.0.1:8000/quote \
  -H "Content-Type: application/json" \
  -d '{"plan":"pro","seats":10,"billing_cycle":"monthly","region":"UK"}' | python3 -m json.tool
```

---

## ✅ Checklist

Before finishing, make sure you have:

- [ ] All 16 screenshots captured
- [ ] Screenshots are high quality and readable
- [ ] Each screenshot has a caption in your report
- [ ] You've explained what each screenshot demonstrates
- [ ] Screenshots are organized by section (Testing, API, Code)
- [ ] You've highlighted the A+ differentiators in your screenshots
- [ ] HTML coverage report is viewable (htmlcov/index.html)
- [ ] Server is running for interactive demonstration if needed

---

**You're ready to create an A+ report!** 🎉
