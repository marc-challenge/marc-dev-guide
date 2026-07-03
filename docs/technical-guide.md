# Technical Guide

This page covers the **`marc_sdk`** client API and the **baseline (demo) agent**, plus the
optional **manipulation learning kit**. The SDK hides the ROS 2 protocol so you can focus on
your VLA and navigation logic. For raw topic details see the
[API Reference](api-reference.md).

---

## SDK reference (`marc_sdk`)

### Install and initialize

```bash
# Standard (Docker submission): marc_sdk ships as SOURCE — your image COPYs it and adds
#   it to PYTHONPATH (see demo/Dockerfile). No pip step needed.
# Host-side / local dev only (ROS2 Humble sourced): install from the starter-kit ROOT —
pip install -e .                                   # run where pyproject.toml lives (kit root), NOT inside marc_sdk/
# or the release wheel:
pip install marc_sdk-2026.1.0-py3-none-any.whl     # attached to the marc-starter-kit GitHub Release (not published to PyPI)
```

```python
from marc_sdk import MARCClient

client = MARCClient.from_env()   # reads MARC_TEAM_ID / MARC_TOKEN
client.connect()                 # handshake (HELLO -> CHALLENGE -> PROOF -> ACK), automatic
```

`connect()` runs the full challenge-response handshake and starts a background executor.
The token is used only as an HMAC key and is never transmitted.

### Callback model

Register handlers with decorators; they fire on the executor thread.

| Decorator | Fires on | Signature |
|---|---|---|
| `@client.on_mission` | Stage 1 mission (msg 201) | `fn(mission)` |
| `@client.on_stage2_mission` | Stage 2 mission (msg 211) | `fn(mission)` |
| `@client.on_stage2_run` | Stage 2 driving begins | `fn()` (runs in its own thread; loop on `client.is_running`) |
| `@client.on_state_change` | state transition (msg 202) | `fn(old, new)` |
| `@client.on_time_remaining` | time tick (msg 203) | `fn(remaining)` |
| `@client.on_score` | score result (msg 401) | `fn(score)` |
| `@client.on_warning` | warning (msg 502) | `fn(type, message)` |

### Sensor getters

All getters return the latest cached ROS 2 message (thread-safe), or `None`.

```python
client.list_cctv()                       # discovered CCTV ids
client.get_cctv_image(camera_id)         # sensor_msgs/Image
client.get_cctv_info(camera_id)          # sensor_msgs/CameraInfo
client.get_robot_image("base_left")      # base_left/right, gripper_left/right
client.get_robot_depth("base")           # base / gripper (32FC1)
client.get_lidar()                       # sensor_msgs/LaserScan
client.get_odom(); client.get_imu()
client.get_arm_state()                   # sensor_msgs/JointState
client.get_occupancy_map()               # nav_msgs/OccupancyGrid
client.get_world_pose()                  # (x, y, yaw_rad) — same frame as target_coord
```

### Control

```python
client.send_cmd_vel(linear_x=0.3, angular_z=0.2)   # max 1.5 m/s, 1.0 rad/s
client.stop()
client.send_arm_command(joint_state)               # sensor_msgs/JointState passthrough
```

### Submission API

```python
client.submit_grounding(result)            # Stage 1 (msg 301)
client.submit_stage2_grounding(result)     # Stage 2 interpretation (msg 311)
client.task_complete()                      # Stage 2 collection done (msg 302) — irreversible
```

`result` may be a `GroundingResult`, a `dict`, or keyword arguments
(`camera_id`, `target_type`, `landmark`, `anchor_coord`, `target_coord`, `relation`,
`situation`). Lost-and-found problems use `relation`; SAR person problems use `situation`.

### Minimal agent

```python
from marc_sdk import MARCClient

client = MARCClient.from_env()
client.connect()

@client.on_mission
def stage1(mission):
    client.submit_grounding(my_vla.process(mission))

@client.on_stage2_mission
def stage2_interpret(mission):
    client.submit_stage2_grounding(my_vla.process(mission))

@client.on_stage2_run
def drive():
    while client.is_running:
        twist = my_nav.compute(client.get_world_pose(), client.get_occupancy_map())
        client.send_cmd_vel(**twist)
    client.task_complete()

client.run()
```

---

## Baseline agent (demo)

The demo (`demo/`, at the starter-kit root) is a complete, non-interactive agent you can
run, read, and replace piece by piece.

| File | Role |
|---|---|
| `participant_app.py` | Wires the full Stage 1 / Stage 2 flow via `MARCClient` handlers. |
| `mock_vla.py` | **Mock VLA grounding** — keyword matching; you replace this with your model. |
| `occupancy_planner.py` | Occupancy-grid **A\*** path planner (`get_occupancy_map()` input). |
| `nav.py` | Waypoint-follow controller producing `(linear_x, angular_z)`. |

Flow:

1. **Register** -> `SESSION_ACK`.
2. **Stage 1**: per-round `voice_command` -> mock VLA -> `submit_grounding()`.
3. **Stage 2**: `task_description` -> mock VLA -> `submit_stage2_grounding()` -> occupancy
   A\* plan -> waypoint follow (`cmd_vel`), replan on stall, stop on arrival/timeout ->
   `task_complete()`. The Stage 2 destination is referred to as the **designated location**.

```{admonition} Replace the mock VLA
:class: important
`mock_vla.py` is a placeholder — you must **replace it with your own VLA grounding**. Any
ground-truth hard-coding in the demo's mock VLA is a **demo-only convenience**; in the real
separate-hardware submission environment there is no ground-truth access at runtime.
```

```{admonition} Navigation needs no learning environment
:class: note
Obstacles are static (people do not move), so standard ROS 2 navigation suffices: global
occupancy planning + lidar-based local avoidance. The occupancy map contains drivable road
only; detect people and landmarks with sensors.
```

---

## Manipulation learning kit

Pick-and-place is controlled at the **joint-angle level only** — you compute the joint
targets that place the gripper on the object. To lower the barrier, the organizers provide a
baseline plus a learning kit (**Option B**). Ground truth is **not** delivered at runtime;
labels are provided **offline for training only**.

What is provided:

- **FK/IK reference** — dependency-free numpy implementation
  (`manipulation/fk_ik.py`). (Real-time placo IK is environment-dependent and not shipped
  to participants.)
- **Motion primitives** — pick sequence with speed limits (`manipulation/arm_pick.py`,
  reused by `demo/arm_pick.py`).
- **Working baseline pick-and-place** that already earns partial score
  (`manipulation/arm_pick.py`).
- **LeRobot demo dataset** — teleoperation (observation, action) episodes for
  imitation-learning / VLA cold-start (LeRobot format).
- **`manipulation_trainer`** — a sibling of the perception trainer that applies robot joint
  actions and provides success/reward and `reset()/step()` on a domain-randomized practice
  scene (both trainers ship as **two entry points of one trainer image**, excluded from the
  competition runtime).

```{note}
The robot is a **mobile manipulator**: a 6-DoF arm (`joint_1`..`joint_6`) + Robotiq 2F-140
gripper on a 4-wheel-steer chassis. Reach comes from base + arm coordination — the arm alone
is non-redundant. Dataset size, simulator-wrapper scope, and IK distribution policy are
still under review.
```

This year, sim2real is **direction-only**: the design stays transfer-compatible
(joint-space control, realistic sensor observations) but rigorous domain randomization and
high-performance RL are out of scope.
