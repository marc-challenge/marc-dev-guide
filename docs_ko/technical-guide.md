# 기술 가이드

이 페이지는 **`marc_sdk`** 클라이언트 API 와 **베이스라인(데모) 에이전트**, 그리고 옵션인
**매니퓰레이션 학습 키트**를 다룹니다. SDK 가 ROS 2 프로토콜을 감추므로 VLA 와 navigation 로직에
집중할 수 있습니다. 토픽 상세는 [API 레퍼런스](api-reference.md)를 참조하십시오.

---

## SDK 레퍼런스 (`marc_sdk`)

### 설치 및 초기화

```bash
pip install marc-sdk==2026.1.0
```

```python
from marc_sdk import MARCClient

client = MARCClient.from_env()   # MARC_TEAM_ID / MARC_TOKEN 읽음
client.connect()                 # 핸드셰이크(HELLO -> CHALLENGE -> PROOF -> ACK) 자동
```

`connect()` 가 challenge-response 핸드셰이크 전체를 수행하고 백그라운드 executor 를 띄웁니다.
토큰은 HMAC 키로만 사용되며 전송되지 않습니다.

### 콜백 모델

데코레이터로 핸들러를 등록합니다. executor 스레드에서 호출됩니다.

| 데코레이터 | 발화 시점 | 시그니처 |
|---|---|---|
| `@client.on_mission` | Stage 1 미션 (msg 201) | `fn(mission)` |
| `@client.on_stage2_mission` | Stage 2 미션 (msg 211) | `fn(mission)` |
| `@client.on_stage2_run` | Stage 2 주행 시작 | `fn()` (별도 스레드; `client.is_running` 으로 루프) |
| `@client.on_state_change` | 상태 전이 (msg 202) | `fn(old, new)` |
| `@client.on_time_remaining` | 시간 tick (msg 203) | `fn(remaining)` |
| `@client.on_score` | 채점 결과 (msg 401) | `fn(score)` |
| `@client.on_warning` | 경고 (msg 502) | `fn(type, message)` |

### 센서 getter

모든 getter 는 최신 캐시된 ROS 2 메시지를 반환합니다(thread-safe), 없으면 `None`.

```python
client.list_cctv()                       # 탐색된 CCTV id 목록
client.get_cctv_image(camera_id)         # sensor_msgs/Image
client.get_cctv_info(camera_id)          # sensor_msgs/CameraInfo
client.get_robot_image("base_left")      # base_left/right, gripper_left/right
client.get_robot_depth("base")           # base / gripper (32FC1)
client.get_lidar()                       # sensor_msgs/LaserScan
client.get_odom(); client.get_imu()
client.get_arm_state()                   # sensor_msgs/JointState
client.get_occupancy_map()               # nav_msgs/OccupancyGrid
client.get_world_pose()                  # (x, y, yaw_rad) — target_coord 와 동일 frame
```

### 제어

```python
client.send_cmd_vel(linear_x=0.3, angular_z=0.2)   # 최대 1.5 m/s, 1.0 rad/s
client.stop()
client.send_arm_command(joint_state)               # sensor_msgs/JointState passthrough
```

### 제출 API

```python
client.submit_grounding(result)            # Stage 1 (msg 301)
client.submit_stage2_grounding(result)     # Stage 2 해석 (msg 311)
client.task_complete()                      # Stage 2 수거 완료 (msg 302) — 취소 불가
```

`result` 는 `GroundingResult`, `dict`, 또는 키워드 인자
(`camera_id`, `target_type`, `landmark`, `anchor_coord`, `target_coord`, `relation`,
`situation`)로 줄 수 있습니다. 분실물은 `relation`, SAR 사람 문제는 `situation` 을 사용합니다.

### 최소 에이전트

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

## 베이스라인 에이전트 (데모)

데모(`participant_sdk/demo`)는 실행·열람·부분 교체가 가능한 완전한 비대화형 에이전트입니다.

