#!/bin/bash
# Multi-Format File Support - Quick Test Script
# Run this after successfully building the updated container

set -e

echo "🧪 Multi-Format File Support Test Suite"
echo "========================================"
echo ""

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Helper function to wait for task completion
wait_for_task() {
    local task_id=$1
    local max_wait=${2:-60}
    local waited=0
    
    echo -n "Waiting for task completion"
    while [ $waited -lt $max_wait ]; do
        status=$(curl -s http://localhost:5001/status/$task_id | jq -r '.status // "pending"')
        if [ "$status" == "completed" ] || [ "$status" == "failed" ]; then
            echo ""
            return 0
        fi
        echo -n "."
        sleep 3
        waited=$((waited + 3))
    done
    echo ""
    echo "${RED}⏱ Timeout waiting for task${NC}"
    return 1
}

# Check prerequisites
echo "${BLUE}📋 Checking prerequisites...${NC}"
if ! curl -s http://localhost:5001/status/health > /dev/null 2>&1; then
    echo "${RED}❌ API not responding. Please start services:${NC}"
    echo "   podman-compose up -d"
    exit 1
fi
echo "${GREEN}✅ API is healthy${NC}"
echo ""

# List available files
echo "${BLUE}📁 Available data files:${NC}"
curl -s http://localhost:5001/data | jq -r '.files[] | "  - \(.filename) (\(.file_type // "unknown")) - \(.size_human)"' || true
echo ""

# Test 1: CSV (Baseline)
echo "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo "${BLUE}Test 1: CSV File (Baseline - Backward Compatibility)${NC}"
echo "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
TASK_ID=$(curl -s -X POST -H "Content-Type: application/json" \
  -d '{"question":"What is the median Avg_Price?","filename":"sales-data.csv"}' \
  http://localhost:5001/analyze | jq -r '.task_id')
echo "Task ID: $TASK_ID"
if wait_for_task "$TASK_ID" 60; then
    result=$(curl -s http://localhost:5001/status/$TASK_ID | jq '.')
    status=$(echo "$result" | jq -r '.status')
    if [ "$status" == "completed" ]; then
        echo "${GREEN}✅ CSV Test PASSED${NC}"
        echo "$result" | jq -r '.answer' | head -20
    else
        echo "${RED}❌ CSV Test FAILED${NC}"
        echo "$result" | jq -r '.error // .answer' | head -20
    fi
fi
echo ""

# Test 2: TSV File
if curl -s http://localhost:5001/data | jq -e '.files[] | select(.filename=="test-sales.tsv")' > /dev/null; then
    echo "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo "${BLUE}Test 2: TSV File (Tab-Separated Values)${NC}"
    echo "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    TASK_ID=$(curl -s -X POST -H "Content-Type: application/json" \
      -d '{"question":"What is the average Avg_Price?","filename":"test-sales.tsv"}' \
      http://localhost:5001/analyze | jq -r '.task_id')
    echo "Task ID: $TASK_ID"
    if wait_for_task "$TASK_ID" 60; then
        result=$(curl -s http://localhost:5001/status/$TASK_ID | jq '.')
        status=$(echo "$result" | jq -r '.status')
        if [ "$status" == "completed" ]; then
            echo "${GREEN}✅ TSV Test PASSED${NC}"
            echo "$result" | jq -r '.answer' | head -20
        else
            echo "${RED}❌ TSV Test FAILED${NC}"
            echo "$result" | jq -r '.error // .answer' | head -20
        fi
    fi
    echo ""
else
    echo "${YELLOW}⏭ Skipping TSV test (test-sales.tsv not found)${NC}"
    echo ""
fi

# Test 3: JSON File
if curl -s http://localhost:5001/data | jq -e '.files[] | select(.filename=="test-sales.json")' > /dev/null; then
    echo "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo "${BLUE}Test 3: JSON File (Array Format)${NC}"
    echo "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    TASK_ID=$(curl -s -X POST -H "Content-Type: application/json" \
      -d '{"question":"How many events are in the JSON file and what is the total revenue?","filename":"test-sales.json"}' \
      http://localhost:5001/analyze | jq -r '.task_id')
    echo "Task ID: $TASK_ID"
    if wait_for_task "$TASK_ID" 60; then
        result=$(curl -s http://localhost:5001/status/$TASK_ID | jq '.')
        status=$(echo "$result" | jq -r '.status')
        if [ "$status" == "completed" ]; then
            echo "${GREEN}✅ JSON Test PASSED${NC}"
            echo "$result" | jq -r '.answer' | head -20
        else
            echo "${RED}❌ JSON Test FAILED${NC}"
            echo "$result" | jq -r '.error // .answer' | head -20
        fi
    fi
    echo ""
else
    echo "${YELLOW}⏭ Skipping JSON test (test-sales.json not found)${NC}"
    echo ""
fi

# Test 4: Excel File
if curl -s http://localhost:5001/data | jq -e '.files[] | select(.filename=="test-sales.xlsx")' > /dev/null; then
    echo "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo "${BLUE}Test 4: Excel File (.xlsx)${NC}"
    echo "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    TASK_ID=$(curl -s -X POST -H "Content-Type: application/json" \
      -d '{"question":"What is the total revenue in the Excel file?","filename":"test-sales.xlsx"}' \
      http://localhost:5001/analyze | jq -r '.task_id')
    echo "Task ID: $TASK_ID"
    if wait_for_task "$TASK_ID" 60; then
        result=$(curl -s http://localhost:5001/status/$TASK_ID | jq '.')
        status=$(echo "$result" | jq -r '.status')
        if [ "$status" == "completed" ]; then
            echo "${GREEN}✅ Excel Test PASSED${NC}"
            echo "$result" | jq -r '.answer' | head -20
        else
            echo "${RED}❌ Excel Test FAILED${NC}"
            echo "$result" | jq -r '.error // .answer' | head -20
        fi
    fi
    echo ""
else
    echo "${YELLOW}⏭ Skipping Excel test (test-sales.xlsx not found)${NC}"
    echo ""
fi

# Test 5: Mixed Format Analysis
echo "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo "${BLUE}Test 5: Mixed Format Analysis${NC}"
echo "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
file_count=$(curl -s http://localhost:5001/data | jq '.count')
echo "Analyzing $file_count files of different formats..."
TASK_ID=$(curl -s -X POST -H "Content-Type: application/json" \
  -d '{"question":"What is the total attendance across ALL data files? List the file types you analyzed."}' \
  http://localhost:5001/analyze | jq -r '.task_id')
echo "Task ID: $TASK_ID"
if wait_for_task "$TASK_ID" 90; then
    result=$(curl -s http://localhost:5001/status/$TASK_ID | jq '.')
    status=$(echo "$result" | jq -r '.status')
    if [ "$status" == "completed" ]; then
        echo "${GREEN}✅ Mixed Format Test PASSED${NC}"
        echo "$result" | jq -r '.answer' | head -30
    else
        echo "${RED}❌ Mixed Format Test FAILED${NC}"
        echo "$result" | jq -r '.error // .answer' | head -30
    fi
fi
echo ""

# Test 6: Natural Language + New Format
if curl -s http://localhost:5001/data | jq -e '.files[] | select(.filename=="test-sales.json")' > /dev/null; then
    echo "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo "${BLUE}Test 6: Natural Language + JSON (Combined Features)${NC}"
    echo "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    TASK_ID=$(curl -s -X POST -H "Content-Type: application/json" \
      -d '{"question":"What was the average price at all events? (Note: I do not know the exact column name)","filename":"test-sales.json"}' \
      http://localhost:5001/analyze | jq -r '.task_id')
    echo "Task ID: $TASK_ID"
    if wait_for_task "$TASK_ID" 60; then
        result=$(curl -s http://localhost:5001/status/$TASK_ID | jq '.')
        status=$(echo "$result" | jq -r '.status')
        if [ "$status" == "completed" ]; then
            echo "${GREEN}✅ Natural Language + JSON Test PASSED${NC}"
            echo "$result" | jq -r '.answer' | head -20
        else
            echo "${RED}❌ Natural Language + JSON Test FAILED${NC}"
            echo "$result" | jq -r '.error // .answer' | head -20
        fi
    fi
    echo ""
fi

# Summary
echo "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo "${BLUE}📊 Test Suite Complete${NC}"
echo "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo "Review the results above to verify:"
echo "  ✓ CSV files still work (backward compatibility)"
echo "  ✓ TSV files load automatically"
echo "  ✓ JSON files load automatically"
echo "  ✓ Excel files load automatically"
echo "  ✓ Mixed format analysis works"
echo "  ✓ Natural language works with all formats"
echo ""
echo "${GREEN}For detailed test plan, see: TEST-MULTI-FORMAT.md${NC}"
