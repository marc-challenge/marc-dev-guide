# 기술 가이드

이 페이지는 참가자가 대회에 제출할 프로그램을 개발할 때 사용하는 도구와 코드를 소개합니다. 아래 다섯
가지를 순서대로 읽으면, 어디서 개발하고 무엇으로 로봇과 통신하며 어디서부터 코드를 시작하는지 한눈에
파악할 수 있습니다.

- 시뮬레이션 플랫폼(연습용) — 로컬 환경에서 개발한 프로그램을 연동하여 연습하는 시뮬레이션 환경입니다.
  예선과 본선에서 사용되는 가상 캠퍼스와 거의 동일하게 구성되어 있어, 실제 대회 환경 그대로 미리
  연습할 수 있습니다.
- `marc_sdk` — 참가자의 프로그램이 플랫폼과 ROS 2 로 통신하도록 지원하는 파이썬 라이브러리입니다. 카메라
  영상 같은 센서 데이터를 수신하고, 로봇을 제어하고, 답안을 제출하는 작업을 함수 호출 몇 개로 처리할 수
  있습니다. 통신의 복잡한 부분은 SDK 가 대신 처리하므로, 참가자는 인식(VLA)과 주행 로직에만 집중할 수
  있습니다.
- 베이스라인 코드(데모) — 참가 등록부터 답안 제출, 로봇 주행까지 전체 흐름이 이미 연결되어 있는 예제
  코드입니다. 인식과 판단을 담당하는 부분만 참가자의 실제 구현으로 교체하면 되는 출발점입니다.
- 데이터셋 생성기 — CCTV 영상 속 물건을 인식하는 모델(객체 탐지 등)을 학습시킬 때 사용하는, 이미지와
  정답 라벨을 자동으로 생성하는 도구입니다.
- 매니퓰레이션 학습 키트(선택) — 로봇팔로 물건을 집어 옮기는 동작(pick-and-place)을 연습하고 구현할
  때 참고하는 코드입니다.

아래 다섯 개 항목은 모두 같은 순서로 정리했습니다 — 먼저 개요, 그다음 제공 기능, 마지막으로 어느
폴더에서 어떻게 사용하는지(사용 방법)입니다. 로봇·센서와 주고받는 메시지의 정확한 규격이 필요할 때는
[API 레퍼런스](api-reference.md)를 참조합니다.

---

## 시뮬레이션 플랫폼(연습용)

시뮬레이션 플랫폼은 참가자가 개발한 에이전트를 제출하기 전에 참가자 PC 에서 연동하여 반복 연습하는
실행 환경입니다. 예선·본선과 거의 동일한 가상 캠퍼스에서 로봇과 센서를 그대로 다룰 수 있습니다.

### 제공 기능

- 대회와 거의 동일한 가상 캠퍼스(디지털 트윈)와 로봇(4륜 섀시 + 6축 팔), 고정 CCTV·로봇 카메라·라이다
  센서, 그리고 이들과 주고받는 ROS 2 인터페이스.
- 성격이 다른 연습 시나리오 두 가지.
  - `marc2026_chungmu` — 실제 대회와 같은 형식의 전체 문항이 담긴 종합 연습 시나리오입니다. 정답이
    함께 들어 있어, 참가자가 제출한 답안이 몇 점을 받는지 자체 채점 결과까지 확인할 수 있습니다.
  - `marc2026_demo` — 베이스라인 코드가 등록부터 답안 제출·주행까지 처음부터 끝까지 문제없이 도는지
    빠르게 확인하기 위한 데모 시나리오입니다. 짧은 시간에 전체 동작을 시연할 수 있도록
    `marc2026_chungmu` 를 변형한 시나리오입니다.
- 어떤 시나리오로 띄울지, 그 시나리오의 어떤 문항을 제출할지 고르는 선택 기능.

실제 채점에 사용되는 시나리오는 공개하지 않으므로, 위 두 시나리오로 형식과 흐름을 익힌 뒤 실제 인식·판단
코드를 준비하는 방식으로 연습해야 합니다.

### 사용 방법

스타터킷의 `simulation-platform/` 폴더에서 실행합니다. 참가자는 보통 **① 경연 환경 설정(시나리오·문항
선택) → ② 플랫폼 실행** 순서로 진행하며, 개발 중에는 설정을 바꿔 가며 이 과정을 반복합니다.