| 파일 | 역할 |
|---|---|
| `demo_participant.py` | `MARCClient` 핸들러로 Stage 1 / Stage 2 전체 흐름 연결. |
| `mock_vla.py` | **Mock VLA grounding** — 키워드 매칭; 참가자가 자신의 모델로 교체. |
| `occupancy_planner.py` | 점유 격자 **A\*** 경로 계획(`get_occupancy_map()` 입력). |
| `nav.py` | `(linear_x, angular_z)` 산출 waypoint 추종 컨트롤러. |

흐름:

1. **등록** -> `SESSION_ACK`.
2. **Stage 1**: 라운드별 `voice_command` -> mock VLA -> `submit_grounding()`.
3. **Stage 2**: `task_description` -> mock VLA -> `submit_stage2_grounding()` -> occupancy
   A\* 경로 계획 -> waypoint 추종(`cmd_vel`), stall 시 재계획, 도달/타임아웃 시 정지 ->
   `task_complete()`. Stage 2 도착지는 **지정된 장소** 로 표기합니다.

```{admonition} Mock VLA 를 교체하세요
:class: important
`mock_vla.py` 는 자리표시이며, 참가자가 **자신의 VLA grounding 으로 교체** 해야 합니다.
데모 mock VLA 의 정답 하드코딩은 **데모 전용 편의**이며, 실제 별도 하드웨어 제출 환경에서는
런타임에 정답 접근이 없습니다.
```

```{admonition} Navigation 은 학습 환경이 불필요합니다
:class: note
장애물은 정적이므로(사람은 이동하지 않음) 표준 ROS 2 navigation 으로 충분합니다: 전역 occupancy
계획 + 라이다 기반 지역 회피. 점유 지도는 주행 가능 도로만 담으므로 사람·랜드마크는 센서로 감지합니다.
```

---

## 매니퓰레이션 학습 키트

pick-and-place 는 **관절각(joint-angle) 제어만** 으로 수행합니다 — 그리퍼를 물체에 놓는 관절
목표값을 참가자가 직접 계산합니다. 진입장벽을 낮추기 위해 주최측은 베이스라인 + 학습 키트
(**옵션 B**)를 제공합니다. 정답(GT)은 런타임에 제공하지 않으며, 라벨은 **오프라인 학습용으로만**
제공합니다.

제공 항목:

- **FK/IK 레퍼런스** — 의존성 없는 numpy 구현
  (`participant_sdk/verification/fk_ik.py`). (실시간 placo IK 는 환경 의존이라 참가자에게 배포하지
  않습니다.)
- **모션 프리미티브 / 웨이포인트 보간** — EE 웨이포인트 -> 관절각 키프레임, 속도제한 보간
  (`arm_pick.py`, `waypoint_sequence.py`).
- **동작하는 베이스라인 pick-and-place** — 그대로 부분 점수 획득 가능(`arm_pick.py`).
- **LeRobot 데모 데이터셋** — 모방학습 / VLA 콜드스타트용 텔레오퍼레이션 (관측, 액션) 에피소드
  (LeRobot 포맷).
- **`manipulation_trainer`** — 지각 트레이너의 형제 도구. 도메인 랜덤화된 연습 씬에서 로봇 관절
  action 을 적용하고 성공/보상과 `reset()/step()` 을 제공합니다(두 트레이너는 **한 트레이너 이미지의
  두 엔트리** 로 배포되며 경연 런타임에서는 제외).

```{note}
로봇은 **모바일 매니퓰레이터** 입니다: 4륜 조향 섀시 위 6-DoF 팔(`joint_1`..`joint_6`) +
Robotiq 2F-140 그리퍼. 도달성은 베이스+팔 협응에서 나오며 팔 단독은 비여유(non-redundant)입니다.
데이터셋 규모·시뮬 래퍼 공개 범위·IK 배포 정책은 내부 검토 중입니다.
```

올해 sim2real 은 **방향성만** 입니다: 설계는 전이-호환(joint-space 제어, 실센서 형태 관측)을
유지하되, 엄밀한 도메인 랜덤화나 고성능 RL 은 범위 밖입니다.
