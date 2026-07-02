# API 레퍼런스 — ROS 2 인터페이스

플랫폼과 에이전트는 전적으로 **ROS 2(Fast DDS)** 로 통신합니다. 이 페이지는 토픽·메시지·QoS·좌표계의
단일 출처(SSoT)입니다.

두 가지 전송 계열:

- **운영(`/marc/ops/...`)** — `header` / `payload` 구조와 숫자 `msg` id 를 담은 JSON 을 실은
  `std_msgs/String`. 세션·미션·제출·채점.
- **센서 / 제어** — 전용 토픽의 ROS 2 표준 메시지(Image, CameraInfo, Twist, JointState,
  LaserScan, OccupancyGrid, TF).

---

## 네임스페이스

```
/marc/
├── ops/                                  # 운영 (JSON + msg id)
│   ├── register                          #   세션 핸드셰이크 (고정 토픽)
│   ├── announce                          #   Platform -> All (미션·상태·시간)
│   └── {team_id}/
│       ├── request                       #   Participant -> Platform
│       ├── response                      #   Platform -> Participant
│       └── notification                  #   Platform -> Participant (비동기)
├── env/                                  # 환경 (ROS 2 표준)
│   ├── cctv/{id}/image, info             #   CCTV RGB + 카메라 파라미터
│   └── map/occupancy, metadata           #   정적 2D 점유 격자
├── {team_id}/robot/                      # 팀별 로봇 센서 / 제어
│   ├── base_camera/{left,right}/image, info, depth/image, points
│   ├── gripper_camera/{left,right}/image, info, depth/image, points
│   ├── odom, imu, lidar/scan
│   ├── arm/joint_states, arm/joint_command
│   └── cmd_vel
/tf
/clock
```

---

## 핸드셰이크 (세션 인증)

등록은 **challenge-response** 핸드셰이크입니다. 장기 비밀인 팀 토큰은 **와이어에 절대 전송하지
않으며**, HMAC 증명으로 소유를 입증하고 만료형 `session_key` 를 발급받습니다.

```
HELLO (100)  -> CHALLENGE (410) -> PROOF (101) -> SESSION_ACK (400)
participant     platform           participant     platform
```

1. **HELLO (msg 100)** `/marc/ops/register` — `{ team_id, team, client_nonce }`.
2. **CHALLENGE (msg 410)** `.../response` — `{ server_nonce, ttl, alg: "HMAC-SHA256" }`.
3. **PROOF (msg 101)** `/marc/ops/register` — `proof = HMAC-SHA256(token, "server_nonce|client_nonce|team_id")`.
4. **SESSION_ACK (msg 400)** `.../response` — `{ status: "ok", session_key, expires_at }`.

ACK 이후 모든 `request` 메시지는 발급받은 `session_key` 를 `header.session` 에 싣습니다. 토큰 값과
그 도출 방식은 여기에 **공개하지 않습니다** — 토큰은 별도 경로로 전달받습니다. SDK 가 `connect()` 에서
전체 핸드셰이크를 대행합니다.

---

## 메시지 헤더

모든 운영 메시지는 `{ "header": {...}, "payload": {...} }` 구조입니다.

| 필드 | 타입 | 필수 | 설명 |
|---|---|---|---|
| `msg` | int | 전체 | 메시지 유형 id. |
| `timestamp` | float | 전체 | 발행 시각(Unix epoch, 초). |
| `seq` | int | request, response | request/response 페어링 키; 세션 내 **단조 증가**(재전송 방어). |
| `session` | string | request만 | 발급받은 `session_key`(정적 토큰 아님). |

---

## 제어 토픽

### `cmd_vel` — 본체 이동

`/marc/{team_id}/robot/cmd_vel`, 타입 `geometry_msgs/Twist`.

| 필드 | 의미 |
|---|---|
| `linear.x` | 전진/후진 (m/s), + = 전진 |
| `linear.y` | 횡이동 (m/s), + = 좌 |
| `angular.z` | 회전 (rad/s), + = 반시계 |

| 제약 | 값 |
|---|---|
| 이동 평면 | XY (2D) |
| 좌표계 | Z-up 오른손 (ROS 2 REP-103) |
| **최대 선속도** | **1.5 m/s** |
| **최대 각속도** | **1.0 rad/s** |

`linear.z`, `angular.x`, `angular.y` 는 사용하지 않습니다.

### 매니퓰레이터 — 관절 명령

`/marc/{team_id}/robot/arm/joint_command`, 타입 `sensor_msgs/JointState`.

| 속성 | 값 |
|---|---|
| DoF | **6** (`joint_1`..`joint_6`) |
| 제어 모드 | 위치 target (radian) |
| 상태 발행 주기 | **60 Hz** (물리 스텝 동기), `arm/joint_states` |