#### ① 경연 환경 설정 (시나리오·문항 선택)

무엇을 — 어떤 시나리오의 어떤 문항을 — 제출할지 먼저 정합니다. 이 설정은 플랫폼 폴더의 `.env` 에 저장되어
다음 실행부터 적용됩니다.

**시나리오 선택.** 어떤 시나리오로 플랫폼을 실행할지는 `ENV_MARC_SCENARIO` 로 지정합니다(기본값
`marc2026_chungmu`). `.env` 에 지정해 두면(권장) 다음 실행부터 적용되고, 한 번만 변경해 실행하려면 실행
명령 앞에 일시적으로 지정해도 됩니다.

```bash
# simulation-platform/.env
ENV_MARC_SCENARIO=marc2026_demo
```

**문항 선택 (`problems.yaml`).** 시나리오에는 여러 문항이 들어 있는데, 개발 중에는 그중 특정 문항만
선택하여 반복 시험이 필요한 경우가 많습니다. **`problems.yaml` 파일이 있으면** 플랫폼이 그 파일에서
선택한(selected) 문항만 출제하고, **파일이 없으면 전체 문항**을 출제합니다. 별도 환경변수 설정은 필요
없습니다.

제출할 문항은 아래 명령의 체크리스트로 선택합니다(위아래로 이동, 스페이스바로 켜고 끄기). 저장하면 킷 루트에
활성 파일 `problems.yaml` 과 시나리오별 보관본 `problems.<scenario>.yaml` 이 함께 생성되고, 다음
실행부터 자동 적용됩니다. 전체 문항으로 되돌리려면 `problems.yaml` 을 삭제합니다.

```bash
bash simulation-platform/marc.sh select marc2026_chungmu   # or marc2026_demo
```

```{note}
**문항 선택은 시나리오별로 따로 보관됩니다.** select 를 실행하면 그 시나리오의 보관본
`problems.<scenario>.yaml` 과 플랫폼이 읽는 활성 파일 `problems.yaml` 이 함께 저장되고, 같은
시나리오로 다시 select 하면 이전 선택을 불러와 이어서 편집합니다. 플랫폼은 실행 시 `problems.yaml` 의
`scenario` 가 현재 시나리오와 다르면 그 파일을 무시하고 경고를 남긴 뒤 **전체 문항으로 폴백**하므로,
**시나리오를 변경했다면 그 시나리오로 select 를 다시 실행**해야 합니다. 시나리오에 없는 문항 이름은 무시되고
경고만 남습니다.
```

#### ② 플랫폼 실행

환경 설정이 끝나면 플랫폼을 실행합니다. 시나리오(`.env`)와 문항(`problems.yaml`) 선택이 그대로 적용됩니다.

```bash
cd simulation-platform
docker compose --profile platform up   # or: bash marc.sh platform
```

다른 시나리오나 다른 문항으로 시험하려면 **①로 돌아가 설정을 변경한 뒤 다시 실행**합니다 — 개발
중에는 이 "설정 → 실행 → 확인" 반복이 기본 흐름입니다.

---

## MARC 클라이언트 SDK (`marc_sdk`)

이 SDK 의 중심은 `MARCClient` 하나입니다. 플랫폼과 주고받는 ROS 2 통신 — 등록 핸드셰이크, 메시지
종류 구분, 세션·순번 관리, QoS, CCTV 카메라 자동 탐색 — 을 `MARCClient` 가 내부에서 대신 처리합니다.
따라서 참가자는 통신의 세부를 몰라도 인식(VLA)과 주행 로직에 집중할 수 있습니다.

### 제공 기능

- 콜백 모델 — 새 미션이 도착하거나 상태가 변경되거나 채점 결과가 도착하는 등 이벤트가 발생하면, 참가자가
  등록해 둔 콜백 함수를 SDK 가 자동으로 호출합니다.
- 센서 조회 · 로봇 제어 · 정답 제출 메서드 — 카메라·라이다 같은 센서를 읽고, 로봇을 제어하고, 답안을
  제출하는 작업을 함수 호출로 처리합니다.
