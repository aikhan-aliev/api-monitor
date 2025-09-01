# API Monitoring Service

**A lightweight, asynchronous API monitoring tool built with Python, FastAPI, APScheduler, and SQLite.**  

This project monitors the availability, performance, and latency of web APIs in real-time, providing dynamic target management and persistent storage for reliable results.

---

## Features

- **Dynamic Target Management:** Add, list, and remove APIs at runtime via RESTful endpoints.  
- **Asynchronous HTTP Checks:** Efficiently performs concurrent requests using Python’s `asyncio` and `httpx`.  
- **Scheduler Integration:** Uses APScheduler to run periodic checks for each target automatically.  
- **Persistent Storage:** Stores targets and check results in SQLite, ensuring data survives server restarts.  
- **Real-Time Status Reporting:** Provides last check results, HTTP status codes, latency, and error messages.  
- **Extensible Architecture:** Modular design allows easy addition of alerts, metrics, or AI-driven features.

---

## How it Works

1. **Startup**: Initializes the database, seeds a demo target, and starts the scheduler.  
2. **Scheduler**: Periodically runs asynchronous HTTP checks on each target.  
3. **Check Logic**: Measures latency, verifies HTTP status codes, handles retries with exponential backoff, and stores results in SQLite.  
4. **Results**: Last check results are accessible via `/status`.

---

## Usage

- **View all targets:** `GET /targets`  
- **Add a new target:** `POST /targets`  
- **Delete a target:** `DELETE /targets/{id}`  
- **Check last status:** `GET /status` or `GET /status?target_id=<id>`  

  "severity": "LOW"
}
