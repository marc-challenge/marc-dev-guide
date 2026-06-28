# API Reference — ROS 2 Interface

The platform and your agent communicate entirely over **ROS 2 (Fast DDS)**. This page is
the single source of truth for topics, messages, QoS, and coordinate frames.

Two transport families:

- **Operations (`/marc/ops/...`)** — `std_msgs/String` carrying JSON with a `header` /
  `payload` structure and a numeric `msg` id. Session, missions, submissions, scores.
- **Sensors / control** — standard ROS 2 message types on dedicated topics (Image,
  CameraInfo, Twist, JointState, LaserScan, OccupancyGrid, TF).

---

## Namespaces

```
/marc/
├── ops/                                  # operations (JSON + msg id)
│   ├── register                          #   session handshake (fixed topic)
│   ├── announce                          #   Platform -> All (missions, state, time)
│   └── {team_id}/
│       ├── request                       #   Participant -> Platform
│       ├── response                      #   Platform -> Participant
│       └── notification                  #   Platform -> Participant (async)
├── env/                                  # environment (standard ROS 2 msgs)
│   ├── cctv/{id}/image, info             #   CCTV RGB + camera params
│   └── map/occupancy, metadata           #   static 2D occupancy grid
├── {team_id}/robot/                      # per-team robot sensors / control
│   ├── base_camera/{left,right}/image, info, depth/image, points
│   ├── gripper_camera/{left,right}/image, info, depth/image, points
│   ├── odom, imu, lidar/scan
│   ├── arm/joint_states, arm/joint_command
│   └── cmd_vel
/tf
/clock
```

---

## Handshake (session authentication)

Registration is a **challenge-response** handshake. Your long-term team token is **never
sent on the wire**; you prove possession with an HMAC and receive a short-lived
`session_key`.

```
HELLO (100)  -> CHALLENGE (410) -> PROOF (101) -> SESSION_ACK (400)
participant     platform           participant     platform
```

1. **HELLO (msg 100)** on `/marc/ops/register` — `{ team_id, team, client_nonce }`.
2. **CHALLENGE (msg 410)** on `.../response` — `{ server_nonce, ttl, alg: "HMAC-SHA256" }`.
3. **PROOF (msg 101)** on `/marc/ops/register` — `proof = HMAC-SHA256(token, "server_nonce|client_nonce|team_id")`.
4. **SESSION_ACK (msg 400)** on `.../response` — `{ status: "ok", session_key, expires_at }`.

After ACK, every `request` message carries the issued `session_key` in `header.session`.
The token value and how it is derived are **not published** here — you receive your token
out of band. The SDK performs the whole handshake for you in `connect()`.

---

## Message header

Every operations message is `{ "header": {...}, "payload": {...} }`.

| Field | Type | Required on | Description |
|---|---|---|---|
| `msg` | int | all | Message type id. |
| `timestamp` | float | all | Publish time (Unix epoch, seconds). |
| `seq` | int | request, response | Request/response pairing key; **monotonically increasing** per session (replay defense). |
| `session` | string | request only | Issued `session_key` (not the static token). |

---

## Control topics

### `cmd_vel` — base motion

`/marc/{team_id}/robot/cmd_vel`, type `geometry_msgs/Twist`.

| Field | Meaning |
|---|---|
| `linear.x` | Forward/back (m/s), + = forward |
| `linear.y` | Lateral (m/s), + = left |
| `angular.z` | Yaw (rad/s), + = counter-clockwise |

| Constraint | Value |
|---|---|
| Motion plane | XY (2D) |
| Frame | Z-up right-handed (ROS 2 REP-103) |
| **Max linear speed** | **1.5 m/s** |
| **Max angular speed** | **1.0 rad/s** |

`linear.z`, `angular.x`, `angular.y` are unused.

### Manipulator — joint command

`/marc/{team_id}/robot/arm/joint_command`, type `sensor_msgs/JointState`.

| Property | Value |
|---|---|
| DoF | **6** (`joint_1`..`joint_6`) |
| Control mode | Position target (radians) |
| State publish rate | **60 Hz** (physics-step synced), on `arm/joint_states` |

