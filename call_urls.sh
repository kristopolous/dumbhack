#!/bin/bash

BASE_URL="http://localhost:5000"
URL_TO_SCRAPE="https://example.com"

# Scrape URL
echo "Scraping URL..."
curl -X POST -H "Content-Type: application/json" -d "{\"url\": \"$URL_TO_SCRAPE\"}" "$BASE_URL/scrape"

echo ""

# Call
echo "Calling..."
curl -X POST -H "Content-Type: application/json" -d "{\"url\": \"$URL_TO_SCRAPE\", \"personas\": [\"persona1\", \"persona2\"]}" "$BASE_URL/call"

echo ""

# Add to Call
echo "Adding to call..."
curl -X POST -H "Content-Type: application/json" -d '{"id": "12345", "persona": "persona3"}' "$BASE_URL/add_to_call"

echo ""

# Remove from Call
echo "Removing from call..."
curl -X POST -H "Content-Type: application/json" -d '{"id": "12345", "persona": "persona3"}' "$BASE_URL/remove_from_call"