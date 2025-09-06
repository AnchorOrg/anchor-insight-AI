# Hoppscotch Usage Guide (Anchor Insight AI)

This guide explains how to import and call the project’s Hoppscotch collection (`./docs/hoppscotch.json`) in sequence, with practical notes for each request to serve as an operational guide.

> Basics
>
> - Base URL: `http://localhost:7003`
> - Unified prefix: `/api/v1`
> - Run (example): `pipenv run python src/app/main.py`
> - Camera monitoring requires a local camera; focus scoring (`/analyze`) requires an OpenAI API key (`OPENAI_API_KEY` in `.env`).

## Import the Collection

1) Open Hoppscotch (Web or App).
2) Go to Collections → Import → select `./docs/hoppscotch.json` from this repository.
3) After import you will see three folders: General, Monitor Service, Focus Score Service.

## Recommended Call Order (Quick Start)

1) General (optional but recommended)
   - GET `/` (Root) → verify the service is running
   - GET `/health` (Health Check) → quick liveness probe
2) Focus Score Service (optional, for screenshot scoring)
   - GET `/api/v1/analyze/health` → check configuration and availability
   - GET `/api/v1/analyze/health/detail` → detailed health (includes OpenAI connectivity)
   - POST `/api/v1/analyze/upload` → upload an image file to get a focus score
3) Monitor Service (full camera-monitoring flow)
   - POST `/api/v1/monitor/start?session_id=default` → start monitoring
   - Poll: GET `/status`, `/score`, `/latest`, `/records`, `/summary` (all with `session_id`)
   - POST `/stop` (with `session_id`) → stop monitoring
   - Optional: GET `/sessions` to list sessions; DELETE `/session/{session_id}` to remove a session

> Note: `session_id` defaults to `default`. For concurrent sessions, use different `session_id` values to isolate state and records within the same process.

---

## General Group

### 1) Root
- Method & Path: GET `http://localhost:7003/`
- Purpose: Returns service metadata (name, status, version, major routes) to confirm the service is running.
- When to use: Initial connectivity verification or to confirm route prefixes.

### 2) Health Check
- Method & Path: GET `http://localhost:7003/health`
- Purpose: Lightweight health check returning `{ status: "healthy", version: "..." }`.
- When to use: Liveness probe, automation monitoring, or quick local check.

---

## Monitor Service Group (Camera-based focus monitoring)

> Common query parameter: `session_id` (optional, defaults to `default`). The same `session_id` refers to the same monitoring session.

### 1) Start Monitoring
- Method & Path: POST `/api/v1/monitor/start`
- Query: `session_id=default`
- Request Body (JSON):
  ```json
  {
    "show_window": false,
    "model_path": "./your/path/yolo11s-pose.pt",
    "camera_index": 0
  }
  ```
- Purpose:
  - Create or get the monitoring session for the `session_id` and asynchronously start YOLOv11-Pose camera detection.
  - `show_window=false` is recommended for headless environments; if `model_path` is omitted, defaults apply (it’s recommended to pass `yolo11s-pose.pt` explicitly).
- Response: `{ status, message, config }`. If the camera isn’t available, it may still return `started` (the service degrades gracefully and logs the error).
- When to use: Before starting a new camera monitoring session.
- Note: During testing, ensure the camera is not used by other applications.

### 2) Get Status
- Method & Path: GET `/api/v1/monitor/status`
- Query: `session_id=default`
- Purpose: Query initialization status, whether a person is currently detected, the current session summary, and the total number of records.
- Key fields: `is_initialized`, `person_detected`, `current_session` (type and elapsed minutes), `total_records`.
- When to use: Poll during monitoring to check status and whether recording has started.

### 3) Get Focus Score
- Method & Path: GET `/api/v1/monitor/score`
- Query: `session_id=default`
- Purpose: Compute the focus score (0–100) from accumulated “focus/leave” periods (internally normalized from a 0–5 scale).
- Key fields: `focus_score` (integer 0–100), `confidence` (high/low).
- When to use: During or after monitoring to obtain interim or overall focus score.

### 4) Get Latest Record
- Method & Path: GET `/api/v1/monitor/latest`
- Query: `session_id=default`
- Purpose: Fetch the most recent formatted “focus/leave” time block (e.g., “xx/xx/xxxx Focus time: hh:mm am - hh:mm am”).
- Key fields: `latest_record` (string). When none, `message` is `"no records"`.
- When to use: Incremental reading of the latest block.

