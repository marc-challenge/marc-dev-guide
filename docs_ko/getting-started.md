# 시작하기

깨끗한 머신에서 동작하는 데모 에이전트까지 최단 경로로 도달한 뒤, 계속 개발하는 데 필요한 전체
환경을 정리합니다.

> 이 페이지의 모든 버전 문자열(이미지 태그·wheel 버전·일정)은 **잠정 / 내부 검토** 단계입니다.
> 릴리스 동결 전까지 `2026.1.0`, `v2026.x` 는 예시로 간주하십시오.

---

## Quickstart (목표: 30분)

최단 경로: **받아서 → 켜고 → 데모 실행**.

### 0. 사전 준비 확인

아래 [환경 셋업](#환경-셋업) 충족 여부를 확인하십시오(Ubuntu 22.04, NVIDIA RTX GPU,
Docker + NVIDIA Container Runtime, ROS 2 Humble).

### 1. 스타터킷 받기

```bash
git clone https://github.com/marc-challenge/marc-starter-kit.git
cd marc-starter-kit
```

스타터킷은 SDK, 데모 에이전트, Docker 레시피, 공개 시나리오, **chungmu** 연습 배경 USD 를 포함합니다.

### 2. NVIDIA NGC 로그인 (`nvcr.io`)

플랫폼·Trainer 이미지는 **Dockerfile-only** 라 프리빌트를 받지 않고, Isaac Sim base 이미지
(`nvcr.io/nvidia/isaac-sim:5.1.0`)를 **본인 명의로** 직접 pull 하여 로컬 빌드합니다 — 직접 pull
한다는 것은 곧 **Isaac Sim EULA 에 본인이 라이선시로 동의**한다는 의미입니다. pull 하려면 NGC
로그인이 선행되어야 합니다.