- ROS 2 통신 자동 처리 — 등록 핸드셰이크, 메시지 구분, 세션·순번 관리, QoS, CCTV 카메라 자동 탐색을
  내부에서 대신 처리합니다.

각 콜백·메서드의 전체 목록과 시그니처·파라미터·반환값은 [API 레퍼런스](api-reference.md)에 정리되어
있습니다. 여기서는 초기화하고 첫 콜백을 연동하는 기본 사용법만 설명합니다.

### 사용 방법

`marc_sdk` 는 pip 로 설치하는 패키지가 아니라 스타터킷 루트의 `marc_sdk/` 폴더에 소스로 포함되어
있습니다. 파이썬이 찾을 수 있도록 경로만 지정하면 바로 import 하여 사용합니다.

#### 준비 및 초기화

```bash
# Submission image (Docker): marc_sdk source is COPYed into the image and added to
#   PYTHONPATH (see demo/Dockerfile). No action needed.
# Host-side dev: add marc_sdk's parent folder (the starter-kit root) to PYTHONPATH so it imports.
#   demo/launch.sh does this automatically. To set it manually:
export PYTHONPATH="<starter-kit-root>:${PYTHONPATH}"
```

```python
from marc_sdk import MARCClient

client = MARCClient.from_env()   # reads MARC_TEAM_ID / MARC_TOKEN
client.connect()                 # handshake (HELLO -> CHALLENGE -> PROOF -> ACK), automatic
```

`from_env()` 는 팀 ID 와 인증 토큰을 환경변수 `MARC_TEAM_ID` 와 `MARC_TOKEN` 에서 읽어 클라이언트를
만듭니다. 이 두 값은 **구글 폼으로 대회 참가를 신청한 뒤 발급받는 팀 ID 와 팀 인증 토큰**입니다.
보통 제출용 `docker-compose.yml` 의 환경변수로 지정합니다(→ [제출 가이드](submit-guide.md)).
환경변수 대신 `MARCClient(team_id=..., token=...)` 처럼 값을 직접 넘길 수도 있습니다.

이어서 `connect()` 가 challenge-response 핸드셰이크 전체를 수행하고 백그라운드 executor 를 실행합니다.

#### 콜백으로 플랫폼과 연동하기

각 이벤트에 대응하는 데코레이터에 콜백 함수를 등록해 두면, 그 이벤트가 일어날 때 SDK 가 등록된 콜백
함수를 자동으로 호출합니다. 따라서 참가자는 이벤트를 처리할 콜백 함수를 구현해 등록하기만 하면,
플랫폼과의 통신 방식을 몰라도 플랫폼과 연동할 수 있습니다. 아래는 Stage 1 미션을 받아 답안을 제출하는
가장 간단한 형태입니다.

```python
from marc_sdk import MARCClient

client = MARCClient.from_env()

@client.on_mission
def handle_mission(mission):              # a Stage 1 problem arrives
    result = my_vla(mission.voice_command)  # your perception -> GroundingResult
    client.submit_grounding(result)

client.connect()   # register + handshake
client.run()       # spin in the background (blocks)
```

같은 방식으로 Stage 2 미션(`on_stage2_mission`), 주행 시작(`on_stage2_run`), 채점 결과(`on_score`) 등
다른 이벤트도 콜백 함수를 구현해 등록합니다. 어떤 이벤트가 있고 각 콜백이 언제 호출되며 어떤 값을
받는지, 그리고 센서 조회·로봇 제어·정답 제출 함수의 시그니처·파라미터·반환값은
[API 레퍼런스](api-reference.md)에서 자세히 다룹니다.

---

## 베이스라인 코드 (데모)

스타터킷에는 등록부터 답안 제출·로봇 주행까지 전체 흐름이 이미 연결된 베이스라인 코드(데모)가
들어 있습니다. 인식·판단 부분만 모의 구현(mock)으로 채워져 있어서, 참가자는 이 코드를 출발점으로 그
부분을 실제 구현으로 교체하면 됩니다. 세 개의 `mock_agent_*` 에이전트는 CCTV·센서로 인식하는 대신,
데모 데이터 파일 `mock_demo_data.yaml` 에 미리 뽑아 둔 값(문항별 정답 좌표, 장애물)을 찾아 쓰는
방식으로 동작합니다.

