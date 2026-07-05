# API Reference

This page is the single source of truth (SSoT) for the interfaces participants reference, and
it is split into two layers.

- marc_sdk Python API — the layer most participants call directly. It covers client creation
  and connection, callbacks, sensor queries, robot control, answer submission, and the data
  types exchanged.
- ROS 2 interface — the lower layer of topics, messages, QoS, and coordinate frames that
  marc_sdk exchanges with the platform internally. With the SDK you rarely deal with it
  directly, but you reference it when accessing at a low level or checking a specification.

The basic usage of preparing the SDK and creating a client is explained first in the
[Technical Guide](technical-guide.md).

---

## marc_sdk

At the center of `marc_sdk` is a single class, `MARCClient`. The ROS 2 communication with the
platform — the registration handshake, distinguishing message types, session and sequence
management, QoS, and CCTV camera auto-discovery — is handled internally by `MARCClient`.
Below is the full reference for its public API (source of truth: `marc_sdk/client.py` and
`types.py`).

### Client creation and connection

- `MARCClient.from_env(**kwargs) -> MARCClient`
  - Parameters: reads the team ID and authentication token from the environment variables
    `MARC_TEAM_ID` / `MARC_TOKEN`. Additional keyword arguments are passed through to
    `MARCClient(...)`.
  - Returns: an initialized `MARCClient`. Instead of environment variables, you can also
    create it directly with `MARCClient(team_id=..., token=...)`.
- `connect(timeout=30.0, register_period=2.0) -> bool`
  - `timeout` (`float`, default `30.0`) — the maximum time (seconds) to wait for
    `SESSION_ACK`
  - `register_period` (`float`, default `2.0`) — the registration retry period (seconds)
  - Behavior: rclpy init -> create node/publishers/subscribers -> challenge-response
    handshake (HELLO -> CHALLENGE -> PROOF -> ACK) -> start the background executor.
  - Returns: `True` if authentication succeeds.
- `run()`
  - Parameters: none
  - Behavior: spins the node and blocks the main thread (exit with Ctrl-C). Callbacks are
    called on the background executor thread.
- `shutdown()`
  - Parameters: none
  - Behavior: sends a stop command, then cleans up the node/executor (safe to call more than
    once).
- `is_running` (property, `bool`)
  - `True` during the Stage 2 driving phase. Use it as the exit condition for the
    `on_stage2_run` loop.
- `stage2_reveal` (property)
  - The most recent Stage 2 reveal (`Stage2Reveal` or `None`). Use it when checking by
    polling instead of `on_stage2_reveal`.

### Callbacks

While the platform and the SDK communicate, moments arise when the agent should take some
action (e.g. a new mission arriving) or when real-time information must be delivered to the
agent (e.g. time remaining, state changes, scoring results). If you register a callback
function on the decorator that corresponds to each event, the SDK automatically calls the
registered callback when that event occurs. Callbacks are called on the background executor
thread.

| Decorator | Summary |
|---|---|
| `@client.on_mission` | Stage 1 round problem issued |
| `@client.on_stage2_mission` | Stage 2 problem issued |
| `@client.on_stage2_run` | Stage 2 driving begins |
| `@client.on_stage2_reveal` | Stage 2 grounding score revealed |
| `@client.on_state_change` | competition state transition |
| `@client.on_time_remaining` | time-remaining update |
| `@client.on_time_expired` | time limit expired |
| `@client.on_transition` | stage transition |
| `@client.on_score` | scoring result |
| `@client.on_warning` | warning |

Each callback is organized as (when it fires / signature / what to do inside the callback)
below. The signature is the arguments the registered callback function receives, and the
sub-items are the type and meaning of each argument (or its fields).

**Mission handling**

- `on_mission`
  - Fires: when the platform issues each Stage 1 round problem (msg 201)
  - Signature: `fn(mission)`
    - `mission.voice_command` (`str`) — the person's natural-language command to process
    - `mission.round` (`int`) — the current round number
    - `mission.total_rounds` (`int`) — the total number of Stage 1 rounds
    - `mission.time_limit` (`float`) — this round's time limit (seconds)
  - Implement: interpret the natural-language command, find the target, and submit with
    `submit_grounding()`