The arm is a 6-DoF (non-redundant) manipulator with a Robotiq 2F-140 gripper; the mobile
base provides the redundancy for whole-body reach. See the
[Technical Guide → manipulation kit](technical-guide.md#manipulation-learning-kit).

---

## Sensor topics

### CCTV (environment)

| Topic | Type | Notes |
|---|---|---|
| `/marc/env/cctv/{id}/image` | `sensor_msgs/Image` | RGB, encoding `rgb8` |
| `/marc/env/cctv/{id}/info` | `sensor_msgs/CameraInfo` | intrinsics (K) |

| Property | Value |
|---|---|
| Resolution | **3840 x 2160 (8MP, 16:9)** |
| `frame_id` | `{camera_id}` |

Discover available ids by listing topics under `/marc/env/cctv/`.

### Robot stereo cameras

Stereo cameras on the **base** (`base_camera/`, driving + search) and the **gripper**
(`gripper_camera/`, close-range pick-and-place). Each provides `left`/`right` RGB
(`rgb8`), `depth/image` (`32FC1`, metres), and `points` (`sensor_msgs/PointCloud2`).

### Other robot sensors

| Topic | Type | Rate |
|---|---|---|
| `odom` | `nav_msgs/Odometry` | 60 Hz |
| `imu` | `sensor_msgs/Imu` | 60 Hz |
| `lidar/scan` | `sensor_msgs/LaserScan` | — |
| `arm/joint_states` | `sensor_msgs/JointState` | 60 Hz |

```{note}
Exact lidar range/FOV/rate and the stereo resolution/baseline are finalized with the robot
USD asset and published with the frozen release.
```

### Map

| Topic | Type | Notes |
|---|---|---|
| `/marc/env/map/occupancy` | `nav_msgs/OccupancyGrid` | static 2D grid, latched |
| `/marc/env/map/metadata` | `nav_msgs/MapMetaData` | resolution, origin, size |

The occupancy map encodes **drivable road only**; people and landmarks are **not** in the
map (detect them with sensors). Frame `map`, Z-up, metres.

---

## TF / coordinate frames

| Item | Spec |
|---|---|
| Standard | ROS 2 REP-103 |
| Axes | X = forward, Y = left, Z = up (right-handed) |
| Units | metres; radians (Twist), degrees (YAML) |
| TF | `/tf` (`tf2_msgs/TFMessage`), parent `world` -> robot prim |
| Clock | `/clock` (`rosgraph_msgs/Clock`), simulation time |

Isaac Sim 5.x is Z-up right-handed, so no axis conversion is needed.

```{admonition} Mission-area ground-plane assumption
:class: note
Mission areas are computed by projecting each camera ray onto a **per-camera ground plane**
(`z = ground_height`), not onto one global flat plane. The scene is not perfectly flat —
there is roughly a 10 cm step between road and grass — so account for the relevant ground
height when back-projecting CCTV pixels to world coordinates.
```

---

## QoS profiles

| Topic class | Reliability | Durability | History | Depth |
|---|---|---|---|---|
| Operations (JSON), `cmd_vel`, `joint_command`, TF, Clock | RELIABLE | VOLATILE | KEEP_LAST | 10 |
| `{team_id}/response`, map (occupancy) | RELIABLE | TRANSIENT_LOCAL | KEEP_LAST | 10 |
| Sensor images | BEST_EFFORT | VOLATILE | KEEP_LAST | 1 |

`TRANSIENT_LOCAL` lets late joiners still receive the `SESSION_ACK` and the latched map.

---

## Message dictionary

| id | Name | Topic | Direction |
|---|---|---|---|
| 100 | SESSION_HELLO | `ops/register` | Participant -> Platform |
| 101 | SESSION_PROOF | `ops/register` | Participant -> Platform |
| 201 | MISSION_COMMAND (Stage 1) | `ops/announce` | Platform -> All |
| 202 | COMPETITION_STATE | `ops/announce` | Platform -> All |
| 203 | TIME_REMAINING | `ops/announce` | Platform -> All |
| 204 | TIME_EXPIRED | `ops/announce` | Platform -> All |
| 211 | STAGE2_MISSION | `ops/announce` | Platform -> All |
| 301 | GROUNDING_RESULT (Stage 1) | `ops/{team}/request` | Participant -> Platform |
| 302 | TASK_COMPLETE (Stage 2) | `ops/{team}/request` | Participant -> Platform |
| 311 | STAGE2_GROUNDING_RESULT | `ops/{team}/request` | Participant -> Platform |
| 400 | SESSION_ACK | `ops/{team}/response` | Platform -> Participant |
| 401 | SCORE_RESULT | `ops/{team}/response` | Platform -> Participant |
| 410 | SESSION_CHALLENGE | `ops/{team}/response` | Platform -> Participant |
| 501 | STAGE_TRANSITION | `ops/{team}/notification` | Platform -> Participant |
| 502 | WARNING | `ops/{team}/notification` | Platform -> Participant |

### Competition states (msg 202)

`READY` -> `STAGE1_RUN` -> `STAGE2_RUN` -> `FINISHING` -> `FINISHED`.

### Grounding payload (msg 301 / 311)

Single-target model. `target_type` is a single string; coordinates are single 3D points.

```json
{
  "camera_id": "rig_1_a",
  "interpretation": {
    "target_type": "cola_can",
    "landmark": "bench",
    "relation": "beside",
    "situation": "normal"
  },
  "grounding": {
    "anchor_coord": [-62.3, 151.2, 16.5],
    "target_coord": [-62.1, 151.5, 16.5]
  }
}
```

| Field | Meaning |
|---|---|
| `interpretation.target_type` | Single object type. Person problems use `"person"`. |
| `interpretation.landmark` | Reference landmark name (when a relation is involved). |
| `interpretation.relation` | Spatial relation (`near`, `beside`, `behind`, `front`, `left`, `right`, `on`, `above`) — for lost-and-found relation problems. |
| `interpretation.situation` | Situation category (`accident`, `emergency`, `abnormal`, `normal`) — for SAR person problems. |
| `grounding.anchor_coord` | Estimated landmark coordinate `[x, y, z]` (m). |
| `grounding.target_coord` | Estimated target coordinate `[x, y, z]` (m). |
