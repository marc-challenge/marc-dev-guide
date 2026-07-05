# API 레퍼런스

이 페이지는 참가자가 참조하는 인터페이스의 단일 출처(SSoT)이며, 두 계층으로 나뉩니다.

- marc_sdk 파이썬 API — 대부분의 참가자가 직접 호출하는 계층입니다. 클라이언트 생성·연결,
  콜백, 센서 조회, 로봇 제어, 정답 제출, 그리고 주고받는 데이터 타입을 다룹니다.
- ROS 2 인터페이스 — 그 아래에서 실제로 오가는 토픽·메시지·QoS·좌표계입니다. SDK 를 쓰면
  대부분 직접 다룰 일이 없지만, 저수준으로 접근하거나 규격을 확인할 때 참조합니다.

두 계층 모두 같은 형식으로 적었습니다. 각 항목은 **이름 → 시그니처 또는 타입 → 파라미터·필드(자료형과
의미) → 반환·비고** 순서이며, 여러 항목을 한눈에 보는 색인은 표로 정리했습니다.

SDK 를 준비하고 클라이언트를 만드는 기본 사용법은 [기술 가이드](technical-guide.md)에서 먼저 설명합니다.

---

## marc_sdk

`marc_sdk` 의 중심은 `MARCClient` 하나입니다. 플랫폼과 주고받는 ROS 2 통신 — 등록 핸드셰이크, 메시지
종류 구분, 세션·순번 관리, QoS, CCTV 카메라 자동 탐색 — 을 `MARCClient` 가 안에서 대신 처리합니다.
아래는 그 공개 API 전체 레퍼런스입니다(정본: `marc_sdk/client.py`·`types.py`).

### 클라이언트 생성 · 연결

- `MARCClient.from_env(**kwargs) -> MARCClient`
  - 파라미터: 환경변수 `MARC_TEAM_ID` / `MARC_TOKEN` 에서 팀 ID 와 인증 토큰을 읽습니다. 추가 키워드
    인자는 `MARCClient(...)` 로 그대로 전달됩니다.
  - 반환: 초기화된 `MARCClient`. 환경변수 대신 `MARCClient(team_id=..., token=...)` 로 직접 만들 수도 있습니다.
- `connect(timeout=30.0, register_period=2.0) -> bool`
  - `timeout` (`float`, 기본 `30.0`) — `SESSION_ACK` 를 기다리는 최대 시간(초)
  - `register_period` (`float`, 기본 `2.0`) — 등록 재시도 주기(초)
  - 동작: rclpy 초기화 → 노드/펍·섭 생성 → challenge-response 핸드셰이크(HELLO → CHALLENGE → PROOF → ACK)
    → 백그라운드 executor 기동.
  - 반환: 인증에 성공하면 `True`.
- `run()`
  - 파라미터: 없음
  - 동작: 노드를 spin 하며 메인 스레드를 블록합니다(Ctrl-C 로 종료). 콜백은 백그라운드 executor 스레드에서 호출됩니다.
- `shutdown()`
  - 파라미터: 없음
  - 동작: 정지 명령을 보낸 뒤 노드/executor 를 정리합니다(중복 호출에 안전).
- `is_running` (property, `bool`)
  - Stage 2 주행 구간 동안 `True`. `on_stage2_run` 루프의 종료 조건으로 씁니다.
- `stage2_reveal` (property)
  - 가장 최근 Stage 2 reveal(`Stage2Reveal` 또는 `None`). `on_stage2_reveal` 대신 폴링으로 확인할 때 씁니다.

### 콜백

플랫폼과 SDK 가 통신하는 동안, 에이전트가 어떤 행동을 해야 하는 순간(예: 새 미션 도착)이나 에이전트에게
실시간 정보를 전달해야 하는 순간(예: 남은 시간·상태 변화·채점 결과)이 생깁니다. 각 이벤트에 대응하는
데코레이터에 콜백 함수를 등록해 두면, 그 이벤트가 일어날 때 SDK 가 등록된 콜백을 자동으로 호출합니다.
콜백은 백그라운드 executor 스레드에서 호출됩니다.