- `on_stage2_mission`
  - Fires: when the platform issues the Stage 2 problem (msg 211)
  - Signature: `fn(mission)`
    - `mission.task_description` (`str`) — the task command to process
    - `mission.time_limit` (`float`) — the time limit (seconds)
    - `mission.owner_position` (`list[float]` or `None`) — the position `[x, y, z]` to bring
      the object to (`None` if there is no owner_zone)
  - Implement: interpret the command, find the target, and submit with
    `submit_stage2_grounding()`
- `on_stage2_reveal`
  - Fires: right after Stage 2 grounding is scored (msg 411)
  - Signature: `fn(reveal)`
    - `reveal.grounding_score` (`float`) — the score of this grounding submission (0–100)
    - `reveal.target_type` (`str`) — the type of object to pick
    - `reveal.hint_center` (`list[float]`) — the center of the target's approximate location
      `[x, y, z]` (not the exact answer)
    - `reveal.hint_radius` (`float`) — the approximate-location radius (m)
  - Implement: from the candidates within the radius, choose the object by
    `reveal.target_type`, and prepare to collect toward this location (can also be polled via
    the `client.stage2_reveal` property)
  - Note: this is designed so that **even if you submitted the Stage 2 grounding
    incorrectly**, the platform tells you the approximate answer location so you can continue
    navigation and pick & place. Thanks to this, your collection-and-delivery ability can be
    evaluated regardless of grounding accuracy.
- `on_stage2_run`
  - Fires: when entering the Stage 2 driving phase (a separate thread)
  - Signature: `fn()` — no arguments
  - Implement: loop while `client.is_running` is true, doing navigation, picking, and
    delivery, and call `task_complete()` when done

**State and time notifications**

- `on_state_change`
  - Fires: when the competition state changes (msg 202)
  - Signature: `fn(old, new)`
    - `old` (`str`) — the previous state
    - `new` (`str`) — the next state (`READY` -> `STAGE1_RUN` -> `STAGE2_RUN` -> `FINISHING`
      -> `FINISHED`)
  - Implement: initialize/transition internal logic per state
- `on_transition`
  - Fires: on a stage transition notice (msg 501)
  - Signature: `fn(from_state, to_state)`
    - `from_state` (`str`) — the state before the transition
    - `to_state` (`str`) — the state after the transition
  - Implement: handle the transition point (similar to `on_state_change`)
- `on_time_remaining`
  - Fires: when the time remaining is updated periodically (msg 203)
  - Signature: `fn(remaining)`
    - `remaining` (`float`) — the time remaining (seconds)
  - Implement: adjust strategy by time (e.g. hurry when little time is left)
- `on_time_expired`
  - Fires: when the time limit ends (msg 204)
  - Signature: `fn(which)`
    - `which` (`str`) — the kind of time that ended (`'stage1'` / `'total'`)
  - Implement: clean up / stop the work in progress

**Results and warnings**

- `on_score`
  - Fires: when a scoring result arrives (msg 401)
  - Signature: `fn(score)`
    - `score.total` (`float`) — the total score
    - `score.scores` (`dict`) — the detailed score items
    - `score.is_final` (`bool`) — whether it is the final result (`False` for a round score)
    - `score.round` (`int` or `None`) — the round number (`None` for the final result)
  - Implement: check / record the score
- `on_warning`
  - Fires: when the platform sends a warning (msg 502)
  - Signature: `fn(type, message)`
    - `type` (`str`) — the warning type
    - `message` (`str`) — the warning message
  - Implement: record or respond to the warning type and message

### Sensor queries

The sensor data the platform publishes is queried with the functions below. Every function
returns the most recently received ROS 2 message as-is (thread-safe), and returns `None` if
no value has been received yet.

| Function | Summary |
|---|---|
| `list_cctv()` | list of available CCTV ids |
| `get_cctv_image(camera_id)` | CCTV RGB image |
| `get_cctv_info(camera_id)` | CCTV intrinsics |
| `get_robot_image(which)` | robot camera RGB image |
| `get_robot_depth(which)` | robot camera depth image |
| `get_lidar()` | robot lidar scan |
| `get_odom()` | robot odometry |
| `get_imu()` | robot IMU |
| `get_arm_state()` | robot arm joint state |
| `is_grasping()` | whether the gripper is holding an object |
| `is_basket_occupied()` | whether an object is loaded in the basket |
| `get_occupancy_map()` | occupancy grid map |
| `get_world_pose()` | robot position and orientation |
| `subscribe(topic, msg_type, callback, qos)` | subscribe to an arbitrary topic directly |