```{admonition} mock_demo_data.yaml 은 시나리오에서 뽑은 데모 전용 데이터입니다
:class: important
`mock_demo_data.yaml` 의 Stage 1·2 문항별 정답 좌표와 장애물은 `tools/mock_data_builder` 가
데모 시나리오(`scenarios/marc2026_demo.yaml`)에서 **정답을 추출하고 무작위 오답을 일부 섞어** 만든
것입니다. 실제 채점 환경에서는 시나리오도 런타임 정답도 없으므로, 이 데이터를 사용하는 세 mock 에이전트를
참가자의 실제 인식·감지 코드로 반드시 교체해야 합니다.
```

### 제공 기능

- 등록부터 답안 제출, 로봇 주행까지 전체 흐름이 이미 연결된 실행 가능한 예제 코드.
- 인식·판단을 대신하는 세 개의 mock 에이전트(인식·내비게이션·조작) — 어디를 실제 코드로 바꾸면 되는지 명확합니다.
- Stage 2 주행: 미리 뽑아 둔 장애물 데이터로 이동 경로를 계획하는 내비게이션 모의 구현 — 교체·개선 대상.

### 사용 방법

스타터킷 루트의 `demo/` 폴더에 있으며, 그 폴더에서 실행합니다.

```bash
cd demo
docker compose up
```

#### 파일 구조

아래 "구분" 열은 각 파일이 **교체해야 할 mock 인지, 그대로 사용하는 필수 코드인지** 를 나타냅니다.

| 파일 | 구분 | 역할 |
|---|---|---|
| `participant_app.py` | 필수(진입점) | `MARCClient` 에 콜백을 등록하고 Stage 1 / Stage 2 전체 흐름을 연결 |
| `mock_agent_vla.py` | **mock — 교체 대상** | Stage 1·2 인식(VLA) 모의 구현. CCTV 를 분석하지 않고, 받은 자연어 명령으로 `mock_demo_data.yaml` 에서 문항별 정답을 찾아 제출 |
| `mock_agent_navigation.py` | **mock — 교체·개선 대상** | Stage 2 내비게이션 모의 구현. 미리 뽑아 둔 장애물 데이터로 이동 경로를 계획하여 주행 |
| `mock_agent_manipulation.py` | **mock — 교체·개선 대상** | 로봇팔 집기 동작(관절각 키프레임) |
| `mock_demo_data.yaml` | 데모 데이터 | 세 mock 에이전트가 참조하는, 시나리오에서 미리 뽑은 Stage 1·2 정답 좌표 + 장애물 (데모 전용 — 개요 참조) |

세 개의 `mock_agent_*` 파일이 참가자가 개발할 에이전트 코드(인식·내비게이션·조작)를 **대신하는
모의 구현**입니다. `participant_app.py` 는 이들을 불러 전체 흐름만 연결합니다.

#### 실행 흐름

1. **시작·등록** — `participant_app.py` 가 `MARCClient` 를 만들고 콜백을 등록한 뒤, `connect()`(등록
   → `SESSION_ACK`) → `run()`(백그라운드 수신 시작).
2. **Stage 1 (인식·좌표 제출)** — 라운드마다 `on_mission` 콜백에서 `mock_agent_vla.process()` 가
   받은 자연어 명령에 해당하는 정답을 찾아 `GroundingResult` 로 돌려주고, 이를 `submit_grounding()` 으로 제출.
3. **Stage 2 해석** — `on_stage2_mission` 콜백에서 `mock_agent_vla.process_stage2()` 가 그 문항의
   정답을 찾아 `GroundingResult` 로 돌려주고, 이를 `submit_stage2_grounding()` 으로 제출. 함께 받은
   `owner_position`(배치 위치)을 저장.
4. **Stage 2 리빌** — `on_stage2_reveal` 콜백에서 대략 위치 힌트(`hint_center`)를 수거 목표로 저장.
5. **Stage 2 주행** — `on_stage2_run`(별도 스레드)에서: ① 수거 지점으로 내비게이션 → 도착하면
   로봇팔로 집기, ② 배치 위치(owner_zone)로 내비게이션 → 도착 후 `task_complete()`.

#### 모의 구현(mock)으로 처리한 부분

