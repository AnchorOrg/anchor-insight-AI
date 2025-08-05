Here’s the same API design in English, with seven endpoints:

---

# Anchor Insight AI API Endpoints

**Base path:** `/api/v1`

| # | Method         | Path                                    | Data type | Description                                                                                                                                                                                                                              |
| - | -------------- | --------------------------------------- | --------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1 | **POST** | `/session`                            |           | Create a new focus session (register user goal).                                                                                                                                                                                         |
| 2 | **POST** | `/session/{session_id}/stream/camera` |           | Upload a short camera video chunk (captured via OpenCV).                                                                                                                                                                                 |
| 3 | **POST** | `/session/{session_id}/stream/screen` |           | Upload a short screen‐share screenshot                                                                                                                                                                                                  |
| 4 | POST           | `/session/{session_id}/notifications` |           | send real‐time “stay focused” notifications ( from anchor insight to anchor app, or directly to the anchor focus frontend. need a judgement)                                                                                          |
| 5 | **POST** | `/session/{session_id}/feedback`      | String    | receive end‐of‐session feedback: goal achieved flag, comments, user rating. Within 3 pieces of adivices.                                                                                                                              |
| 6 | POST           | `/sessions/{session_id}/score`        |           | At this point, since the user didn't input the final feedback, therefore the score would be based on previous data collected during the  focus session.<br />Need fast feedback.<br />send the current session score at the sesison end |
| 7 | **POST** | `/sessions/{session_id}/report`       |           | Send the final score (“B” rating after feedback) plus suggested actions at session end if the session doesn't have user input score by MySQL DB query.                                                                                 |

---

## Endpoint Details

### 1. Create Session

```
POST /api/v1/sessions
```

**Request body** (JSON):

```json
{
  "user_id": "string",
  "goal": "Read Chapter 5 of the book",
  "metadata": { /* optional settings */ }
}
```

**Response**:

```json
{
  "session_id": "uuid",
  "started_at": "2025-08-05T14:30:00Z"
}
```

### 2. Upload Camera Chunk

```
POST /api/v1/sessions/{session_id}/stream/camera
```

* **Content-Type**: `multipart/form-data` or `application/octet-stream`
* **Path parameter**: `session_id`

### 3. Upload Screen‐Share Chunk

```
POST /api/v1/sessions/{session_id}/stream/screen
```

* **Content-Type**: `multipart/form-data` or `application/octet-stream`
* **Path parameter**: `session_id`

### 4. Real‐time Notifications

```
GET /api/v1/sessions/{session_id}/notifications
```

* **Response type**: `text/event-stream` (SSE) or WebSocket
* Streams “please refocus” events when the AI detects distraction.

### 5. Submit Feedback

```
POST /api/v1/sessions/{session_id}/feedback
```

**Request body** (JSON):

```json
{
  "achieved": true,
  "comments": "I mostly stayed focused but got distracted once.",
  "rating": 4
}
```

### 6. Get In‐Session Score

```
GET /api/v1/sessions/{session_id}/score
```

**Response**:

```json
{
  "score": 75,
  "timestamp": "2025-08-05T15:00:00Z"
}
```

### 7. Get Final Report

```
GET /api/v1/sessions/{session_id}/report
```

**Response**:

```json
{
  "final_score": 82,
  "actions": [
    "Take a 5-minute break every 25 minutes",
    "Mute non-essential notifications"
  ]
}
```

---

This set of endpoints covers:

1. **Session management** (start, feedback)
2. **Data ingestion** (camera/screen chunks)
3. **Real-time alerts**
4. **Score reporting** (interim and final) with suggested actions

anchorは、自己定量化製品の構築を支援する会社であり、将来的には自動化製品を構築する予定です。未来を築き、人類社会に奇跡を起こすことを目指しています。
