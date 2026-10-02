# OpenAPI-Compliant Model Inference Service with Nginx and Python

A contract-first machine learning inference service built with Python (FastAPI), secured behind an Nginx reverse proxy, and containerized with Docker Compose to enforce absolute network isolation.

---

## Architecture Overview

```text
                  +-------------------------------------------------------+
                  |               Host / Public Network                   |
                  |                                                       |
                  |   External Client (curl / browser / microservice)     |
                  +--------------------------+----------------------------+
                                             |
                                  HTTP Port 8080 (Published)
                                             v
+-------------------------------------------------------------------------+
| Docker Internal Network (Isolated)                                      |
|                                                                         |
|   +-----------------------------------------------------------------+   |
|   |                       Nginx Reverse Proxy                       |   |
|   |   - Enforces Rate Limiting (10 req/s, burst 20)                 |   |
|   |   - Injects Security Headers (X-Content-Type-Options: nosniff)  |   |
|   |   - Forwards Client Headers (X-Real-IP, X-Forwarded-For)        |   |
|   +--------------------------------+--------------------------------+   |
|                                    |                                    |
|                      proxy_pass    | http://api:8000 (Internal Only)    |
|                                    v                                    |
|   +-----------------------------------------------------------------+   |
|   |                     FastAPI Inference Service                   |   |
|   |   - Port 8000 exposed ONLY within internal Docker network       |   |
|   |   - Validates JSON payload against OpenAPI Contract             |   |
|   |   - Provides /health and /v1/predict endpoints                  |   |
|   +-----------------------------------------------------------------+   |
+-------------------------------------------------------------------------+
```

### Key Architectural Guarantees
1. **Network Isolation**: The Python backend service (`api`) does **not** map ports to the host machine. It binds only to an internal Docker network, making direct external access impossible.
2. **Reverse Proxy Security**: All external traffic flows through Nginx on port `8080`. Nginx applies rate limiting (Leaky Bucket) and hardening headers (`X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`).
3. **Contract-First Compliance**: API schemas and paths strictly adhere to the OpenAPI 3.0 specification defined in `openapi.yaml`.

---

## File Structure

```text
.
├── docker-compose.yml   # Orchestrates Nginx and API services with network isolation
├── Dockerfile           # Builds isolated Python FastAPI inference container
├── nginx.conf           # Reverse proxy configuration with rate limiting & security headers
├── openapi.yaml         # OpenAPI 3.0.3 specification contract
├── requirements.txt     # Python dependencies (FastAPI, Uvicorn, Pydantic)
├── app.py               # Application entrypoint (/health and /v1/predict)
└── README.md            # Setup, testing, and architecture documentation
```

---

## Quickstart (One-Command Setup)

To build and start the entire stack in detached mode:

```bash
docker-compose up -d --build
```

To view service status and verify health:

```bash
docker-compose ps
```

To view real-time logs:

```bash
docker-compose logs -f
```

To stop and tear down the containers:

```bash
docker-compose down
```

---

## API Testing & Verification

### 1. Health Check Endpoint (`GET /health`)
Verify that the service is running and healthy via the Nginx proxy:

```bash
curl -i http://localhost:8080/health
```

**Expected Response (200 OK):**
```json
{"status":"ok"}
```

---

### 2. Valid Inference Request (`POST /v1/predict`)
Send a valid text payload conforming to the OpenAPI contract:

```bash
curl -i -X POST http://localhost:8080/v1/predict \
  -H "Content-Type: application/json" \
  -d '{"text": "I am delighted with the high performance of this deployment!"}'
```

**Expected Response (200 OK):**
```json
{
  "label": "positive",
  "score": 0.95
}
```

---

### 3. Input Validation Rejection (Invalid/Missing Payload)
Verify that missing or invalid payloads are gracefully rejected:

**Missing `text` field:**
```bash
curl -i -X POST http://localhost:8080/v1/predict \
  -H "Content-Type: application/json" \
  -d '{}'
```
**Expected Response:** `422 Unprocessable Entity`

**Malformed JSON:**
```bash
curl -i -X POST http://localhost:8080/v1/predict \
  -H "Content-Type: application/json" \
  -d '{"text": invalid_json'
```
**Expected Response:** `422 Unprocessable Entity` (or `400 Bad Request`)

---

### 4. Network Isolation Test (Direct Access Blocked)
Verify that direct host access to the backend port `8000` is blocked and fails:

```bash
curl -i -X POST http://localhost:8000/v1/predict \
  -H "Content-Type: application/json" \
  -d '{"text": "test"}'
```

**Expected Output:**
```text
curl: (7) Failed to connect to localhost port 8000: Connection refused
```

---

### 5. Security Headers Verification
Inspect response headers from Nginx to verify security hardening:

```bash
curl -I http://localhost:8080/health
```

**Key Response Headers:**
```http
HTTP/1.1 200 OK
Server: nginx/...
X-Content-Type-Options: nosniff
X-Frame-Options: DENY
Content-Type: application/json
```

---

### 6. Rate Limiting Verification
The Nginx configuration defines `limit_req_zone $binary_remote_addr zone=mylimit:10m rate=10r/s;` with `burst=20 nodelay`. Rapidly firing requests exceeding the burst limit triggers:

```http
HTTP/1.1 503 Service Temporarily Unavailable
```

---

### 7. Nginx Configuration Syntax Test
Verify the syntax of the Nginx configuration file:

```bash
docker-compose exec nginx nginx -t
```

**Expected Output:**
```text
nginx: the configuration file /etc/nginx/nginx.conf syntax is ok
nginx: configuration file /etc/nginx/nginx.conf test is successful
```