- `list_cctv() -> list[str]`
  - Parameters: none
  - Returns: the list of discovered CCTV camera ids. Pass these ids to the two functions
    below.
- `get_cctv_image(camera_id: str) -> sensor_msgs/Image | None`
  - `camera_id` (`str`) — the CCTV id to query (check with `list_cctv()`)
  - Returns: that camera's latest RGB frame (encoding `rgb8`). The primary input for VLA
    perception.
- `get_cctv_info(camera_id: str) -> sensor_msgs/CameraInfo | None`
  - `camera_id` (`str`) — the CCTV id to query
  - Returns: that camera's intrinsics (projection matrix K, etc.). Used for pixel<->3D
    conversion.
- `get_robot_image(which: str = "base_left") -> sensor_msgs/Image | None`
  - `which` (`str`, default `"base_left"`) — the robot camera position. One of
    `base_left`, `base_right`, `gripper_left`, `gripper_right` (other values raise
    `ValueError`).
  - Returns: that camera's latest RGB image (`rgb8`).
- `get_robot_depth(which: str = "base") -> sensor_msgs/Image | None`
  - `which` (`str`, default `"base"`) — the depth camera family. One of `base`, `gripper`
    (other values raise `ValueError`).
  - Returns: that camera's depth image (`32FC1`, pixel value = distance in metres).
- `get_lidar() -> sensor_msgs/LaserScan | None`
  - Parameters: none
  - Returns: the robot's 2D lidar scan. Used for close-range obstacle avoidance.
- `get_odom() -> nav_msgs/Odometry | None`
  - Parameters: none
  - Returns: robot odometry (position and velocity).
- `get_imu() -> sensor_msgs/Imu | None`
  - Parameters: none
  - Returns: inertial sensor values (orientation, angular velocity, acceleration).
- `get_arm_state() -> sensor_msgs/JointState | None`
  - Parameters: none
  - Returns: the robot arm's current joint state (joint angles, etc.).
- `is_grasping() -> bool | None`
  - Parameters: none
  - Returns: `True` if the gripper is currently holding an object, else `False` (`None`
    before the first message arrives). Isomorphic to the object detection of a real Robotiq
    2F-140: if a close command is blocked by an object and cannot close to the target angle,
    it is `True`. Used to detect a failed pick (stays `False`) or a drop in transit (`True`
    -> `False`) and retry.
- `is_basket_occupied() -> bool | None`
  - Parameters: none
  - Returns: `True` if an object is currently in the rear basket, else `False` (`None` before
    the first message arrives). Like a real basket-load sensor, it is a generic signal that
    only tells you "whether something is loaded"; it does not tell you whether the correct
    object was delivered or the score. Used to confirm delivery success or detect a case
    where it fell outside the basket (retry). The provided cameras cannot see the rear
    basket, so confirm delivery with this signal. Published in Stage 2 only.
- `get_occupancy_map() -> nav_msgs/OccupancyGrid | None`
  - Parameters: none
  - Returns: the static 2D occupancy grid (drivable road only). The input for path planning.
- `get_world_pose() -> tuple[float, float, float] | None`
  - Parameters: none
  - Returns: the robot's world coordinate and orientation `(x, y, yaw_rad)`. Same coordinate
    frame as the submitted coordinate `target_coord`, and the position feedback for Stage 2
    driving.
- `subscribe(topic: str, msg_type, callback, qos=None)`
  - `topic` (`str`) — the ROS 2 topic name to subscribe to
  - `msg_type` — the message type class (e.g. `sensor_msgs.msg.Image`)
  - `callback` — the function `fn(msg)` to call when a message is received
  - `qos` (default `None`) — the QoS profile. Default (RELIABLE) if `None`
  - Returns: the rclpy subscription object (`rclpy.subscription.Subscription`)
  - Note: an escape hatch to subscribe to an arbitrary topic directly when the functions
    above are not enough.

### Robot control

Controls the robot body's motion and the robot arm.

| Function | Summary |
|---|---|
| `send_cmd_vel(linear_x, linear_y, angular_z)` | body motion command |
| `stop()` | stop the body |
| `send_arm_command(joint_state)` | robot arm joint command |