데모가 인식·판단 대신 `mock_demo_data.yaml` 의 미리 뽑아 둔 값으로 채워 둔 세 부분이며, 참가자가 실제
코드로 교체할 위치입니다.

- `mock_agent_vla.py` — Stage 1·2 인식(VLA). CCTV 를 분석하지 않고, 받은 자연어 명령으로 문항별
  정답 좌표를 데모 데이터에서 찾아 제출합니다.
- `mock_agent_navigation.py` — Stage 2 내비게이션. 센서로 장애물을 감지하는 대신, 미리 뽑아 둔
  장애물 데이터로 이동 경로를 계획하여 주행합니다.
- `mock_agent_manipulation.py` — 로봇팔 집기. 물체 위치를 인식하지 않고 고정된 관절 키프레임으로 집습니다.

세 에이전트 모두 데모 데이터에 의존하므로, 실제 대회에서는 참가자의 실제 인식·감지 코드로 교체해야 합니다.

```{important}
**교체 대상은 "알고리즘"이며, "플랫폼 연동"이 아닙니다.** mock 인 것은 위 세 에이전트 안의 인식·판단·
이동 경로 로직뿐입니다. 반면 `participant_app.py` 가 플랫폼과 주고받는 `marc_sdk` 호출 — 등록·핸드셰이크
(`connect`), 콜백 등록(`on_mission`·`on_stage2_mission`·`on_stage2_run` 등), 답안 제출
(`submit_grounding`·`submit_stage2_grounding`), 센서 조회(`get_cctv_image`·`get_occupancy_map`),
로봇 제어(`send_cmd_vel`)·완료 통지(`task_complete`) — 은 **그대로 사용해야 하는 정확한 예시 코드**입니다.
참가자는 이 연동 골격을 유지한 채, 각 콜백이 반환할 값을 만드는 알고리즘만 실제 구현으로 교체하면 됩니다.
```

#### 코드 구조

`participant_app.py` 의 골격은 아래와 같습니다. 콜백을 등록하고, 각 콜백에서 SDK 함수를 호출하는
형태입니다. mock 부분(아래 주석)만 참가자의 구현으로 교체하면 나머지 흐름은 그대로 동작합니다.

```python
from marc_sdk import MARCClient, GroundingResult
from mock_agent_vla import MockVLAGrounding


class DemoParticipant:
    def __init__(self):
        self.client = MARCClient.from_env()
        self.vla = MockVLAGrounding()          # <- replace with your VLA model
        self._register_handlers()

    def _register_handlers(self):
        c = self.client
        c.on_mission(self._on_mission)                # Stage 1
        c.on_stage2_mission(self._on_stage2_mission)  # Stage 2 interpretation
        c.on_stage2_reveal(self._on_stage2_reveal)    # approx. location hint
        c.on_stage2_run(self._drive)                  # Stage 2 driving (own thread)

    def _on_mission(self, mission):
        # mock: look up the pre-extracted answer -- replace with real CCTV perception
        result = self.vla.process(mission.voice_command, self.client.list_cctv())
        self.client.submit_grounding(result)          # GroundingResult

    def _drive(self):
        # navigate to the object -> arm pick -> navigate to the delivery point
        while self.client.is_running:
            twist = self._plan_step()                 # plan a path to the target and follow it
            self.client.send_cmd_vel(**twist)
        self.client.task_complete()

    def run(self):
        self.client.connect()   # register -> SESSION_ACK
        self.client.run()       # spin (background)


DemoParticipant().run()
```

#### 베이스라인에서 개발 시작하기

1. **`mock_agent_vla.py` 를 실제 VLA 로 교체** — `client.get_cctv_image()` 등으로 CCTV 영상을 받아
   대상을 찾고 `GroundingResult` 를 반환하도록 구현합니다. 반환 형식만 맞추면 나머지 흐름은 그대로
   동작합니다.
2. **Stage 2 grounding 을 실제 결과로 교체** — `mock_demo_data.yaml` 에서 찾아 오던 정답 좌표를
   참가자의 grounding 결과로 교체합니다(`process_stage2()` 에 같은 VLA 를 재사용해도 됩니다).
3. **시나리오 의존 제거** — 장애물을 `mock_demo_data.yaml`(시나리오 추출본) 대신 `get_occupancy_map()`
   과 라이다·카메라 센서로 감지하도록 변경합니다.