| 데코레이터 | 요약 |
|---|---|
| `@client.on_mission` | Stage 1 라운드 문제 출제 |
| `@client.on_stage2_mission` | Stage 2 문제 출제 |
| `@client.on_stage2_run` | Stage 2 주행 시작 |
| `@client.on_stage2_reveal` | Stage 2 grounding 채점 결과 공개 |
| `@client.on_state_change` | 대회 상태 전이 |
| `@client.on_time_remaining` | 남은 시간 갱신 |
| `@client.on_time_expired` | 제한 시간 만료 |
| `@client.on_transition` | 스테이지 전환 |
| `@client.on_score` | 채점 결과 |
| `@client.on_warning` | 경고 |

각 콜백을 (발화 시점 / 시그니쳐 / 콜백 안에서 할 일) 로 정리하면 다음과 같습니다. 시그니쳐는 등록한
콜백 함수가 받는 인자이며, 하위 항목은 각 인자(또는 그 필드)의 자료형과 의미입니다.

**미션 처리**

- `on_mission`
  - 발화: 플랫폼에서 Stage 1 의 매 라운드 문제를 출제할 때 (msg 201)
  - 시그니쳐: `fn(mission)`
    - `mission.voice_command` (`str`) — 처리할 사람의 자연어 명령
    - `mission.round` (`int`) — 현재 라운드 번호
    - `mission.total_rounds` (`int`) — Stage 1 전체 라운드 수
    - `mission.time_limit` (`float`) — 이 라운드 제한 시간(초)
  - 구현: 음성 명령을 해석해 대상을 찾고 `submit_grounding()` 으로 제출
- `on_stage2_mission`
  - 발화: 플랫폼에서 Stage 2 문제를 출제할 때 (msg 211)
  - 시그니쳐: `fn(mission)`
    - `mission.task_description` (`str`) — 처리할 작업 명령
    - `mission.time_limit` (`float`) — 제한 시간(초)
    - `mission.owner_position` (`list[float]` 또는 `None`) — 물건을 가져다 둘 위치 `[x, y, z]`(owner_zone 이 없으면 `None`)
  - 구현: 명령을 해석해 대상을 찾고 `submit_stage2_grounding()` 으로 제출
- `on_stage2_reveal`
  - 발화: Stage 2 grounding 채점 직후 (msg 411)
  - 시그니쳐: `fn(reveal)`
    - `reveal.grounding_score` (`float`) — 이번 grounding 제출의 점수(0–100)
    - `reveal.target_type` (`str`) — 집어야 할 물건의 종류
    - `reveal.hint_center` (`list[float]`) — 대상의 대략 위치 중심 `[x, y, z]`(정확한 정답 아님)
    - `reveal.hint_radius` (`float`) — 대략 위치 반경(m)
  - 구현: 반경 안의 후보 중 `reveal.target_type` 으로 물건을 고르고, 이 위치를 목표로 수거 준비(`client.stage2_reveal` 프로퍼티로 폴링도 가능)
  - 비고: Stage 2 grounding 을 **틀리게 제출했더라도** 플랫폼이 대략적인 정답 위치를 알려 주어 navigation 과 pick & place 를 이어갈 수 있도록 고안된 방식입니다. 덕분에 grounding 정확도와 무관하게 수거·전달 능력을 평가받을 수 있습니다.
- `on_stage2_run`
  - 발화: Stage 2 주행 단계에 진입할 때(별도 스레드)
  - 시그니쳐: `fn()` — 인자 없음
  - 구현: `client.is_running` 이 참인 동안 루프를 돌며 내비게이션·집기·전달, 마치면 `task_complete()` 호출

