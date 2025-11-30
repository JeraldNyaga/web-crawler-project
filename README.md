# Books Crawler API

A production-grade web crawler and REST API for scraping and serving book data from [books.toscrape.com](https://books.toscrape.com). Built with FastAPI, Motor (async MongoDB), and APScheduler for change detection.

**Status:** Fully functional ✓ | **Python:** 3.10+ | **Database:** MongoDB

---

## Table of Contents

-   [Overview](#overview)
-   [Features](#features)
-   [Project Structure](#project-structure)
-   [Requirements](#requirements)
-   [Installation](#installation)
-   [Configuration](#configuration)
-   [Quick Start](#quick-start)
-   [Commands](#commands)
-   [API Reference](#api-reference)
-   [Testing](#testing)
-   [Troubleshooting](#troubleshooting)
-   [Contributing](#contributing)
-   [License](#license)

---

## Overview

This project provides a complete solution for:

1. **Web Crawling** — Async scraping of book data with resume capability
2. **Data Storage** — MongoDB for efficient storage and indexing
3. **REST API** — FastAPI endpoints with API key auth and rate limiting
4. **Change Detection** — Automated scheduler to track price/availability updates
5. **Reporting** — JSON and CSV export of changes

### Architecture

```
┌─────────────────┐
│   Web Scraper   │  (crawler/) - Fetches books.toscrape.com
└────────┬────────┘
         │
         ↓
┌─────────────────────┐
│   MongoDB (Motor)   │  (database/) - Async storage
└────────┬────────────┘
         │
    ┌────┴────┐
    ↓         ↓
┌────────┐ ┌──────────────┐
│  API   │ │  Scheduler   │  (api/, scheduler/) - REST & change detection
└────────┘ └──────────────┘
```

---

## Features

-   ✅ **Async Web Scraping** — Concurrent requests with retry logic
-   ✅ **Resume Support** — Track crawl state and resume mid-crawl
-   ✅ **Change Detection** — Automated tracking of price/availability changes
-   ✅ **REST API** — FastAPI with Swagger/ReDoc documentation
-   ✅ **Authentication** — API key-based access control
-   ✅ **Rate Limiting** — Per-key rate limiting with configurable limits
-   ✅ **CORS Support** — Enabled for cross-origin requests
-   ✅ **Health Checks** — DB connectivity and service status monitoring
-   ✅ **Comprehensive Logging** — Structured logging to file and console
-   ✅ **Full Test Suite** — Unit, integration, and verification tests
-   ✅ **Production Ready** — Error handling, validation, graceful shutdown

---

## Project Structure

```
web-crawler-project/
│
├── api/                          # FastAPI REST application
│   ├── main.py                   # App factory, lifespan, middleware
│   ├── routes.py                 # Endpoint handlers (/books, /changes, /health)
│   ├── auth.py                   # API key validation
│   ├── rate_limiter.py           # Per-key rate limiting
│   └── models/                   # Pydantic response models
│       ├── book_response.py
│       ├── book_list_response.py
│       ├── change_response.py
│       ├── change_list_response.py
│       ├── error_response.py
│       └── health_response.py
│
├── database/                     # MongoDB manager
│   └── mongo.py                  # Async MongoDB operations (Motor)
│
├── crawler/                      # Web scraping
│   ├── scraper.py                # BookCrawler class
│   ├── parser.py                 # HTML parsing utilities
│   ├── utils.py                  # Helpers (price extraction, etc.)
│   └── models/
│       ├── book.py               # Book Pydantic model
│       ├── crawl_state.py        # Crawl state tracking
│       └── book_parse_result.py  # Parse results
│
├── scheduler/                    # Change detection & scheduling
│   ├── scheduler.py              # ChangeDetectionScheduler
│   └── change_detector.py        # ChangeDetector (comparison logic)
│
├── config/                       # Settings
│   └── settings.py               # Pydantic BaseSettings (env vars)
│
├── tests/                        # Test suite
│   ├── test_api.py               # API endpoint tests
│   ├── test_crawler.py           # Crawler tests
│   └── test_scheduler.py         # Scheduler tests
│
├── logs/                         # Application logs (generated)
│   └── app.log
│
├── reports/                      # Generated reports
│   ├── test_report.json
│   └── test_report.csv
│
├── main.py                       # CLI entry point (crawl|api|schedule|detect)
├── verify_api.py                 # API verification script
├── verify_crawler.py             # Crawler verification script
├── test_connection.py            # DB connectivity test
├── test_change_detection.py      # Change detection tests
├── test_reports.py               # Report generation test
│
├── .env                          # Environment variables (git-ignored)
├── .gitignore
├── requirements.txt              # Python dependencies
└── README.md                     # This file
```

---

## Requirements

-   **Python 3.10+** (tested on 3.12)
-   **MongoDB 4.0+** (running and accessible)
-   **pip** for package management

### Python Packages

See [`requirements.txt`](requirements.txt) or install directly:

```bash
pip install fastapi uvicorn motor pymongo pydantic loguru httpx pytest \
            apscheduler pytz fastapi-utils pytest-asyncio
```

Key dependencies:

-   **FastAPI** — Web framework
-   **Uvicorn** — ASGI server
-   **Motor** — Async MongoDB driver
-   **Pydantic** — Data validation & settings
-   **APScheduler** — Job scheduling
-   **Loguru** — Logging
-   **HTTPx** — Async HTTP client (scraping & testing)
-   **Pytest** — Testing framework

---

## Installation

1. **Clone repository:**

    ```bash
    git clone https://github.com/JeraldNyaga/web-crawler-project
    cd web-crawler-project
    ```

2. **Create virtual environment:**

    ```bash
    python -m venv .venv
    source .venv/bin/activate  # On Windows: .venv\Scripts\activate
    ```

3. **Install dependencies:**

    ```bash
    pip install -r requirements.txt
    ```

4. **Create `.env` file** (see [Configuration](#configuration)):

    ```bash
    cp .env.example .env  # If provided, or create manually
    ```

5. **Verify setup:**
    ```bash
    python test_connection.py
    ```

---

## Configuration

Settings are loaded from `.env` file using [Pydantic BaseSettings](config/settings.py).

### Required Environment Variables

```env
# MongoDB
MONGODB_URI=mongodb://localhost:27017
MONGODB_DB_NAME=books_crawler

# API
API_SECRET_KEY=your-secret-key-here
API_KEYS=demo-key-123,ws9_M8a89hNcbPfWbywR
API_HOST=0.0.0.0
API_PORT=8000

# Crawler
TARGET_URL=https://books.toscrape.com
CRAWLER_USER_AGENT=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36

# Scheduler
SCHEDULER_ENABLED=true
SCHEDULER_RUN_TIME=02:00
SCHEDULER_TIMEZONE=UTC

# Rate Limiting
RATE_LIMIT_ENABLED=true
RATE_LIMIT_REQUESTS=100
RATE_LIMIT_PERIOD=3600

# Logging
LOG_LEVEL=INFO
LOG_FILE_ENABLED=true
LOG_DIR=logs

# Environment
ENVIRONMENT=development
```

### Optional Variables

```env
CRAWLER_MAX_RETRIES=3
CRAWLER_RETRY_DELAY=2
CRAWLER_TIMEOUT=30
CRAWLER_CONCURRENT_REQUESTS=10
```

All variables have sensible defaults. See [config/settings.py](config/settings.py) for details.

---

## Quick Start

### 1. Start MongoDB

```bash
# Ensure you have created a mongodb atlas account first and update .env accordingly
```

### 2. Verify Setup

```bash
python test_connection.py
```

Expected output:

```
INFO     | ==================================================
INFO     | Web Crawler - Connection Test Suite
INFO     | ==================================================
INFO     |
Testing required packages...
SUCCESS  | ✓ fastapi              - FastAPI web framework
SUCCESS  | ✓ httpx                - Async HTTP client
SUCCESS  | ✓ motor                - Async MongoDB driver
SUCCESS  | ✓ pydantic             - Data validation
SUCCESS  | ✓ apscheduler          - Task scheduler
SUCCESS  | ✓ loguru               - Logging
SUCCESS  | ✓ pytest               - Testing framework
SUCCESS  |
✓ All packages installed correctly!
INFO     |
Testing configuration...
SUCCESS  | ✓ MONGODB_URI configured
SUCCESS  | ✓ API_SECRET_KEY configured
SUCCESS  | ✓ API_KEYS configured
SUCCESS  | ✓ Configuration loaded successfully!
INFO     | Testing MongoDB connection...
INFO     | Connection URI: mongodb+srv://...
SUCCESS  | ✓ MongoDB connection successful!
INFO     | ✓ Database: books_crawler
INFO     | ✓ Existing collections: ['test_connection', 'crawl_state', 'changes', 'books', 'test_verification']
SUCCESS  | ✓ Write test successful! Inserted ID: ...
SUCCESS  | ✓ Read test successful! Document: {'_id': ObjectId('...'), 'test': 'connection', 'status': 'success'}
INFO     | ✓ Test document cleaned up
SUCCESS  | ✓ All MongoDB tests passed!
INFO     |
==================================================
SUCCESS  | ✓ ALL TESTS PASSED!
SUCCESS  |
You're ready to start development!
INFO     |
Next steps:
INFO     | 1. Run crawler: python main.py crawl
INFO     | 2. Start API: python main.py api
INFO     | 3. Run scheduler: python main.py schedule
INFO     | ==================================================
```

### 3. Run Crawler

```bash
python main.py crawl
```

This will:

-   Connect to MongoDB
-   Scrape books.toscrape.com
-   Store books and create indexes
-   Save crawl state (resume-capable)

### 4. Start API Server

In a new terminal:

```bash
python main.py api
```

API will be available at:

-   **Swagger UI:** http://localhost:8000/docs
-   **ReDoc:** http://localhost:8000/redoc
-   **JSON OpenAPI:** http://localhost:8000/openapi.json

### 5. Run Scheduler (Optional)

In another terminal:

```bash
python main.py schedule
```

This runs change detection daily at the configured time (default: 23:15 EAT).

---

## Commands

Use the CLI to run different components:

### Crawl

```bash
python main.py crawl
```

**What it does:**

-   Connects to MongoDB
-   Crawls books.toscrape.com
-   Stores books in `books` collection
-   Creates database indexes
-   Tracks progress in `crawl_state` collection
-   Can resume from last page if interrupted

**Output:**

-   Console logs with progress
-   Books stored in MongoDB
-   Logs written to `logs/app.log`

### API Server

```bash
python main.py api
```

**What it does:**

-   Starts FastAPI server on configured host:port
-   Connects to MongoDB on startup
-   Serves REST endpoints
-   Applies rate limiting to requests
-   Logs to console and file

**Endpoints Available:**

-   `GET /` — API info
-   `GET /health` — Health check (no auth required)
-   `GET /books` — List/search books
-   `GET /books/{book_id}` — Book detail
-   `GET /changes` — Recent changes
-   `GET /docs` — Interactive docs

### Scheduler

```bash
python main.py schedule
```

**What it does:**

-   Starts APScheduler
-   Runs change detection daily at `SCHEDULER_RUN_TIME`
-   Detects price/availability changes
-   Stores changes in `changes` collection
-   Logs results

**Output:**

-   Changes stored in MongoDB
-   Logs to `logs/app.log`

### Detect (Once)

```bash
python main.py detect
```

**What it does:**

-   Runs change detection immediately (testing)
-   Does NOT start scheduler
-   Useful for testing without waiting for scheduled time

---

## API Reference

### Authentication

All endpoints except `/health` require an API key in the `X-API-Key` header:

```bash
curl -H "X-API-Key: demo-key-123" http://localhost:8000/books
```

### Endpoints

#### Health Check (No Auth)

```bash
GET /health
```

**Response (200):**

```json
{
	"status": "healthy",
	"timestamp": "2025-11-26T10:00:00Z",
	"database": "connected",
	"total_books": 1000
}
```

#### API Root

```bash
GET /
```

**Response:**

```json
{
	"name": "Books Crawler API",
	"version": "1.0.0",
	"status": "running",
	"documentation": "/docs",
	"endpoints": {
		"books": "/books",
		"book_detail": "/books/{book_id}",
		"changes": "/changes",
		"health": "/health"
	},
	"authentication": {
		"type": "API Key",
		"header": "X-API-Key"
	},
	"rate_limit": {
		"requests": 100,
		"period": "3600 seconds"
	}
}
```

#### Get Books

```bash
GET /books?category=Fiction&min_price=10&max_price=50&rating=4&sort=price&order=asc&page=1&limit=20
```

**Query Parameters:**

-   `category` (str, optional) — Filter by category
-   `min_price` (float, optional) — Minimum price
-   `max_price` (float, optional) — Maximum price
-   `rating` (int, optional) — Minimum rating (1-5)
-   `sort` (str, optional) — `title`, `price`, `rating`, `num_reviews`
-   `order` (str, optional) — `asc` or `desc`
-   `page` (int, optional) — Page number (default: 1)
-   `limit` (int, optional) — Items per page (default: 20, max: 100)

**Response (200):**

```json
{
	"books": [
		{
			"id": "507f1f77bcf86cd799439011",
			"url": "http://books.toscrape.com/catalogue/...",
			"title": "A Light in the Attic",
			"description": "...",
			"category": "Poetry",
			"price_excl_tax": 51.77,
			"price_incl_tax": 51.77,
			"availability": "In stock",
			"num_reviews": 0,
			"image_url": "...",
			"rating": 3,
			"crawl_timestamp": "2025-11-26T10:00:00Z"
		}
	],
	"total": 1000,
	"page": 1,
	"limit": 20
}
```

#### Get Book Detail

```bash
GET /books/507f1f77bcf86cd799439011
```

**Response (200):**

```json
{
  "id": "507f1f77bcf86cd799439011",
  "url": "...",
  "title": "A Light in the Attic",
  ...
}
```

**Response (404):** Book not found

#### Get Changes

```bash
GET /changes?change_type=price_change&limit=50
```

**Query Parameters:**

-   `change_type` (str, optional) — `price_change`, `availability_change`, `new_book`
-   `limit` (int, optional) — Max results (default: 100, max: 500)

**Response (200):**

```json
{
	"changes": [
		{
			"id": "507f1f77bcf86cd799439012",
			"book_id": "507f1f77bcf86cd799439011",
			"change_type": "price_change",
			"old_value": 51.77,
			"new_value": 45.99,
			"changed_at": "2025-11-26T10:00:00Z",
			"book_title": "A Light in the Attic"
		}
	],
	"total": 42
}
```

### Rate Limiting

All responses include rate limit headers:

```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 87
X-RateLimit-Reset: 1637914800
```

When limit exceeded (429):

```json
{
	"error": "RateLimitError",
	"message": "Rate limit exceeded",
	"detail": "Too many requests"
}
```

### Error Responses

**401 Unauthorized:**

```json
{
	"error": "AuthenticationError",
	"message": "Invalid or missing API key"
}
```

**422 Validation Error:**

```json
{
  "error": "ValidationError",
  "message": "Invalid request parameters",
  "details": [...]
}
```

**500 Internal Server Error:**

```json
{
	"error": "InternalServerError",
	"message": "An unexpected error occurred"
}
```

**503 Service Unavailable:**

```json
{
	"error": "ServiceUnavailable",
	"message": "Database connection not available"
}
```

---

## Testing

### Run All Tests

```bash
pytest -v
```

### Run Specific Test Class

```bash
pytest tests/test_api.py::TestAuthentication -v
pytest tests/test_api.py::TestBooksEndpoint -v
pytest tests/test_crawler.py -v
```

### Run with Coverage

```bash
pytest --cov=api --cov=crawler --cov=scheduler --cov-report=html
```

### Verification Scripts

Before running the full system, use verification scripts:

#### API Verification

```bash
# Terminal 1: Start API
python main.py api

# Terminal 2: Run verification
python verify_api.py
```

Expected output:

```
✓ Health check passed
✓ Root endpoint OK
✓ Authentication required (401 without key)
✓ Authentication with valid key OK
✓ GET /books OK
✓ Filters work
✓ Sorting works
✓ Pagination works
✓ GET /changes OK
✓ Swagger docs accessible

✓ ALL API TESTS PASSED (9/9)
```

#### Crawler Verification

```bash
python verify_crawler.py
```

Expected output:

```
✓ All imports successful
✓ Models working correctly
✓ Utility functions OK
✓ Database connection successful
✓ HTML parser OK
✓ Crawler initialization OK

✓ ALL CHECKS PASSED (6/6)
```

#### Connection Test

```bash
python test_connection.py
```

This tests:

-   MongoDB connectivity
-   Required packages
-   Basic functionality

---

## Data Models

### Book

```python
{
  "id": str,                          # MongoDB ObjectId
  "url": str,                         # Product page URL
  "title": str,                       # Book title
  "description": Optional[str],       # Book description
  "category": str,                    # Category name
  "price_excl_tax": float,           # Price without tax
  "price_incl_tax": float,           # Price with tax
  "availability": str,               # "In stock" or other status
  "num_reviews": int,                # Number of reviews
  "image_url": str,                  # Cover image URL
  "rating": int,                     # 1-5 stars
  "crawl_timestamp": datetime        # When book was crawled
}
```

### Change

```python
{
  "id": str,                         # MongoDB ObjectId
  "book_id": str,                    # Reference to book
  "change_type": str,                # "price_change", "availability_change", "new_book"
  "old_value": Any,                  # Previous value
  "new_value": Any,                  # New value
  "changed_at": datetime,            # Timestamp of change
  "book_title": str                  # Book title (denormalized)
}
```

### CrawlState

```python
{
  "state_type": str,                 # Always "crawler"
  "last_category": Optional[str],    # Last category crawled
  "last_page": int,                  # Last page number
  "last_book_url": Optional[str],    # Last book URL processed
  "total_books_crawled": int,        # Counter
  "started_at": datetime,            # Crawl start time
  "updated_at": datetime,            # Last update time
  "status": str                      # "in_progress", "completed", "failed"
}
```

---

## Troubleshooting

### MongoDB Connection Failed

**Error:**

```
Failed to connect to MongoDB: connection refused
```

**Solutions:**

1. Ensure MongoDB is running:

2. Check `MONGODB_URI` in `.env`:

3. Test connectivity:
    ```bash
    python test_connection.py
    ```

### API Returns 503 Service Unavailable

**Error:**

```
{
  "error": "ServiceUnavailable",
  "message": "Database connection not available"
}
```

**Solutions:**

1. Check `/health` endpoint:

    ```bash
    curl http://localhost:8000/health
    ```

2. Check logs:

3. Ensure DB connection started:
    - API should log `Connected to MongoDB` on startup

### API Returns 401 Unauthorized

**Error:**

```
{
  "error": "AuthenticationError",
  "message": "Invalid or missing API key"
}
```

**Solutions:**

1. Ensure `X-API-Key` header is set:

    ```bash
    curl -H "X-API-Key: demo-key-123" http://localhost:8000/books
    ```

2. Check API key is in `API_KEYS` in `.env`:
    ```bash
    API_KEYS=demo-key-123,ws9_M8a89hNcbPfWbywR
    ```

### Rate Limit Exceeded (429)

**Error:**

```
{
  "error": "RateLimitError",
  "message": "Rate limit exceeded"
}
```

**Solutions:**

1. Check rate limit settings in `.env`:

    ```bash
    RATE_LIMIT_REQUESTS=100
    RATE_LIMIT_PERIOD=3600  # seconds
    ```

2. Wait for rate limit window to reset (see `X-RateLimit-Reset` header)

3. Use a different API key if available

### Crawler Hangs or Is Slow

**Solutions:**

1. Increase concurrent requests:

    ```bash
    CRAWLER_CONCURRENT_REQUESTS=20
    ```

2. Reduce timeout:

    ```bash
    CRAWLER_TIMEOUT=15
    ```

3. Check network connectivity:
    ```bash
    curl https://books.toscrape.com
    ```

### Tests Fail with Database Errors

**Error:**

```
'NoneType' object has no attribute 'books'
```

**Solutions:**

1. Ensure MongoDB is running

2. Check `.env` has `MONGODB_URI`

3. Run individual test:

    ```bash
    pytest tests/test_api.py::TestHealthEndpoint -v -s
    ```

4. Check logs for detailed error:
    ```bash
    tail -f logs/app.log
    ```

---

## Development Workflow

### 1. Make Changes

Edit code in `api/`, `crawler/`, or `scheduler/` directories.

### 2. Test Locally

```bash
# Run relevant tests
pytest tests/test_api.py -v

# Or run verification script
python verify_api.py
```

### 3. Check Logs

```bash
tail -f logs/app.log
```

### 4. Commit & Push

```bash
git add .
git commit -m "Descriptive message"
git push origin feature-branch
```

---

### Prerequisites

-   MongoDB hosted and accessible
-   Python 3.10+ installed on server
-   `.env` file with production settings

### Steps

1. **Clone repository:**

    ```bash
    git clone <repo-url> /opt/web-crawler-project
    cd /opt/web-crawler-project
    ```

2. **Install dependencies:**

    ```bash
    python -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
    ```

3. **Configure `.env`:**

    ```bash
    # Use production settings
    ENVIRONMENT=production
    API_HOST=0.0.0.0
    API_PORT=8000
    LOG_LEVEL=WARNING
    # ... other vars
    ```

4. **Run with Gunicorn (recommended):**

    ```bash
    gunicorn -w 4 -k uvicorn.workers.UvicornWorker \
             --bind 0.0.0.0:8000 \
             api.main:app
    ```

---

## Contributing

### Code Style

-   Follow PEP 8
-   Use type hints
-   Add docstrings to functions
-   Max line length: 100

### Adding Features

1. Create feature branch: `git checkout -b feature/name`
2. Add tests for new functionality
3. Update README if needed
4. Run full test suite: `pytest`
5. Open PR with description

### Reporting Bugs

Include:

-   Error message and traceback
-   Steps to reproduce
-   Environment (Python version, OS, MongoDB version)
-   Relevant logs

---

## Performance Tuning

### MongoDB Indexes

The application automatically creates indexes on:

-   `books.url` (unique)
-   `books.category`
-   `books.price_incl_tax`
-   `books.rating`
-   `books.crawl_timestamp`
-   `books.content_hash`
-   `changes.book_id`

### Crawler Performance

```env
# Parallel requests
CRAWLER_CONCURRENT_REQUESTS=20

# Connection timeout
CRAWLER_TIMEOUT=30

# Retry policy
CRAWLER_MAX_RETRIES=3
CRAWLER_RETRY_DELAY=2
```

### API Rate Limiting

```env
# Per API key
RATE_LIMIT_REQUESTS=100
RATE_LIMIT_PERIOD=3600  # 1 hour
```

---

## Monitoring & Logs

### Log Locations

-   **Console:** Real-time during execution
-   **File:** `logs/app.log` (configured in `config/settings.py`)

### Log Levels

```env
LOG_LEVEL=DEBUG    # Verbose (development)
LOG_LEVEL=INFO     # Standard (default)
LOG_LEVEL=WARNING  # Warnings only (production)
LOG_LEVEL=ERROR    # Errors only
```

### Health Monitoring

```bash
# Check API health
curl http://localhost:8000/health

# Monitor logs
tail -f logs/app.log

# Check MongoDB
mongo --eval "db.adminCommand('ping')"
```

---

## License

### MIT License

Copyright (c) 2025 Jerald Nyaga

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