### 5) Get Records
- Method & Path: GET `/api/v1/monitor/records`
- Query: `session_id=default`
- Purpose: Fetch all recorded time blocks for the current session.
- Key fields: Each item contains `type` (focus/leave), `start`, `end`, `formatted`, `duration_minutes`.
- When to use: Export or display the full focus/leave timeline.

### 6) Get Summary
- Method & Path: GET `/api/v1/monitor/summary`
- Query: `session_id=default`
- Purpose: Retrieve summary statistics.
- Key fields: `total_focus_minutes`, `total_leave_minutes`, `focus_sessions`, `leave_sessions`.
- When to use: Periodic summary during monitoring or for a final report.

### 7) Health Check
- Method & Path: GET `/api/v1/monitor/health`
- Purpose: Health of the monitoring subsystem; includes whether any session is running and a UTC timestamp.
- When to use: Subsystem-only check (not the whole service).

### 8) List Sessions
- Method & Path: GET `/api/v1/monitor/sessions`
- Purpose: List all existing session IDs.
- When to use: Manage multi-session setups.

### 9) Stop Monitoring
- Method & Path: POST `/api/v1/monitor/stop`
- Query: `session_id=default`
- Purpose: Stop monitoring for the session and “close” any ongoing time block for accounting.
- Key fields: `{ status, message, final_stats }`, where `final_stats` is the final summary for the session.
- When to use: Call when the monitoring run is complete.

### 10) Remove Session
- Method & Path: DELETE `/api/v1/monitor/session/{session_id}` (example: `.../session/default`)
- Purpose: Remove a session and its resources (stops it first if running).
- When to use: Clean up unused sessions to free memory.

> Tips:
> - To show the camera feed overlay, set `show_window=true`; press `q` to close the window and end the loop.
> - Camera parameters (resolution, FPS, buffer, etc.) are configurable in `src/config/settings.py`; `yolo11s-pose.pt` is included at the repository root.

---

## Focus Score Service Group (Screenshot focus scoring)

> This group does not rely on a camera. It analyzes uploaded screenshots using OpenAI’s multimodal API and returns a 0–100 focus score.

### 1) Health Check
- Method & Path: GET `/api/v1/analyze/health`
- Purpose: Basic health check, returns current model and limit settings.
- When to use: Initial validation or troubleshooting.

### 2) Detailed Health Check
- Method & Path: GET `/api/v1/analyze/health/detail`
- Purpose: Deep check that attempts to reach the OpenAI API and reports connectivity.
- When to use: Diagnose OpenAI-related issues (key/network/quota/model availability).

### 3) Analyze Uploads
- Method & Path: POST `/api/v1/analyze/upload`
- Body (multipart/form-data): field name `file`, upload an image file
- Supported types: `image/jpeg`, `image/jpg`, `image/png`, `image/gif`, `image/webp`, `image/bmp`
- Purpose: Convert the image to Base64 and analyze with OpenAI, returning `focus_score` (0–100).
- Key fields: `focus_score`, `confidence` (always `high`), `processing_time` (seconds).
- Common issues:
  - Files larger than the default limit (> 10MB) or unsupported types return 400.
  - Missing or invalid `OPENAI_API_KEY` will cause health checks or scoring to fail.

---

## Typical End-to-End Scenarios

1) Local camera focus monitoring (single session)
   1. GET `/` → GET `/health`
   2. POST `/api/v1/monitor/start?session_id=default` (`show_window=false`)
   3. Poll GET `/status` and `/score` (optionally add `/latest`/`/records`/`/summary`)
   4. POST `/stop?session_id=default` → GET `/summary` (verify final stats)
   5. DELETE `/session/default` (optional cleanup)

2) Quick focus assessment via screenshot upload
   1. GET `/api/v1/analyze/health` (or `/health/detail`)
   2. POST `/api/v1/analyze/upload` (`file` picks a local screenshot)

---

## Common Troubleshooting Tips

- Port & routes: The unified service in this branch listens on port `7003` with the unified prefix `/api/v1`.
- Camera permissions: Your container/system must allow camera access. If the camera cannot be opened, `start` may still return `started` (graceful degradation), but status will show “not initialized / no person detected”.
- Model path: It’s recommended to pass `"./yolo11s-pose.pt"` explicitly in the `start` request (the file is at the repo root) to avoid relying on system defaults.
- OpenAI key: Endpoints under screenshot scoring require a valid `OPENAI_API_KEY`, plus an available model, reachable network, and sufficient billing/quota.
