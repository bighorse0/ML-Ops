# Feature Store Test Suite

This directory contains comprehensive tests for the Feature Store as a Service platform. The test suite covers all aspects of the system including API endpoints, business logic, data models, authentication, and integration scenarios.

## 📁 Test Structure

```
tests/
├── conftest.py              # Test configuration and fixtures
├── test_features.py         # Feature management tests
├── test_monitoring.py       # Monitoring and alerting tests
├── test_computation.py      # Computation and pipeline tests
├── test_lineage.py          # Data lineage tests
├── test_users.py            # User management tests
├── test_organizations.py    # Organization management tests
└── README.md               # This file
```

## 🧪 Test Types

### 1. Unit Tests (`@pytest.mark.unit`)
- Test individual functions and methods in isolation
- Mock external dependencies
- Fast execution (< 1 second per test)
- High code coverage

### 2. Integration Tests (`@pytest.mark.integration`)
- Test interactions between components
- Use test database and external services
- Validate data flow and business logic
- Medium execution time (1-10 seconds per test)

### 3. API Tests (`@pytest.mark.api`)
- Test HTTP endpoints and request/response handling
- Validate API contracts and schemas
- Test authentication and authorization
- End-to-end API functionality

### 4. Performance Tests (`@pytest.mark.slow`)
- Test system performance under load
- Validate response times and throughput
- Stress testing and capacity planning
- Longer execution time (> 10 seconds per test)

## 🚀 Running Tests

### Quick Start
```bash
# Run all tests
python run_tests.py

# Run with verbose output
python run_tests.py --verbose

# Run specific test types
python run_tests.py --unit
python run_tests.py --integration
python run_tests.py --api
```

### Advanced Usage
```bash
# Run specific test files
python run_tests.py --test tests/test_features.py

# Run tests with specific markers
python run_tests.py --marker validation

# Generate coverage report
python run_tests.py --coverage

# Generate comprehensive test report
python run_tests.py --report

# List all available tests
python run_tests.py --list
```

### Direct pytest Commands
```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_features.py

# Run tests with marker
pytest -m unit

# Run with coverage
pytest --cov=api --cov=services --cov=models --cov=utils

# Run specific test function
pytest tests/test_features.py::TestFeaturesAPI::test_create_feature_success
```

## 📊 Test Coverage

The test suite aims for comprehensive coverage across all components:

- **API Layer**: 95%+ coverage
- **Business Logic**: 90%+ coverage
- **Data Models**: 85%+ coverage
- **Authentication**: 95%+ coverage
- **Integration**: 80%+ coverage

### Coverage Reports
```bash
# Generate HTML coverage report
pytest --cov=api --cov=services --cov=models --cov=utils --cov-report=html

# Generate XML coverage report (for CI/CD)
pytest --cov=api --cov=services --cov=models --cov=utils --cov-report=xml
```

## 🔧 Test Configuration

### Environment Variables
Tests use the following environment variables (set in `pytest.ini`):

```ini
TESTING = true
DATABASE_URL = sqlite+aiosqlite:///:memory:
REDIS_URL = redis://localhost:6379/1
KAFKA_BOOTSTRAP_SERVERS = localhost:9092
SECRET_KEY = test-secret-key-for-testing-only
```

### Test Database
- Uses SQLite in-memory database for fast execution
- Each test gets a clean database state
- Automatic cleanup after each test

### Test Data
Sample data is defined in `conftest.py` fixtures:

```python
@pytest.fixture
def sample_feature_data():
    return {
        "name": "test_feature",
        "description": "Test feature for testing",
        "data_type": "float",
        "feature_type": "numeric",
        "entity_type": "user",
        "serving_mode": "online",
        "storage_type": "postgresql",
        "tags": ["test", "feature"],
        "metadata": {"test": True}
    }
```

## 🏗️ Test Fixtures

### Database Fixtures
```python
@pytest.fixture
async def db_session():
    """Provide database session for tests."""
    
@pytest.fixture
async def test_organization(db_session):
    """Create test organization."""
    
@pytest.fixture
async def test_user(db_session, test_organization):
    """Create test user."""
```

### Authentication Fixtures
```python
@pytest.fixture
def auth_headers(test_user):
    """Provide authentication headers."""
    
@pytest.fixture
def readonly_auth_headers(test_user_readonly):
    """Provide readonly user authentication headers."""
```

### Sample Data Fixtures
```python
@pytest.fixture
def sample_feature_data():
    """Sample feature data for testing."""
    
@pytest.fixture
def sample_user_data():
    """Sample user data for testing."""
```

## 📝 Writing Tests

### Test Structure
```python
class TestFeatureAPI:
    """Test suite for Feature API endpoints."""
    
    def test_create_feature_success(self, client, auth_headers, sample_feature_data):
        """Test successful feature creation."""
        response = client.post("/api/features", json=sample_feature_data, headers=auth_headers)
        
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == sample_feature_data["name"]
```