팔은 6-DoF(비여유) 매니퓰레이터 + Robotiq 2F-140 그리퍼이며, 도달성은 본체+팔 협응에서 나옵니다.
[기술 가이드 → 매니퓰레이션 키트](technical-guide.md#매니퓰레이션-학습-키트)를 참조하십시오.

---

## 센서 토픽

### CCTV (환경)

| 토픽 | 타입 | 비고 |
|---|---|---|
| `/marc/env/cctv/{id}/image` | `sensor_msgs/Image` | RGB, 인코딩 `rgb8` |
| `/marc/env/cctv/{id}/info` | `sensor_msgs/CameraInfo` | intrinsic (K) |

| 속성 | 값 |
|---|---|
| 해상도 | **1280 x 720 (HD, 16:9)** |
| `frame_id` | `{camera_id}` |

사용 가능한 id 는 `/marc/env/cctv/` 하위 토픽을 조회하여 확인합니다.

### 로봇 스테레오 카메라

본체(`base_camera/`, 주행 + 탐색)와 그리퍼(`gripper_camera/`, 근거리 pick-and-place)에 각각
스테레오 카메라가 있습니다. 각각 `left`/`right` RGB(`rgb8`), `depth/image`(`32FC1`, m),
`points`(`sensor_msgs/PointCloud2`)를 제공합니다.

### 기타 로봇 센서

| 토픽 | 타입 | 주기 |
|---|---|---|
| `odom` | `nav_msgs/Odometry` | 60 Hz |
| `imu` | `sensor_msgs/Imu` | 60 Hz |
| `lidar/scan` | `sensor_msgs/LaserScan` | — |
| `arm/joint_states` | `sensor_msgs/JointState` | 60 Hz |

```{note}
정확한 라이다 거리/FOV/주기와 스테레오 해상도/baseline 은 로봇 USD 에셋 확정 후 동결 릴리스와 함께
게시합니다.
```

### 지도

| 토픽 | 타입 | 비고 |
|---|---|---|
| `/marc/env/map/occupancy` | `nav_msgs/OccupancyGrid` | 정적 2D 격자, latched |
| `/marc/env/map/metadata` | `nav_msgs/MapMetaData` | 해상도·원점·크기 |

점유 지도는 **주행 가능 도로만** 담습니다. 사람·랜드마크는 지도에 **없으며**(센서로 감지),
frame `map`, Z-up, meter 단위입니다.

---

## TF / 좌표계

| 항목 | 규격 |
|---|---|
| 표준 | ROS 2 REP-103 |
| 축 | X=앞, Y=왼쪽, Z=위 (오른손) |
| 단위 | meter; radian(Twist), degree(YAML) |
| TF | `/tf` (`tf2_msgs/TFMessage`), parent `world` -> 로봇 prim |
| Clock | `/clock` (`rosgraph_msgs/Clock`), 시뮬레이션 시간 |

Isaac Sim 5.x 는 Z-up 오른손 좌표계라 별도 축 변환이 불필요합니다.

```{admonition} 미션area 지면 평면 가정
:class: note
미션area 는 각 카메라 레이를 **카메라별 지면 평면**(`z = ground_height`)에 투영하여 계산합니다.
배경 전체를 하나의 평면으로 보지 않습니다 — 도로와 잔디 사이에 약 10cm 단차가 있으므로, CCTV 픽셀을
world 좌표로 역투영할 때 해당 지면 높이를 고려하십시오.
```

---

## QoS 프로파일

| 토픽 분류 | Reliability | Durability | History | Depth |
|---|---|---|---|---|
| 운영 (JSON), `cmd_vel`, `joint_command`, TF, Clock | RELIABLE | VOLATILE | KEEP_LAST | 10 |
| `{team_id}/response`, 지도(occupancy) | RELIABLE | TRANSIENT_LOCAL | KEEP_LAST | 10 |
| 센서 영상 | BEST_EFFORT | VOLATILE | KEEP_LAST | 1 |

`TRANSIENT_LOCAL` 은 late-joiner 도 `SESSION_ACK` 와 latched 지도를 수신하게 합니다.

---

## 메시지 사전

| id | 이름 | 토픽 | 방향 |
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

### 대회 상태 (msg 202)

`READY` -> `STAGE1_RUN` -> `STAGE2_RUN` -> `FINISHING` -> `FINISHED`.

### Grounding payload (msg 301 / 311)

단일 대상 모델. `target_type` 은 단일 string, 좌표는 단일 3D 점입니다.

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

| 필드 | 의미 |
|---|---|
| `interpretation.target_type` | 단일 객체 유형. 사람 문제는 `"person"`. |
| `interpretation.landmark` | 기준 랜드마크 이름(관계 동반 시). |
| `interpretation.relation` | 공간 관계(`near`, `beside`, `behind`, `front`, `left`, `right`, `on`, `above`) — 분실물 관계 문제. |
| `interpretation.situation` | 상황 카테고리(`accident`, `emergency`, `abnormal`, `normal`) — SAR 사람 문제. |
| `grounding.anchor_coord` | 기준 랜드마크 추정 좌표 `[x, y, z]` (m). |
| `grounding.target_coord` | 대상 추정 좌표 `[x, y, z]` (m). |
