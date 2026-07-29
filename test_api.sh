#!/bin/bash

echo "==============================================="
echo "QuickQuote v1 API Testing Script"
echo "==============================================="
echo ""

BASE_URL="http://127.0.0.1:8000"

echo "1. Testing Health Endpoint"
echo "-------------------------------------------"
curl -s -X GET ${BASE_URL}/health | python3 -m json.tool
echo ""
echo ""

echo "2. Testing Basic Plan (10 seats, monthly, UK)"
echo "-------------------------------------------"
curl -s -X POST ${BASE_URL}/quote \
  -H "Content-Type: application/json" \
  -d '{"plan":"basic","seats":10,"billing_cycle":"monthly","region":"UK"}' | python3 -m json.tool
echo ""
echo ""

echo "3. Testing Pro Plan (25 seats, annual, Ireland)"
echo "-------------------------------------------"
curl -s -X POST ${BASE_URL}/quote \
  -H "Content-Type: application/json" \
  -d '{"plan":"pro","seats":25,"billing_cycle":"annual","region":"IE"}' | python3 -m json.tool
echo ""
echo ""

echo "4. Testing Enterprise Plan (50 seats, monthly, US - no tax)"
echo "-------------------------------------------"
curl -s -X POST ${BASE_URL}/quote \
  -H "Content-Type: application/json" \
  -d '{"plan":"enterprise","seats":50,"billing_cycle":"monthly","region":"US"}' | python3 -m json.tool
echo ""
echo ""

echo "5. Testing Volume Discount (100 seats - 20% discount)"
echo "-------------------------------------------"
curl -s -X POST ${BASE_URL}/quote \
  -H "Content-Type: application/json" \
  -d '{"plan":"basic","seats":100,"billing_cycle":"monthly","region":"UK"}' | python3 -m json.tool
echo ""
echo ""

echo "6. Testing Error: Missing seats (should return 422)"
echo "-------------------------------------------"
curl -s -X POST ${BASE_URL}/quote \
  -H "Content-Type: application/json" \
  -d '{"plan":"basic","billing_cycle":"monthly","region":"UK"}' | python3 -m json.tool
echo ""
echo ""

echo "7. Testing Error: Negative seats (should return 422)"
echo "-------------------------------------------"
curl -s -X POST ${BASE_URL}/quote \
  -H "Content-Type: application/json" \
  -d '{"plan":"basic","seats":-5,"billing_cycle":"monthly","region":"UK"}' | python3 -m json.tool
echo ""
echo ""

echo "8. Testing Error: Unknown plan (should return 400)"
echo "-------------------------------------------"
curl -s -X POST ${BASE_URL}/quote \
  -H "Content-Type: application/json" \
  -d '{"plan":"premium","seats":10,"billing_cycle":"monthly","region":"UK"}' | python3 -m json.tool
echo ""
echo ""

echo "9. Testing Pricing Anomaly (24 vs 25 pro seats)"
echo "-------------------------------------------"
echo "24 seats:"
curl -s -X POST ${BASE_URL}/quote \
  -H "Content-Type: application/json" \
  -d '{"plan":"pro","seats":24,"billing_cycle":"monthly","region":"UK"}' | python3 -m json.tool
echo ""
echo "25 seats (cheaper than 24!):"
curl -s -X POST ${BASE_URL}/quote \
  -H "Content-Type: application/json" \
  -d '{"plan":"pro","seats":25,"billing_cycle":"monthly","region":"UK"}' | python3 -m json.tool
echo ""
echo ""

echo "==============================================="
echo "Testing Complete!"
echo "==============================================="