- `send_cmd_vel(linear_x=0.0, linear_y=0.0, angular_z=0.0, twist=None)`
  - `linear_x` (`float`, default `0.0`) — forward/back speed (m/s, + is forward)
  - `linear_y` (`float`, default `0.0`) — left/right lateral speed (m/s, + is left)
  - `angular_z` (`float`, default `0.0`) — rotation speed (rad/s, + is counter-clockwise)
  - `twist` (`geometry_msgs/Twist`, default `None`) — if given, this Twist is published as-is
    and the three arguments above are ignored
  - Returns: none
  - Note: max allowed 1.5 m/s / 1.0 rad/s. The SDK does not automatically clamp excess input,
    so the agent must respect it.
- `stop()`
  - Parameters: none
  - Behavior: stops the body immediately (publishes `cmd_vel` 0)
  - Returns: none
- `send_arm_command(joint_state)`
  - `joint_state` (`sensor_msgs/JointState`) — the robot arm's target joint state (6-axis
    joint angles)
  - Behavior: publishes as-is to the robot arm joint command topic (passthrough)
  - Returns: none

### Answer submission

Submits the Stage 1/2 answers and notifies Stage 2 collection completion. A grounding answer
is passed only as the `GroundingResult` type (see "Data types" below).

| Function | Summary |
|---|---|
| `submit_grounding(result)` | submit Stage 1 grounding (msg 301) |
| `submit_stage2_grounding(result)` | submit Stage 2 interpretation (msg 311) |
| `task_complete()` | Stage 2 collection done (msg 302) |

- `submit_grounding(result: GroundingResult) -> int`
  - `result` (`GroundingResult`) — the grounding result to submit. **Accepts only
    `GroundingResult`**. If you already have a payload dict, convert it with
    `GroundingResult.from_payload(payload)` and pass that.
  - Behavior: submit the Stage 1 grounding answer (msg 301)
  - Returns: the assigned request sequence number `seq` (`int`)
- `submit_stage2_grounding(result: GroundingResult) -> int`
  - Parameters: same as `submit_grounding` (`GroundingResult`)
  - Behavior: submit the Stage 2 interpretation answer (msg 311)
  - Returns: `seq` (`int`)
- `task_complete() -> int`
  - Parameters: none
  - Behavior: publish Stage 2 collection completion (msg 302). It switches to the finishing
    phase the moment it is called and cannot be cancelled.
  - Returns: `seq` (`int`)

### Data types

The data types exchanged as callback arguments and submission results (source of truth:
`marc_sdk/types.py`). Import with `from marc_sdk import GroundingResult`.

- `GroundingResult` — the grounding result you build and submit.
  - `camera_id` (`str`) — the CCTV id where the target is visible
  - `target_type` (`str`) — the target's type (`"person"` for person problems)
  - `anchor_coord` (`list[float]`) — the estimated reference-landmark coordinate `[x, y, z]`
  - `target_coord` (`list[float]`) — the estimated target coordinate `[x, y, z]`
  - `landmark` (`str`, default `""`) — the reference landmark name (when there is a spatial
    relation)
  - `relation` (`str`, default `None`) — the spatial relation (used in lost-item relation
    problems)
  - `situation` (`str`, default `None`) — the situation category (used in SAR person
    problems)
  - Methods: `GroundingResult.from_payload(payload: dict) -> GroundingResult` (create from a
    payload dict), `to_payload() -> dict` (serialize to the submission payload)
- `Mission` — the `on_mission` argument. Fields: `voice_command` (`str`), `round` (`int`),
  `total_rounds` (`int`), `time_limit` (`float`).
- `Stage2Mission` — the `on_stage2_mission` argument. Fields: `task_description` (`str`),
  `time_limit` (`float`), `owner_position` (`list[float]` or `None`).
- `Stage2Reveal` — the `on_stage2_reveal` argument. Fields: `grounding_score` (`float`),
  `target_type` (`str`), `hint_center` (`list[float]`), `hint_radius` (`float`).
- `Score` — the `on_score` argument. Fields: `total` (`float`), `scores` (`dict`), `is_final`
  (`bool`), `round` (`int` or `None`), `stage` (`str`).

---

## ROS 2

The platform and the agent communicate entirely over ROS 2. Since `marc_sdk` wraps this
layer, you normally do not deal with it directly, but reference this section when accessing at
a low level or checking a specification. There are two transport families.

- Operations (`/marc/ops/...`) — a `std_msgs/String` carrying JSON with a `header` / `payload`
  structure and a numeric `msg` id. Session, mission, submission, scoring.
- Sensors / control — standard ROS 2 messages on dedicated topics (Image, CameraInfo, Twist,
  JointState, LaserScan, OccupancyGrid, TF).