**상태 · 시간 알림**

- `on_state_change`
  - 발화: 대회 상태가 바뀔 때 (msg 202)
  - 시그니쳐: `fn(old, new)`
    - `old` (`str`) — 이전 상태
    - `new` (`str`) — 다음 상태 (`READY` → `STAGE1_RUN` → `STAGE2_RUN` → `FINISHING` → `FINISHED`)
  - 구현: 상태에 맞춰 내부 로직 초기화·전환
- `on_transition`
  - 발화: 스테이지 전환 알림 시 (msg 501)
  - 시그니쳐: `fn(from_state, to_state)`
    - `from_state` (`str`) — 전환 전 상태
    - `to_state` (`str`) — 전환 후 상태
  - 구현: 전환 시점 처리(`on_state_change` 와 유사)
- `on_time_remaining`
  - 발화: 남은 시간이 주기적으로 갱신될 때 (msg 203)
  - 시그니쳐: `fn(remaining)`
    - `remaining` (`float`) — 남은 시간(초)
  - 구현: 시간에 따라 전략 조절(예: 시간이 얼마 없으면 서두르기)
- `on_time_expired`
  - 발화: 제한 시간이 끝났을 때 (msg 204)
  - 시그니쳐: `fn(which)`
    - `which` (`str`) — 끝난 시간의 종류(`'stage1'` / `'total'`)
  - 구현: 진행 중이던 작업 정리·중단

**결과 · 경고**

- `on_score`
  - 발화: 채점 결과가 도착할 때 (msg 401)
  - 시그니쳐: `fn(score)`
    - `score.total` (`float`) — 합계 점수
    - `score.scores` (`dict`) — 세부 점수 항목
    - `score.is_final` (`bool`) — 최종 결과 여부(라운드 점수면 `False`)
    - `score.round` (`int` 또는 `None`) — 라운드 번호(최종 결과면 `None`)
  - 구현: 점수 확인·기록
- `on_warning`
  - 발화: 플랫폼이 경고를 보낼 때 (msg 502)
  - 시그니쳐: `fn(type, message)`
    - `type` (`str`) — 경고 유형
    - `message` (`str`) — 경고 메시지
  - 구현: 경고 유형·메시지 기록 또는 대응

### 센서 조회

플랫폼이 발행하는 센서 데이터는 아래 함수로 조회합니다. 모든 함수는 가장 최근에 받은 ROS 2 메시지를
그대로 반환하며(thread-safe), 아직 받은 값이 없으면 `None` 을 반환합니다.

| 함수 | 요약 |
|---|---|
| `list_cctv()` | 사용 가능한 CCTV id 목록 |
| `get_cctv_image(camera_id)` | CCTV RGB 영상 |
| `get_cctv_info(camera_id)` | CCTV 내부 파라미터 |
| `get_robot_image(which)` | 로봇 카메라 RGB 영상 |
| `get_robot_depth(which)` | 로봇 카메라 깊이 영상 |
| `get_lidar()` | 로봇 라이다 스캔 |
| `get_odom()` | 로봇 오도메트리 |
| `get_imu()` | 로봇 IMU |
| `get_arm_state()` | 로봇팔 관절 상태 |
| `get_occupancy_map()` | 점유 격자 지도 |
| `get_world_pose()` | 로봇 위치·방향 |
| `subscribe(topic, msg_type, callback, qos)` | 임의 토픽 직접 구독 |

- `list_cctv() -> list[str]`
  - 파라미터: 없음
  - 반환: 탐색된 CCTV 카메라 id 목록. 이 id 를 아래 두 함수에 넘깁니다.
- `get_cctv_image(camera_id: str) -> sensor_msgs/Image | None`
  - `camera_id` (`str`) — 조회할 CCTV id (`list_cctv()` 로 확인)
  - 반환: 해당 카메라의 최신 RGB 프레임(인코딩 `rgb8`). VLA 인지의 주 입력.