4. **필요하면 내비게이션·집기 개선** — `mock_agent_navigation.py` / `mock_agent_manipulation.py`
   는 그대로도 부분 점수를 얻을 수 있으므로, 먼저 인식(1·2)부터 교체하고 이후 개선합니다.
5. **리빌 힌트 활용** — Stage 2 에서 grounding 이 틀려도 `on_stage2_reveal` 의 대략 위치로 수거
   주행을 이어갈 수 있습니다(데모가 이미 그렇게 동작합니다).
6. **제출** — mock 을 실제 구현으로 교체한 뒤, [제출 가이드](submit-guide.md)의 절차대로 Docker 로
   빌드·제출합니다.

```{admonition} Navigation 은 학습 환경이 불필요합니다
:class: note
장애물은 정적이므로(사람은 이동하지 않음) 표준 ROS 2 navigation 으로 충분합니다: 전역 occupancy
계획 + 라이다 기반 지역 회피. 점유 지도는 주행 가능 도로만 담으므로 사람·랜드마크는 센서로 감지합니다.
```

---

## 데이터셋 생성기

CCTV 영상으로 물건과 사람을 찾는 인지 모델을 학습하려면, 라벨(정답)이 붙은 학습 데이터가
필요합니다. 데이터셋 생성기는 시뮬레이션 플랫폼(연습·대회 공통)과 동일한 CCTV 화각 안에 대회용
사물·랜드마크·사람을 배치하고, 그 장면의 이미지와 정답 라벨을 자동으로 생성합니다.
(모델을 대신 학습시키지는 않으며 — 학습에 사용할 데이터를 생성합니다.)

### 제공 기능

생성하는 데이터는 두 가지입니다.

- 물체 인식(object detection) — 배치한 **사물·랜드마크·사람** 각각의 종류(`class`)와 2D 경계상자(bounding box).
- 위치·방향 추정(pose estimation)용 정보 — 각 CCTV 의 위치·방향(extrinsics)과 렌즈 정보(intrinsics),
  그리고 카메라 이미지. 대상의 **3D 위치·방향**을 계산하는 데 쓰는 재료이며, 사람의 자세(앉음·누움
  등)와는 무관합니다.

```{note}
이 도구는 개별 물체의 종류와 위치·방향을 추정하기 위한 데이터를 생성하는 것이지, 벤치 옆의 우산과
같이 사물 사이의 관계(relation)를 학습하기 위한 데이터는 생성하지 않습니다.
```

### 사용 방법

플랫폼과 같은 `simulation-platform/` 폴더에서, 실행할 대상만 `dataset-gen` 으로 지정해 실행합니다.

```bash
cd simulation-platform

# The two commands below do the same thing.
docker compose --profile dataset-gen up
bash marc.sh dataset-gen
```

#### 결과물

생성기를 실행하면 학습 데이터를 얻는 방법은 두 가지입니다.

- **ROS 2 토픽 (실시간)** — 참가자 애플리케이션이 생성기 실행 중에 ROS 2 로 데이터를 실시간으로 받는
  방식입니다. 카메라별로 아래 토픽을 발행합니다(`{cam}` = 카메라 id, 네임스페이스 기본값 `marc`).
  - `/marc/env/cctv/{cam}/image` (`sensor_msgs/Image`) — 카메라 이미지.
  - `/marc/env/cctv/{cam}/info` (`sensor_msgs/CameraInfo`) — 렌즈 정보(intrinsics).
  - `/marc/env/cctv/{cam}/groundtruth` (`std_msgs/String`, JSON) — 물체 인식 정답: 각 대상의
    종류(`class`)와 2D 경계상자. 장면이 바뀌기 전까지 정적이라 **latched** 로 발행되어, 나중에
    구독해도 현재 장면의 정답을 곧바로 받습니다.
  - `/tf_static` (`tf2_msgs/TFMessage`) — 각 카메라의 위치·방향(extrinsics). 위치·방향 추정에 사용합니다.
- **오프라인 파일 (반복 학습)** — 파일로 추출해 둔 데이터를 활용해 모델을 반복적으로 학습시킬 때 쓰는
  방식입니다. `trainer_output/<시나리오>/scene_<번호>/<카메라>.json` (+ 같은 이름의 `.png`) 로
  저장되며, 실행을 반복하면 기존 장면을 덮어쓰지 않고 누적합니다.