### Namespaces

```
/marc/
├── ops/                                  # ops (JSON + msg id)
│   ├── register                          #   session handshake (fixed topic)
│   ├── announce                          #   Platform -> All (mission / state / time)
│   └── {team_id}/
│       ├── request                       #   Participant -> Platform
│       ├── response                      #   Platform -> Participant
│       └── notification                  #   Platform -> Participant (async)
├── env/                                  # env (ROS 2 standard)
│   ├── cctv/{id}/image, info             #   CCTV RGB + camera params
│   └── map/occupancy, metadata           #   static 2D occupancy grid
├── {team_id}/robot/                      # per-team robot sensors / control
│   ├── base_camera/{left,right}/image, info, depth/image, points
│   ├── gripper_camera/{left,right}/image, info, depth/image, points
│   ├── odom, imu, lidar/scan
│   ├── arm/joint_states, arm/joint_command
│   ├── gripper/holding                     #   grasp-hold feedback (std_msgs/Bool)
│   ├── basket/occupied                     #   basket presence, Stage 2 (std_msgs/Bool)
│   └── cmd_vel
/tf
/clock
```

### Handshake (session authentication)

Registration is a challenge-response handshake. The long-term secret, the team token, is
**never sent on the wire**; you prove possession with an HMAC and receive an expiring
`session_key`.

```
HELLO (100)  -> CHALLENGE (410) -> PROOF (101) -> SESSION_ACK (400)
participant     platform           participant     platform
```

1. HELLO (msg 100) `/marc/ops/register` — `{ team_id, team, client_nonce }`.
2. CHALLENGE (msg 410) `.../response` — `{ server_nonce, ttl, alg: "HMAC-SHA256" }`.
3. PROOF (msg 101) `/marc/ops/register` — `proof = HMAC-SHA256(token, "server_nonce|client_nonce|team_id")`.
4. SESSION_ACK (msg 400) `.../response` — `{ status: "ok", session_key, expires_at }`.

After ACK, every `request` message carries the issued `session_key` in `header.session`. The
token value and how it is derived are not published here — you receive your token out of
band. The SDK performs the whole handshake for you in `connect()`.

### Message header

Every operations message has the structure `{ "header": {...}, "payload": {...} }`.

| Field | Type | Required on | Description |
|---|---|---|---|
| `msg` | int | all | Message type id |
| `timestamp` | float | all | Publish time (Unix epoch, seconds) |
| `seq` | int | request, response | Request/response pairing key; monotonically increasing per session (replay defense) |
| `session` | string | request only | The issued `session_key` (not the static token) |

### Control topics

- `cmd_vel` — `geometry_msgs/Twist`
  - Topic: `/marc/{team_id}/robot/cmd_vel`
  - `linear.x` (`float`, m/s) — forward/back (+ = forward)
  - `linear.y` (`float`, m/s) — lateral (+ = left)
  - `angular.z` (`float`, rad/s) — yaw (+ = counter-clockwise)
  - Constraints: motion plane XY (2D), frame Z-up right-handed (REP-103), max linear speed
    1.5 m/s / max angular speed 1.0 rad/s
  - Note: `linear.z`, `angular.x`, `angular.y` are unused.
- `arm/joint_command` — `sensor_msgs/JointState`
  - Topic: `/marc/{team_id}/robot/arm/joint_command`
  - DoF: 6 (`joint_1`..`joint_6`), control mode = position target (radians)
  - State publish: on `arm/joint_states`, per physics step (nominal 20 Hz). The actual
    delivery rate can drop with the run machine's real-time factor, so advance your control
    loop with the arrival of this state feedback rather than on a fixed period.
  - Note: a 6-DoF (non-redundant) manipulator + Robotiq 2F-140 gripper; reach comes from
    base + arm coordination. See the [Technical Guide -> Manipulation learning kit](technical-guide.md).
- `gripper/holding` — `std_msgs/Bool` (published by the platform)
  - Topic: `/marc/{team_id}/robot/gripper/holding`
  - Meaning: `true` if the gripper is holding an object. Isomorphic to the object detection of
    a real Robotiq 2F-140: if a close command is blocked by an object and cannot close to the
    target angle, it is `true`. Used to detect a failed pick or a drop in transit and retry
    (SDK `is_grasping()`).
