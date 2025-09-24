#!/bin/bash
# CLI Test Commands for Docker Container
# Run these commands inside the container to test CLI functionality

echo "=== Testing Levo CLI in Docker Container ==="
echo ""

echo "1. Testing CLI import with sample ecommerce API (JSON):"
python cli/levo.py import --spec test-inputs/sample_ecommerce_api.json --application ecommerce --service orders

echo ""
echo "2. Testing CLI import with sample ecommerce API v2 (YAML):"
python cli/levo.py import --spec test-inputs/sample_ecommerce_api_v2.yaml --application ecommerce --service catalog --replace

echo ""
echo "3. Testing CLI import with payment service API:"
python cli/levo.py import --spec test-inputs/payment_service_api.json --application payments --service gateway

echo ""
echo "4. List all imported schemas:"
python cli/levo.py list

echo ""
echo "=== CLI Tests Complete ==="