정답 JSON 은 groundtruth 토픽과 오프라인 파일에 공통으로 쓰이며, 형태는 다음과 같습니다.

```json
{
  "scene_id": 3,
  "frame_id": "rig_3_b",
  "image": { "width": 1280, "height": 720 },
  "detections": [
    { "class": "master_chef_can", "kind": "object",
      "bbox": [412, 133, 468, 210], "occlusion": 0.12 }
  ]
}
```

`bbox` 는 픽셀 좌표 `[x_min, y_min, x_max, y_max]` 순서이고, `occlusion` 은 가림 정도(0=가려지지 않음)입니다.

#### 다양한 장면 만들기

화면의 버튼으로 학습 장면을 계속 새로 생성합니다.

- `New Scene` — 카메라는 그대로 두고, 화각 안의 물건·사람만 다시 배치합니다.
- `New Camera` — 카메라(미션)부터 다시 선택하여 배치합니다.

자주 사용하는 환경변수: `ENV_MARC_SCENARIO`(시나리오 선택), `HEADLESS`(GUI 없이 실행),
`MARC_TRAINER_DIR`(저장 위치), `TRAINER_SAVE_OFFLINE=0`(오프라인 파일 저장 끄기).

---

## 매니퓰레이션 학습 키트

pick-and-place 는 관절각(joint-angle) 제어만으로 수행합니다 — 그리퍼를 물체에 놓는 관절
목표값을 참가자가 직접 계산합니다. 진입장벽을 낮추기 위해 주최측은 베이스라인 + 학습 키트
(옵션 B)를 제공합니다. 정답(GT)은 런타임에 제공하지 않으며, 라벨은 **오프라인 학습용으로만**
제공합니다.

### 제공 기능

**현재 스타터킷에 포함된 것** (`manipulation/` 폴더):

- FK/IK 레퍼런스 — 의존성 없는 numpy 구현(`manipulation/fk_ik.py`). URDF 링크 변환을 numpy 로
  체이닝해 FK 를 만들고, 수치 야코비안 + damped-least-squares 로 position IK 를 풉니다. (실시간 placo
  IK 는 환경 의존이라 참가자에게 배포하지 않습니다.)
- 모션 프리미티브 / 동작하는 베이스라인 pick — arm_base 프레임 EE 웨이포인트를 관절각으로
  보간해 집기 시퀀스를 수행합니다(`manipulation/arm_pick.py`, `fk_ik` 사용). 그대로도 부분 점수를
  얻을 수 있습니다.

**후속 제공 예정** (아직 스타터킷에 포함되지 않음):

- LeRobot 데모 데이터셋 — 모방학습 / VLA 콜드스타트용 텔레오퍼레이션 (관측, 액션) 에피소드
  (LeRobot 포맷).
- `manipulation_trainer` — 도메인 랜덤화된 연습 씬에서 로봇 관절 action 을 적용하고 성공/보상과
  `reset()/step()` 을 제공하는 학습 도구(경연 런타임에서는 제외).

### 사용 방법

스타터킷의 `manipulation/` 폴더에 참조 코드로 들어 있습니다. 베이스라인 데모의 집기 동작이 이
`arm_pick.py` 를 사용하므로, 관절 목표값을 직접 계산할 때는 `fk_ik.py` 의 FK/IK 를 출발점으로 삼아
`arm_pick.py` 의 집기 시퀀스를 참가자의 방식으로 확장합니다.

```{note}
로봇은 모바일 매니퓰레이터입니다: 4륜 조향 섀시 위 6-DoF 팔(`joint_1`..`joint_6`) +
Robotiq 2F-140 그리퍼. 도달성은 베이스+팔 협응에서 나오며 팔 단독은 비여유(non-redundant)입니다.
데이터셋 규모·시뮬 래퍼 공개 범위·IK 배포 정책은 내부 검토 중입니다.
```

올해 sim2real 은 방향성만 제시합니다: 설계는 전이-호환(joint-space 제어, 실센서 형태 관측)을
유지하되, 엄밀한 도메인 랜덤화나 고성능 RL 은 범위 밖입니다.