- `get_cctv_info(camera_id: str) -> sensor_msgs/CameraInfo | None`
  - `camera_id` (`str`) — 조회할 CCTV id
  - 반환: 해당 카메라의 내부 파라미터(투영 행렬 K 등). 픽셀↔3D 변환에 사용.
- `get_robot_image(which: str = "base_left") -> sensor_msgs/Image | None`
  - `which` (`str`, 기본값 `"base_left"`) — 로봇 카메라 위치. `base_left`·`base_right`·`gripper_left`·`gripper_right` 중 하나(그 외 값은 `ValueError`).
  - 반환: 해당 카메라의 최신 RGB 영상(`rgb8`).
- `get_robot_depth(which: str = "base") -> sensor_msgs/Image | None`
  - `which` (`str`, 기본값 `"base"`) — 깊이 카메라 계열. `base`·`gripper` 중 하나(그 외 값은 `ValueError`).
  - 반환: 해당 카메라의 깊이 영상(`32FC1`, 픽셀 값 = 미터 거리).
- `get_lidar() -> sensor_msgs/LaserScan | None`
  - 파라미터: 없음
  - 반환: 로봇 2D 라이다 스캔. 근접 장애물 회피에 사용.
- `get_odom() -> nav_msgs/Odometry | None`
  - 파라미터: 없음
  - 반환: 로봇 오도메트리(위치·속도).
- `get_imu() -> sensor_msgs/Imu | None`
  - 파라미터: 없음
  - 반환: 관성 센서 값(자세·각속도·가속도).
- `get_arm_state() -> sensor_msgs/JointState | None`
  - 파라미터: 없음
  - 반환: 로봇팔의 현재 관절 상태(관절 각도 등).
- `get_occupancy_map() -> nav_msgs/OccupancyGrid | None`
  - 파라미터: 없음
  - 반환: 정적 2D 점유 격자(주행 가능 도로만). 경로 계획의 입력.
- `get_world_pose() -> tuple[float, float, float] | None`
  - 파라미터: 없음
  - 반환: 로봇의 월드 좌표·방향 `(x, y, yaw_rad)`. 제출 좌표 `target_coord` 와 같은 좌표계이며 Stage 2 주행의 위치 피드백.
- `subscribe(topic: str, msg_type, callback, qos=None)`
  - `topic` (`str`) — 구독할 ROS 2 토픽 이름
  - `msg_type` — 메시지 타입 클래스(예: `sensor_msgs.msg.Image`)
  - `callback` — 메시지 수신 시 호출할 함수 `fn(msg)`
  - `qos` (기본값 `None`) — QoS 프로파일. `None` 이면 기본(RELIABLE)
  - 반환: rclpy 구독 객체(`rclpy.subscription.Subscription`)
  - 비고: 위 함수로 부족할 때 임의 토픽을 직접 구독하는 escape hatch.

### 로봇 제어

로봇 본체 이동과 로봇팔을 제어합니다.

| 함수 | 요약 |
|---|---|
| `send_cmd_vel(linear_x, linear_y, angular_z)` | 본체 이동 명령 |
| `stop()` | 본체 정지 |
| `send_arm_command(joint_state)` | 로봇팔 관절 명령 |

- `send_cmd_vel(linear_x=0.0, linear_y=0.0, angular_z=0.0, twist=None)`
  - `linear_x` (`float`, 기본 `0.0`) — 전/후진 속도(m/s, +가 전진)
  - `linear_y` (`float`, 기본 `0.0`) — 좌/우 횡이동 속도(m/s, +가 좌)
  - `angular_z` (`float`, 기본 `0.0`) — 회전 속도(rad/s, +가 반시계)
  - `twist` (`geometry_msgs/Twist`, 기본 `None`) — 주어지면 이 Twist 를 그대로 발행하고 위 세 인자는 무시
  - 반환: 없음
  - 비고: 허용 최대 1.5 m/s / 1.0 rad/s. SDK 가 초과 입력을 자동으로 제한하지 않으므로 에이전트가 직접 지켜야 함.
