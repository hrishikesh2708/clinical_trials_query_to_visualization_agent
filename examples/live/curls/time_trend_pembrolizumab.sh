curl -s -X POST http://127.0.0.1:8000/api/v1/visualize \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Trials per year for pembrolizumab since 2015",
    "drug_name": "Pembrolizumab",
    "start_year": 2015
  }'
