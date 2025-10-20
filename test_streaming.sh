#!/bin/bash

# Test script for streaming progress updates
# Usage: ./test_streaming.sh

echo "🚀 Starting analysis task..."

# Submit the analysis task
RESPONSE=$(curl -s -X POST -H "Content-Type: application/json" \
  -d '{"question":"What is the total revenue in the TSV file?","filename":"test-sales.tsv"}' \
  http://localhost:5001/analyze)

# Extract task ID
TASK_ID=$(echo $RESPONSE | grep -o '"task_id":"[^"]*"' | cut -d'"' -f4)

if [ -z "$TASK_ID" ]; then
  echo "❌ Failed to get task ID"
  echo "Response: $RESPONSE"
  exit 1
fi

echo "✅ Task submitted: $TASK_ID"
echo ""
echo "📊 Streaming progress updates (press Ctrl+C to stop):"
echo "=================================================="
echo ""

# Stream progress updates using Server-Sent Events
curl -N http://localhost:5001/status/$TASK_ID/stream

echo ""
echo "=================================================="
echo "✅ Task complete!"