- `stop()`
  - 파라미터: 없음
  - 동작: 본체를 즉시 정지(`cmd_vel` 0 발행)
  - 반환: 없음
- `send_arm_command(joint_state)`
  - `joint_state` (`sensor_msgs/JointState`) — 로봇팔 목표 관절 상태(6축 관절 각도)
  - 동작: 로봇팔 관절 명령 토픽으로 그대로 발행(passthrough)
  - 반환: 없음

### 정답 제출

Stage 1·2 의 답안을 제출하고, Stage 2 수거 완료를 알립니다. grounding 답안은 오직 `GroundingResult`
타입으로 넘깁니다(아래 "데이터 타입" 참조).

| 함수 | 요약 |
|---|---|
| `submit_grounding(result)` | Stage 1 grounding 제출 (msg 301) |
| `submit_stage2_grounding(result)` | Stage 2 해석 제출 (msg 311) |
| `task_complete()` | Stage 2 수거 완료 (msg 302) |

- `submit_grounding(result: GroundingResult) -> int`
  - `result` (`GroundingResult`) — 제출할 grounding 결과. **오직 `GroundingResult` 만 받습니다**. payload dict 를 이미 가지고 있다면 `GroundingResult.from_payload(payload)` 로 변환해 넘깁니다.
  - 동작: Stage 1 grounding 답안 제출(msg 301)
  - 반환: 부여된 요청 순번 `seq` (`int`)
- `submit_stage2_grounding(result: GroundingResult) -> int`
  - 파라미터: `submit_grounding` 과 동일(`GroundingResult`)
  - 동작: Stage 2 해석 답안 제출(msg 311)
  - 반환: `seq` (`int`)
- `task_complete() -> int`
  - 파라미터: 없음
  - 동작: Stage 2 수거 완료 발행(msg 302). 호출 즉시 종료 단계로 전환되며 취소 불가.
  - 반환: `seq` (`int`)

### 데이터 타입

콜백 인자와 제출 결과로 오가는 데이터 타입입니다(정본: `marc_sdk/types.py`). `from marc_sdk import
GroundingResult` 로 가져옵니다.

- `GroundingResult` — 참가자가 만들어 제출하는 grounding 결과.
  - `camera_id` (`str`) — 대상이 보이는 CCTV id
  - `target_type` (`str`) — 대상의 종류(사람 문제는 `"person"`)
  - `anchor_coord` (`list[float]`) — 기준 랜드마크 추정 좌표 `[x, y, z]`
  - `target_coord` (`list[float]`) — 대상 추정 좌표 `[x, y, z]`
  - `landmark` (`str`, 기본 `""`) — 기준 랜드마크 이름(공간 관계가 있을 때)
  - `relation` (`str`, 기본 `None`) — 공간 관계(분실물 관계 문제에서 사용)
  - `situation` (`str`, 기본 `None`) — 상황 카테고리(SAR 사람 문제에서 사용)
  - 메서드: `GroundingResult.from_payload(payload: dict) -> GroundingResult`(payload dict 로부터 생성), `to_payload() -> dict`(제출 payload 로 직렬화)
- `Mission` — `on_mission` 인자. 필드: `voice_command`(`str`) · `round`(`int`) · `total_rounds`(`int`) · `time_limit`(`float`).
- `Stage2Mission` — `on_stage2_mission` 인자. 필드: `task_description`(`str`) · `time_limit`(`float`) · `owner_position`(`list[float]` 또는 `None`).
- `Stage2Reveal` — `on_stage2_reveal` 인자. 필드: `grounding_score`(`float`) · `target_type`(`str`) · `hint_center`(`list[float]`) · `hint_radius`(`float`).
- `Score` — `on_score` 인자. 필드: `total`(`float`) · `scores`(`dict`) · `is_final`(`bool`) · `round`(`int` 또는 `None`) · `stage`(`str`).