- `basket/occupied` — `std_msgs/Bool` (published by the platform, Stage 2)
  - Topic: `/marc/{team_id}/robot/basket/occupied`
  - Meaning: `true` if an object is currently in the rear basket. Like a real basket-load
    sensor, it is a generic signal that only tells you "whether something is loaded" and does
    not expose correctness or score. Used to confirm delivery success and retry (SDK
    `is_basket_occupied()`).

### Sensor topics

- CCTV (environment)
  - `/marc/env/cctv/{id}/image` — `sensor_msgs/Image`, RGB (`rgb8`)
  - `/marc/env/cctv/{id}/info` — `sensor_msgs/CameraInfo`, intrinsics (K)
  - Properties: resolution 1280 x 720 (HD, 16:9), `frame_id` = `{camera_id}`
  - Note: discover available ids by listing topics under `/marc/env/cctv/`.
- Robot stereo cameras
  - There is a stereo camera on each of the base (`base_camera/`, driving + search) and the
    gripper (`gripper_camera/`, close-range pick-and-place).
  - Each camera: `left`/`right` RGB (`rgb8`), `depth/image` (`32FC1`, m), `points`
    (`sensor_msgs/PointCloud2`)
- Map
  - `/marc/env/map/occupancy` — `nav_msgs/OccupancyGrid`, static 2D grid, latched
  - `/marc/env/map/metadata` — `nav_msgs/MapMetaData`, resolution, origin, size
  - Note: the occupancy map contains **drivable road only**. People and landmarks are not in
    the map (detect them with sensors); frame `map`, Z-up, metres.

Other robot sensors (all under `/marc/{team_id}/robot/`):

| Topic | Type | Rate (nominal) |
|---|---|---|
| `odom` | `nav_msgs/Odometry` | 20 Hz |
| `imu` | `sensor_msgs/Imu` | 20 Hz |
| `lidar/scan` | `sensor_msgs/LaserScan` | — |
| `arm/joint_states` | `sensor_msgs/JointState` | 20 Hz |
| `gripper/holding` | `std_msgs/Bool` | 20 Hz |
| `basket/occupied` | `std_msgs/Bool` | 20 Hz (Stage 2) |

```{note}
The rates in the table are the **nominal physics-step rate (20 Hz)**. State topics are
published every simulation step, so if the run machine cannot keep up with real time (e.g.
with the GUI on or low GPU performance) the actual delivery rate can be lower. Write your
control and decision logic to act as messages arrive, not assuming a fixed rate.
```

```{note}
The exact lidar range/FOV/rate and the stereo resolution/baseline are published with the
frozen release once the robot USD asset is finalized.
```

### TF / coordinate frames

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
Mission areas are computed by projecting each camera ray onto a per-camera ground plane
(`z = ground_height`). They are not treated as one global plane over the whole background —
there is roughly a 10 cm step between road and grass, so account for the relevant ground
height when back-projecting CCTV pixels to world coordinates.
```

### QoS profiles

| Topic class | Reliability | Durability | History | Depth |
|---|---|---|---|---|
| Operations (JSON), `cmd_vel`, `joint_command`, TF, Clock | RELIABLE | VOLATILE | KEEP_LAST | 10 |
| `{team_id}/response`, map (occupancy) | RELIABLE | TRANSIENT_LOCAL | KEEP_LAST | 10 |
| Sensor images | BEST_EFFORT | VOLATILE | KEEP_LAST | 1 |

`TRANSIENT_LOCAL` lets a late joiner still receive the `SESSION_ACK` and the latched map.

### Message dictionary

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

Competition states (msg 202): `READY` -> `STAGE1_RUN` -> `STAGE2_RUN` -> `FINISHING` ->
`FINISHED`.

### Grounding payload (msg 301 / 311)

Single-target model. `target_type` is a single string; the coordinates are a single 3D point.
With the SDK, the `GroundingResult` (see "Data types" above) is serialized into this payload.

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
| `interpretation.target_type` | Single object type. Person problems use `"person"` |
| `interpretation.landmark` | Reference landmark name (when a relation is involved) |
| `interpretation.relation` | Spatial relation (`near`, `beside`, `behind`, `front`, `left`, `right`, `on`, `above`) — for lost-item relation problems |
| `interpretation.situation` | Situation category (`accident`, `emergency`, `abnormal`, `normal`) — for SAR person problems |
| `grounding.anchor_coord` | Estimated landmark coordinate `[x, y, z]` (m) |
| `grounding.target_coord` | Estimated target coordinate `[x, y, z]` (m) |
