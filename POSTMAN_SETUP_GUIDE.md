# Postman Setup Guide

## Quick Start

### 1. Import Collection and Environment

1. **Open Postman**
2. **Import Collection**:
   - Click "Import" button
   - Select `postman_collection.json`
   - Collection will be imported with all endpoints

3. **Import Environment**:
   - Click "Import" button
   - Select `postman_environment.json`
   - Environment will be imported with all variables

4. **Select Environment**:
   - Click the environment dropdown (top right)
   - Select "Recommender System Environment"

### 2. Start the API Server

```bash
# Make sure Redis is running
redis-server

# Start the API (in another terminal)
source venv/bin/activate
python run_api.py
```

### 3. Test the API

1. **Health Check**:
   - Run "Health Check" request
   - Should return `{"status": "healthy", "redis_connected": true}`

2. **Popular Items**:
   - Run "Get Popular Items" request
   - Should return top items with purchase frequencies

3. **Similar Items**:
   - Run "Get Similar Items" request
   - Should return items frequently co-purchased with PID

4. **Basket Recommendations**:
   - Run "Get Basket Recommendations" request
   - Should return recommendations for the basket

## Collection Structure

### 📁 Health & Status
- **Health Check**: Service and Redis status
- **Root Endpoint**: Basic API information

### 📁 Recommendations
- **Get Popular Items**: Most frequently purchased items
- **Get Similar Items**: Items frequently co-purchased together
- **Get Basket Recommendations**: Real-time basket suggestions
- **Get Order Recommendations**: Recommendations for specific orders

### 📁 Test Scenarios
- **Predefined test cases** with different parameters
- **Edge case testing** with various limits
- **Real-world scenarios** with actual item combinations

### 📁 Error Testing
- **Invalid inputs** to test error handling
- **Edge cases** like empty baskets
- **Validation errors** for parameter limits

## Environment Variables

### Base Configuration
- `base_url`: API base URL (default: http://localhost:8000)
- `api_version`: API version (v1)

### Default Limits
- `popular_limit`: Default limit for popular items (10)
- `similar_limit`: Default limit for similar items (5)
- `basket_limit`: Default limit for basket recommendations (10)
- `order_limit`: Default limit for order recommendations (10)

### Test Data
- `item_name`: Default item for testing (PID)
- `item_name_2`: Second item (Water Level Meter)
- `item_name_3`: Third item (Cal Kit)
- `order_id`: Default order ID (12345)
- `basket_item_1`, `basket_item_2`: Default basket items

### Performance Testing
- `timeout_ms`: Request timeout (5000ms)
- `expected_response_time_ms`: Expected response time (100ms)

## Automated Testing

### Pre-request Scripts
- **Auto-setup**: Sets default values if not configured
- **Environment validation**: Ensures all required variables are set

### Test Scripts
- **Response time**: Validates response time < 1000ms
- **Status codes**: Ensures successful responses (200/201)
- **Content-Type**: Validates JSON responses
- **Response structure**: Validates recommendation format
- **Data validation**: Checks similarity scores and required fields

### Running Tests

1. **Individual Tests**:
   - Click "Send" on any request
   - Tests run automatically
   - Check "Test Results" tab

2. **Collection Tests**:
   - Right-click collection
   - Select "Run collection"
   - Choose environment
   - Click "Run"

3. **Newman CLI** (Optional):
   ```bash
   # Install Newman
   npm install -g newman
   
   # Run collection
   newman run postman_collection.json -e postman_environment.json
   ```

## Test Scenarios

### 1. Basic Functionality Tests
- ✅ Health check returns healthy status
- ✅ Popular items returns top items
- ✅ Similar items returns co-purchased items
- ✅ Basket recommendations work with multiple items

### 2. Parameter Validation Tests
- ✅ Limit parameters are respected
- ✅ Invalid limits are handled gracefully
- ✅ Empty requests return appropriate errors
- ✅ Malformed JSON is handled

### 3. Performance Tests
- ✅ Response times < 100ms
- ✅ Concurrent requests handled
- ✅ Large result sets processed
- ✅ Memory usage stable

### 4. Error Handling Tests
- ✅ Non-existent items return empty results
- ✅ Invalid parameters return 422 errors
- ✅ Server errors return 500 status
- ✅ Network errors handled gracefully

## Customization

### Adding New Tests
1. **Create new request** in appropriate folder
2. **Add test scripts** in "Tests" tab:
   ```javascript
   pm.test("Custom test", function () {
       // Your test logic here
   });
   ```

### Modifying Environment
1. **Edit environment variables** in Postman
2. **Add new variables** as needed
3. **Export updated environment** for sharing

### Creating New Scenarios
1. **Duplicate existing request**
2. **Modify parameters** as needed
3. **Add to appropriate folder**
4. **Update test scripts** if needed

## Troubleshooting

### Common Issues

1. **Connection Refused**:
   - Check if API server is running
   - Verify `base_url` in environment
   - Check port 8000 is available

2. **Redis Connection Failed**:
   - Ensure Redis server is running
   - Check Redis connection in health endpoint
   - Verify Redis data is loaded

3. **Empty Results**:
   - Check if data processing completed
   - Verify Redis has data loaded
   - Check item names are correct

4. **Test Failures**:
   - Review test scripts in "Tests" tab
   - Check response format matches expectations
   - Verify environment variables are set

### Debug Steps

1. **Check Health**:
   ```bash
   curl "http://localhost:8000/health/"
   ```

2. **Verify Redis**:
   ```bash
   redis-cli ping
   redis-cli dbsize
   ```

3. **Test API Directly**:
   ```bash
   curl "http://localhost:8000/api/v1/popular-items?limit=3"
   ```

4. **Check Logs**:
   - Review API server logs
   - Check Redis logs
   - Review Postman console

## Best Practices

### Testing Strategy
1. **Start with health check** to verify connectivity
2. **Test basic endpoints** before complex scenarios
3. **Use test scenarios** for comprehensive testing
4. **Run error tests** to verify error handling
5. **Monitor performance** with response time tests

### Environment Management
1. **Use separate environments** for dev/staging/prod
2. **Keep sensitive data** in environment variables
3. **Export environments** for team sharing
4. **Version control** environment files

### Collection Maintenance
1. **Keep tests updated** with API changes
2. **Add new test cases** for new features
3. **Remove obsolete tests** when endpoints change
4. **Document test purposes** in descriptions

## Integration with CI/CD

### Newman Integration
```bash
# Install Newman
npm install -g newman

# Run tests in CI pipeline
newman run postman_collection.json \
  -e postman_environment.json \
  --reporters cli,json \
  --reporter-json-export results.json
```

### GitHub Actions Example
```yaml
name: API Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Setup Node.js
        uses: actions/setup-node@v2
        with:
          node-version: '16'
      - name: Install Newman
        run: npm install -g newman
      - name: Run API Tests
        run: newman run postman_collection.json -e postman_environment.json
```

## Support

For issues with the Postman collection:
1. Check this setup guide
2. Review API documentation
3. Verify server and Redis are running
4. Check Postman console for errors
5. Test API endpoints directly with curl
