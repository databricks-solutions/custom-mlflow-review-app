#!/bin/bash
# Test script for trace modal functionality

echo "Testing Trace Modal Functionality"
echo "================================="

# 1. Get a trace ID from search results
echo "1. Getting trace ID from search results..."
TRACE_ID=$(curl -s -X POST http://localhost:8000/api/mlflow/search-traces \
  -H "Content-Type: application/json" \
  -d '{"experiment_ids": ["2178582188830602"], "max_results": 1}' | jq -r '.traces[0].info.trace_id')

echo "   Found trace ID: $TRACE_ID"

# 2. Test the trace endpoint
echo -e "\n2. Testing GET /api/mlflow/traces/{trace_id}..."
RESPONSE=$(curl -s -w "\n%{http_code}" http://localhost:8000/api/mlflow/traces/$TRACE_ID)
HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
BODY=$(echo "$RESPONSE" | head -n-1)

if [ "$HTTP_CODE" = "200" ]; then
    echo "   ✅ Success! HTTP $HTTP_CODE"
    
    # Extract some key info
    STATE=$(echo "$BODY" | jq -r '.info.state')
    SPANS_COUNT=$(echo "$BODY" | jq '.data.spans | length')
    EXPERIMENT_ID=$(echo "$BODY" | jq -r '.info.trace_location.experiment_id')
    
    echo "   - State: $STATE"
    echo "   - Spans: $SPANS_COUNT"
    echo "   - Experiment: $EXPERIMENT_ID"
else
    echo "   ❌ Failed! HTTP $HTTP_CODE"
    echo "$BODY" | jq '.'
fi

# 3. Test with multiple traces
echo -e "\n3. Testing multiple traces..."
curl -s -X POST http://localhost:8000/api/mlflow/search-traces \
  -H "Content-Type: application/json" \
  -d '{"experiment_ids": ["2178582188830602"], "max_results": 3}' | \
  jq -r '.traces[].info.trace_id' | \
  while read trace_id; do
    STATUS_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/api/mlflow/traces/$trace_id)
    echo "   - Trace $trace_id: HTTP $STATUS_CODE"
  done

echo -e "\n✅ Trace modal endpoint testing complete!"