### Test Categories

#### 1. Success Tests
- Test normal operation with valid data
- Verify correct response format and status codes
- Check data persistence and retrieval

#### 2. Validation Tests
- Test input validation and error handling
- Verify appropriate error messages
- Test edge cases and boundary conditions

#### 3. Authorization Tests
- Test access control and permissions
- Verify role-based access
- Test unauthorized access scenarios

#### 4. Integration Tests
- Test component interactions
- Verify data flow between services
- Test external service integrations

### Best Practices

#### 1. Test Naming
```python
def test_create_feature_success(self, ...):
def test_create_feature_validation_error(self, ...):
def test_create_feature_duplicate_name(self, ...):
def test_get_feature_not_found(self, ...):
```

#### 2. Test Organization
```python
class TestFeatureAPI:
    """Test suite for Feature API endpoints."""
    
class TestFeatureValidation:
    """Test suite for feature data validation."""
    
class TestFeatureSearchAndFiltering:
    """Test suite for feature search and filtering."""
```

#### 3. Assertions
```python
# Status code assertions
assert response.status_code == 201

# Data assertions
assert data["name"] == expected_name
assert "id" in data
assert "created_at" in data

# Error assertions
assert "detail" in data
assert "not found" in data["detail"]
```

#### 4. Test Data
```python
# Use fixtures for reusable data
def test_create_feature(self, client, auth_headers, sample_feature_data):
    response = client.post("/api/features", json=sample_feature_data, headers=auth_headers)

# Modify data for specific test cases
def test_create_feature_with_custom_data(self, client, auth_headers, sample_feature_data):
    custom_data = sample_feature_data.copy()
    custom_data["name"] = "custom_feature"
    response = client.post("/api/features", json=custom_data, headers=auth_headers)
```

## 🔍 Test Debugging

### Running Single Tests
```bash
# Run specific test function
pytest tests/test_features.py::TestFeaturesAPI::test_create_feature_success -v

# Run with print statements
pytest tests/test_features.py::TestFeaturesAPI::test_create_feature_success -s

# Run with debugger
pytest tests/test_features.py::TestFeaturesAPI::test_create_feature_success --pdb
```

### Debugging Tips
1. Use `-s` flag to see print statements
2. Use `--pdb` for interactive debugging
3. Use `-v` for verbose output
4. Use `--tb=short` for shorter tracebacks
5. Use `--maxfail=1` to stop on first failure

## 📈 Performance Testing

### Load Testing
```python
@pytest.mark.slow
def test_feature_serving_performance(self, client, auth_headers):
    """Test feature serving performance under load."""
    # Test with multiple concurrent requests
    # Verify response times < 1ms p99
```

### Stress Testing
```python
@pytest.mark.slow
def test_feature_creation_stress(self, client, auth_headers):
    """Test feature creation under stress."""
    # Create many features concurrently
    # Verify system stability
```

## 🔒 Security Testing

### Authentication Tests
```python
def test_unauthorized_access(self, client):
    """Test unauthorized access to protected endpoints."""
    response = client.get("/api/features")
    assert response.status_code == 401
```

### Authorization Tests
```python
def test_permission_checks(self, client, readonly_auth_headers):
    """Test role-based permission checks."""
    # Test readonly user cannot create resources
    response = client.post("/api/features", json=data, headers=readonly_auth_headers)
    assert response.status_code == 403
```

## 🚨 Continuous Integration

### GitHub Actions
Tests are automatically run on:
- Pull requests
- Push to main branch
- Scheduled runs

### Test Reports
- JUnit XML reports for CI integration
- HTML reports for human review
- Coverage reports for quality metrics

### Quality Gates
- Minimum 80% code coverage
- All tests must pass
- No critical security vulnerabilities
- Performance benchmarks met

## 📚 Additional Resources

### Documentation
- [pytest Documentation](https://docs.pytest.org/)
- [FastAPI Testing](https://fastapi.tiangolo.com/tutorial/testing/)
- [SQLAlchemy Testing](https://docs.sqlalchemy.org/en/14/orm/session_transaction.html#joining-a-session-into-an-external-transaction-such-as-for-test-suites)

### Tools
- [pytest-cov](https://pytest-cov.readthedocs.io/) - Coverage reporting
- [pytest-asyncio](https://pytest-asyncio.readthedocs.io/) - Async test support
- [pytest-html](https://pytest-html.readthedocs.io/) - HTML test reports

### Best Practices
- [Testing Best Practices](https://realpython.com/python-testing/)
- [API Testing Guide](https://realpython.com/api-testing-with-python/)
- [Database Testing](https://realpython.com/testing-third-party-apis-with-mocks/) 