1. [ngc.nvidia.com](https://ngc.nvidia.com) 에서 **무료 계정 생성** 후 로그인.
2. **API Key 발급** — 우측 상단 프로필 → **Setup → Generate API Key**(또는 *Generate Personal
   Key*). 키는 **1회만 노출**되므로 즉시 복사·보관하십시오.
3. **레지스트리 로그인.** Username 은 리터럴 문자열 `$oauthtoken`, Password 는 발급한 API Key.

```bash
docker login nvcr.io
# Username: $oauthtoken      ← 따옴표 없이 이 문자열 그대로
# Password: <발급한 NGC API Key>
```

```{tip}
비대화식(CI) 로그인:
`echo "<API_KEY>" | docker login nvcr.io -u '$oauthtoken' --password-stdin`.
`marc.sh setup` 래퍼는 로그인 필요성을 *안내만* 하며 대신 로그인하지 않습니다(자격증명은 참가자 소유).
```

### 3. 플랫폼 / Trainer 로컬 빌드 (Dockerfile-only)

시뮬레이션 플랫폼·Trainer 이미지는 **Dockerfile-only** 입니다. 프리빌트 이미지는 **재배포되지
않습니다**(Isaac Sim 재배포 라이선스). 위 NGC 로그인을 마친 상태에서 로컬 빌드하면, 빌드가
방금 인증한 base 이미지를 pull 합니다.

```bash
# 빌드 컨텍스트는 리포 루트입니다(Dockerfile 이 simulation_app/, resources/, scenarios/ 를 COPY).
docker build -f marc-dev-platform/Dockerfile.practice -t marc-platform:practice .
```

```{note}
최초 빌드는 Isaac Sim base 이미지를 pull 합니다(그래서 위 NGC 로그인이 필요). 이 단계는 인터넷이
필요하며 정상입니다 — **빌드 시점은 온라인**입니다. 인터넷 차단은 *심사 런타임*에만 적용됩니다.
```

### 4. 런타임 기동

```bash
docker compose up
```

`docker compose up` 이 정본 진입점입니다. 로컬 편의용 래퍼(`marc.sh`)도 제공됩니다.

```{important}
**최초 기동은 오래 걸립니다 — 멈춘 게 아닙니다.** 월드 구성(씬·사람 포즈·랜드마크·로봇)과
셰이더 컴파일에 **수 분**(보통 2~5분, 캐시가 비어 있는 첫 실행은 더 오래)이 걸립니다. 이 동안
**뷰포트는 검정 화면**이고 제목이 *"New Stage\*"* 로, 로딩 바가 멈춘 것처럼 보일 수 있습니다.
이는 정상이며 **그대로 기다리세요(강제 종료 금지).** 아래 로그가 보여야 기동 완료입니다:

    [Runtime] Startup complete in <N>s
    Auto-plan: waiting for a participant to register...

이때 뷰포트에 chungmu 씬이 나타나고, 플랫폼이 참가자 앱의 register 를 받을 준비가 됩니다.
진행 상황은 `docker compose logs -f` 로 확인하세요.
```

### 5. SDK 설치

```bash
pip install marc-sdk==2026.1.0
```

### 6. 데모 에이전트 실행

```bash
# 데모 디렉터리에서. 팀 ID / 토큰을 먼저 설정합니다.
export MARC_TEAM_ID=u1
export MARC_TOKEN=<발급-토큰>
cd participant_sdk/demo
docker compose up        # 주최측도 동일 명령으로 채점
```

에이전트가 등록 → Stage 1 미션 수신 → grounding 제출 → (Stage 2) 로봇 주행하는 것을 확인할 수
있습니다. 로봇이 움직이면 루프가 닫힌 것입니다.

```{tip}
이 페이지의 모든 명령은 복사 버튼을 제공합니다(`sphinx-copybutton`). 실제 태그가 동결되면
pull/build/install 명령을 공개 이미지 태그·wheel 버전과 **글자단위로 일치** 검증한 뒤 게시합니다.
```

---

## 환경 셋업

| 항목 | 요구사항 |
|---|---|
| OS / HW | Ubuntu **22.04**, 충분한 VRAM 의 NVIDIA **RTX** GPU. |
| Docker | Docker + **NVIDIA Container Runtime**(GPU 패스스루). |
| NGC 계정 | **NVIDIA NGC 계정**(무료) + **API Key** — `nvcr.io` 에서 Isaac Sim base 이미지 pull 에 필수([Quickstart 2단계](#2-nvidia-ngc-로그인-nvcr-io) 참조). |
| Python | 참가자 SDK = **3.10**(ROS 2 Humble). 플랫폼 내부 = 3.11(Isaac Sim, 분리 셸). |
| 미들웨어 | ROS 2 **Humble**, **Fast DDS**. 머신 간 `ROS_DOMAIN_ID` 정렬. |
| 토폴로지 | 참가자 앱은 플랫폼과 **별도 하드웨어**(동일 LAN / 동일 ROS 도메인, DDS 는 네트워크 경유). |

### 별도 하드웨어 토폴로지

참가자 애플리케이션은 시뮬레이션 플랫폼과 **다른 머신**에서 실행하는 것을 전제로 합니다. 두 머신은
LAN 과 **동일 `ROS_DOMAIN_ID`** 를 공유하며, DDS 디스커버리/트래픽은 네트워크(UDP)로 흐릅니다.
데모 `docker-compose.yml` 은 `network_mode: host` 로 호스트 NIC 상에서 디스커버리합니다.

8MP CCTV 영상이 네트워크로 전송되므로 **기가비트 이상 LAN** 을 권장합니다.

### Python 셸 분리 (중요)

시스템 ROS 2 Humble 은 **Python 3.10**, Isaac Sim 은 **Python 3.11** 입니다. 혼용하면 import 가
깨집니다. 플랫폼 실행 스크립트는 `/opt/ros` 경로를 `PYTHONPATH`·`LD_LIBRARY_PATH` 에서 제거하여
Isaac Sim 셸을 깨끗하게 유지합니다. import 오류가 발생하면 [FAQ → 트러블슈팅](faq.md#트러블슈팅)을
참조하십시오.

### 환경변수

| 변수 | 기본값 | 설명 |
|---|---|---|
| `MARC_TEAM_ID` | `u1` | 할당받은 팀 ID. |
| `MARC_TOKEN` | — | 세션 토큰(필수). |
| `ROS_DOMAIN_ID` | `0` | ROS 2 도메인; 플랫폼과 일치해야 함. |

```{note}
에이전트는 `MARC_TOKEN`·`ROS_DOMAIN_ID` 등 **`MARC_*`** 환경변수로 설정합니다.
```