---

## ROS 2

플랫폼과 에이전트는 전적으로 ROS 2 로 통신합니다. `marc_sdk` 가 이 계층을 감싸 주므로 보통 직접 다룰
일은 없지만, 저수준으로 접근하거나 규격을 확인할 때 이 절을 참조합니다. 전송은 두 계열입니다.

- 운영(`/marc/ops/...`) — `header` / `payload` 구조와 숫자 `msg` id 를 담은 JSON 을 실은
  `std_msgs/String`. 세션·미션·제출·채점.
- 센서 / 제어 — 전용 토픽의 ROS 2 표준 메시지(Image, CameraInfo, Twist, JointState,
  LaserScan, OccupancyGrid, TF).

### 네임스페이스

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
│   └── cmd_vel
/tf
/clock
```

### 핸드셰이크 (세션 인증)

등록은 challenge-response 핸드셰이크입니다. 장기 비밀인 팀 토큰은 **와이어에 절대 전송하지
않으며**, HMAC 증명으로 소유를 입증하고 만료형 `session_key` 를 발급받습니다.

```
HELLO (100)  -> CHALLENGE (410) -> PROOF (101) -> SESSION_ACK (400)
participant     platform           participant     platform
```

1. HELLO (msg 100) `/marc/ops/register` — `{ team_id, team, client_nonce }`.
2. CHALLENGE (msg 410) `.../response` — `{ server_nonce, ttl, alg: "HMAC-SHA256" }`.
3. PROOF (msg 101) `/marc/ops/register` — `proof = HMAC-SHA256(token, "server_nonce|client_nonce|team_id")`.
4. SESSION_ACK (msg 400) `.../response` — `{ status: "ok", session_key, expires_at }`.

ACK 이후 모든 `request` 메시지는 발급받은 `session_key` 를 `header.session` 에 싣습니다. 토큰 값과
그 도출 방식은 여기에 공개하지 않습니다 — 토큰은 별도 경로로 전달받습니다. SDK 가 `connect()` 에서
전체 핸드셰이크를 대행합니다.

### 메시지 헤더

모든 운영 메시지는 `{ "header": {...}, "payload": {...} }` 구조입니다.

| 필드 | 타입 | 필수 | 설명 |
|---|---|---|---|
| `msg` | int | 전체 | 메시지 유형 id |
| `timestamp` | float | 전체 | 발행 시각(Unix epoch, 초) |
| `seq` | int | request, response | request/response 페어링 키; 세션 내 단조 증가(재전송 방어) |
| `session` | string | request만 | 발급받은 `session_key`(정적 토큰 아님) |

### 제어 토픽

- `cmd_vel` — `geometry_msgs/Twist`
  - 토픽: `/marc/{team_id}/robot/cmd_vel`
  - `linear.x` (`float`, m/s) — 전진/후진 (+ = 전진)
  - `linear.y` (`float`, m/s) — 횡이동 (+ = 좌)
  - `angular.z` (`float`, rad/s) — 회전 (+ = 반시계)
  - 제약: 이동 평면 XY(2D), 좌표계 Z-up 오른손(REP-103), 최대 선속도 1.5 m/s / 최대 각속도 1.0 rad/s
  - 비고: `linear.z`, `angular.x`, `angular.y` 는 사용하지 않습니다.
- `arm/joint_command` — `sensor_msgs/JointState`
  - 토픽: `/marc/{team_id}/robot/arm/joint_command`
  - DoF: 6 (`joint_1`..`joint_6`), 제어 모드 = 위치 target(radian)
  - 상태 발행: `arm/joint_states` 로 60 Hz(물리 스텝 동기)
  - 비고: 6-DoF(비여유) 매니퓰레이터 + Robotiq 2F-140 그리퍼이며, 도달성은 본체+팔 협응에서 나옵니다. [기술 가이드 → 매니퓰레이션 학습 키트](technical-guide.md)를 참조하십시오.

### 센서 토픽

- CCTV (환경)
  - `/marc/env/cctv/{id}/image` — `sensor_msgs/Image`, RGB(`rgb8`)
  - `/marc/env/cctv/{id}/info` — `sensor_msgs/CameraInfo`, intrinsic(K)
  - 속성: 해상도 1280 x 720(HD, 16:9), `frame_id` = `{camera_id}`
  - 비고: 사용 가능한 id 는 `/marc/env/cctv/` 하위 토픽을 조회하여 확인합니다.
- 로봇 스테레오 카메라
  - 본체(`base_camera/`, 주행 + 탐색)와 그리퍼(`gripper_camera/`, 근거리 pick-and-place)에 각각 스테레오 카메라가 있습니다.
  - 각 카메라: `left`/`right` RGB(`rgb8`), `depth/image`(`32FC1`, m), `points`(`sensor_msgs/PointCloud2`)
- 지도
  - `/marc/env/map/occupancy` — `nav_msgs/OccupancyGrid`, 정적 2D 격자, latched
  - `/marc/env/map/metadata` — `nav_msgs/MapMetaData`, 해상도·원점·크기
  - 비고: 점유 지도는 **주행 가능 도로만** 담습니다. 사람·랜드마크는 지도에 없으며(센서로 감지), frame `map`, Z-up, meter 단위입니다.

기타 로봇 센서(모두 `/marc/{team_id}/robot/` 하위):

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

### TF / 좌표계

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
미션area 는 각 카메라 레이를 카메라별 지면 평면(`z = ground_height`)에 투영하여 계산합니다.
배경 전체를 하나의 평면으로 보지 않습니다 — 도로와 잔디 사이에 약 10cm 단차가 있으므로, CCTV 픽셀을
world 좌표로 역투영할 때 해당 지면 높이를 고려하십시오.
```

### QoS 프로파일

| 토픽 분류 | Reliability | Durability | History | Depth |
|---|---|---|---|---|
| 운영 (JSON), `cmd_vel`, `joint_command`, TF, Clock | RELIABLE | VOLATILE | KEEP_LAST | 10 |
| `{team_id}/response`, 지도(occupancy) | RELIABLE | TRANSIENT_LOCAL | KEEP_LAST | 10 |
| 센서 영상 | BEST_EFFORT | VOLATILE | KEEP_LAST | 1 |

`TRANSIENT_LOCAL` 은 late-joiner 도 `SESSION_ACK` 와 latched 지도를 수신하게 합니다.

### 메시지 사전

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

대회 상태 (msg 202): `READY` -> `STAGE1_RUN` -> `STAGE2_RUN` -> `FINISHING` -> `FINISHED`.

### Grounding payload (msg 301 / 311)

단일 대상 모델. `target_type` 은 단일 string, 좌표는 단일 3D 점입니다. SDK 를 쓰면 `GroundingResult`
(위 "데이터 타입")가 이 payload 로 직렬화됩니다.

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
| `interpretation.target_type` | 단일 객체 유형. 사람 문제는 `"person"` |
| `interpretation.landmark` | 기준 랜드마크 이름(관계 동반 시) |
| `interpretation.relation` | 공간 관계(`near`, `beside`, `behind`, `front`, `left`, `right`, `on`, `above`) — 분실물 관계 문제 |
| `interpretation.situation` | 상황 카테고리(`accident`, `emergency`, `abnormal`, `normal`) — SAR 사람 문제 |
| `grounding.anchor_coord` | 기준 랜드마크 추정 좌표 `[x, y, z]` (m) |
| `grounding.target_coord` | 대상 추정 좌표 `[x, y, z]` (m) |
