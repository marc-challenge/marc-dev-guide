# 시작하기

이 페이지는 두 부분으로 구성됩니다. 먼저 아무것도 설치되지 않은 초기 상태의 머신에서 데모가 실제로
동작하는 것을 확인하기까지 가장 빠르게 도달하는 경로(Quickstart)를 안내하고, 이어서 이후 개발 과정에서
참고할 환경 셋업 레퍼런스를 정리합니다. 처음 진행하는 경우 Quickstart 를 위에서부터 순서대로 따라
진행합니다.

---

## Quickstart (목표: 30분)

가장 빠른 경로는 '내려받기 → 실행 → 데모 실행'의 세 단계로 요약됩니다. 실제 진행 순서는 아래와
같습니다.

0. 사전 준비 확인 — 참가자 PC 가 필요한 조건을 갖추었는지 점검합니다.
1. 스타터킷 받기 — 개발의 출발점이 되는 파일 묶음을 내려받습니다.
2. NVIDIA NGC 로그인 — 다음 단계에서 빌드할 base 이미지는 NVIDIA 의 Isaac Sim 이미지를 바탕으로
   합니다. 이 Isaac Sim 이미지를 NGC 에서 가져오려면 먼저 NVIDIA 계정 인증이 필요합니다.
3. 시뮬레이션 플랫폼(연습용) 설치 — Isaac Sim 이미지 위에 대회 환경을 얹은 base 이미지를 참가자
   PC 에서 직접 빌드합니다(플랫폼 이미지 자체는 다음 단계에서 자동으로 빌드됩니다).
4. 플랫폼 실행 — 설치한 시뮬레이션 플랫폼을 실행합니다.
5. SDK 참조 — (필요한 경우에만) SDK 설치 여부를 확인하는 참고 항목입니다.
6. 데모 실행 — 베이스라인 코드를 실행하여 로봇의 동작을 확인합니다.

### 0. 사전 준비 확인

먼저 참가자 PC 가 아래 [환경 셋업](#환경-셋업)의 조건을 갖추었는지 확인합니다.

### 1. 스타터킷 받기

스타터킷은 개발의 출발점입니다. 여기에는 SDK, 베이스라인 코드(데모), Docker 레시피, 공개
시나리오, 연습용 배경 USD 가 포함되어 있으며, 이 위에 참가자의 인지·판단 로직을 구현합니다.

```bash
git clone https://github.com/marc-challenge/marc-starter-kit.git
cd marc-starter-kit
```

### 2. NVIDIA NGC 로그인 (`nvcr.io`)

주최 측이 제공하는 플랫폼은 NVIDIA 의 Isaac Sim 을 기반으로 구축한 시뮬레이션 환경입니다. 참가자가
본인 컴퓨터에서 간편하게 실행할 수 있도록 Docker 형태로 제공합니다.

다만 한 가지 준비가 필요합니다. 이 플랫폼의 바탕이 되는 Isaac Sim 의 Docker 이미지는 **주최 측이
대신 배포할 권한이 없습니다.** 따라서 참가자가 직접 NVIDIA 계정을 생성하여, NVIDIA 가 이미지를
배포하는 NGC 서비스에 접근할 수 있는 상태를 먼저 갖추어야 합니다.

NGC 에 한 번 로그인해 두면 이후에는 스타터킷과 이 가이드의 절차에 따라 플랫폼이 자동으로
내려받아져 설치(빌드)됩니다. 아래 세 단계로 로그인 상태를 설정합니다.

1. [ngc.nvidia.com](https://ngc.nvidia.com) 에서 무료 계정 생성 후 로그인.
2. API Key 발급 — 우측 상단 프로필 → Account Settings → Generate API Key(또는 *Generate Personal Key*).
   키는 **1회만 노출**되므로 즉시 복사·보관해야 합니다.
3. 레지스트리 로그인 — Username 은 리터럴 문자열 `$oauthtoken`, Password 는 발급한 API Key.

```bash
docker login nvcr.io
# Username: $oauthtoken      <- this exact string, no quotes
# Password: <your NGC API key>
```

```{note}
스타터킷의 `marc.sh setup` 명령은 이 로그인을 **대신 수행하지 않습니다.** NVIDIA 계정은 참가자
본인의 것이므로, 위 로그인은 참가자가 한 번 직접 수행해야 합니다(한 번 수행하면 이후 계속 유지됩니다).
```

```{tip}
비밀번호를 화면에 입력하지 않고 명령 한 줄로 로그인하려는 경우(예: 자동화 스크립트) 아래와 같이
API Key 를 파이프로 전달할 수 있습니다.

    echo "<your NGC API key>" | docker login nvcr.io -u '$oauthtoken' --password-stdin
```

### 3. 시뮬레이션 플랫폼(연습용) 설치

시뮬레이션 플랫폼은 앞서 인증한 NGC 의 Isaac Sim 이미지 위에 대회 환경을 얹은 형태입니다. 이때
바탕이 되는 base 이미지(`marc-base:ros2-isaacsim-5.1`)는 레지스트리에서 내려받는 이미지가
아니라, 참가자 PC 에서 한 번 직접 빌드해야 하는 로컬 이미지입니다. 스타터킷의 `setup` 명령이 이
base 이미지 빌드를 대신 처리하므로, 처음에는 아래 한 줄만 실행하면 됩니다(최초 1회). 이 명령은
NGC 로그인 안내도 함께 표시합니다.

```bash
bash simulation-platform/marc.sh setup
```

base 이미지 빌드가 끝나면 마지막에 아래와 같은 안내가 출력됩니다(가운데 `...` 부분은 빌드 로그입니다).

```text
[marc] building base image (marc-base:ros2-isaacsim-5.1) - first time only, this takes a while.
...
[marc] setup complete. Next: bash simulation-platform/marc.sh platform
```

base 이미지 위에 얹는 플랫폼 이미지 자체는 다음 단계(4. 플랫폼 실행)의 `marc.sh platform` 이
자동으로 빌드하고 실행합니다. 이때 플랫폼에 필요한 콘텐츠는 공개 레지스트리(GHCR)에서 자동으로
가져오므로 별도의 인증이 필요하지 않습니다.

```{important}
**설치(빌드)에는 상당한 시간이 소요됩니다 — 정지된 것이 아닙니다.** 컴퓨터 사양과 네트워크 속도에
따라 짧게는 수십 분, 길게는 몇 시간까지 소요될 수 있습니다. 특히 최초 실행 시에는 용량이 큰 데이터를
내려받고 준비하는 과정이므로 더 오래 소요됩니다. 진행 중 진척이 없어 보이더라도 정상 동작이므로,
완료될 때까지 기다려야 합니다.
```

시뮬레이션 플랫폼에는 대회에 필요한 것들이 함께 들어 있습니다.

- 디지털 트윈 — 실제 세종대학교 캠퍼스를 그대로 재현한 가상 환경입니다.
- 로봇 — 바구니를 실은 4륜 이동 로봇과 6축 로봇팔.
- 센서 — 고정 CCTV 와 로봇에 달린 스테레오 카메라.
- ROS 2 인터페이스 — 로봇·센서와 표준 방식으로 명령·데이터를 주고받습니다.
- 공개 연습 시나리오 — 실제 문제와 같은 형식으로 미리 연습해 볼 수 있는 예제입니다.

또한 같은 설치로 데이터셋 생성기와 매니퓰레이션 훈련 도구(Trainer)도 함께 준비됩니다.

```{note}
빌드 과정에서는 시뮬레이션에 필요한 데이터를 인터넷에서 자동으로 내려받습니다. 네트워크
환경으로 인해 이 다운로드가 어렵거나 오프라인에서 빌드해야 하는 경우, 별도로 제공되는 콘텐츠 패키지를
미리 받아 압축을 푼 뒤 해당 데이터로 빌드하는 방법이 있습니다(결과물은 동일합니다). 콘텐츠 패키지를
받는 방법과 빌드 절차는 스타터킷 README 를 참고합니다.
```

### 4. 플랫폼 실행

이제 설치한 플랫폼을 실행합니다. 이 안내에서는 다음 단계에서 실행할 데모와 함께 동작하는
`marc2026_demo` 시나리오로 실행합니다. 플랫폼 폴더로 이동한 뒤, 실행할 시나리오를 `.env` 에 지정합니다.

```bash
cd simulation-platform
cp .env.example .env
```

```bash
# In simulation-platform/.env
ENV_MARC_SCENARIO=marc2026_demo
```

```{note}
스타터킷에 포함된 시뮬레이션 플랫폼의 기본값은 GUI 모드(`HEADLESS=false`)입니다 — 플랫폼의 3차원
뷰포트와 점수 패널이 창으로 표시됩니다. 컨테이너가 호스트의 화면(X 서버)에 접근할 수 있도록,
실행하기 전에 호스트에서 아래 명령을 한 번 실행합니다.

    xhost +local:root

화면이 없는 서버에서 실행하거나 GUI 가 필요 없으면 `.env` 에서 `HEADLESS=true` 로 바꿉니다(이 경우
xhost 는 필요 없습니다).
```

스타터킷에는 연습용 플랫폼 외에도 데이터셋 생성기와 매니퓰레이션 훈련 도구가 함께 포함되어 있으므로,
이 중 실행할 대상을 선택하여 지정해야 합니다. 연습용 플랫폼은 `platform` 입니다. 아래 두 명령은 동일하게
동작하므로 편의에 따라 선택합니다.

```bash
# (1) Run directly with docker compose
docker compose --profile platform up

# (2) Convenience wrapper (runs the command above)
bash marc.sh platform
```

```{note}
`docker compose up` 만 입력하면 아무것도 실행되지 않습니다. 위와 같이 실행할 대상(`platform`)을
반드시 지정해야 합니다(`marc.sh platform` 을 사용하면 이 지정이 자동으로 처리됩니다).
```

```{important}
**최초 실행에는 상당한 시간이 소요됩니다 — 정지된 것이 아닙니다.** 3차원 가상 캠퍼스 데이터를 불러오는 데
수 분(보통 2~5분, 다운로드 후 최초 실행은 더 오래)이 소요됩니다. 이 동안 프로그램 화면은 검게 표시되고,
운영체제가 창을 `"Isaac Sim" is not responding`(응답 없음) 상태로 표시하거나 경고창을 표시할 수 있습니다.
이는 정상 동작이므로 강제로 종료하지 말고 기다려야 합니다. 아래 로그가 표시되면 실행이 완료된 것입니다:

    [Runtime] Startup complete in <N>s
    Auto-plan: waiting for a participant to register...

이때 뷰포트에 연습용 씬이 나타나며, 플랫폼이 참가자 앱의 register 를 수신할 준비가 됩니다.
진행 상황은 `docker compose logs -f` 로 확인합니다.
```

```{figure} _static/not-responding.png
:alt: Isaac Sim 응답 없음 경고 대화상자
:width: 70%

최초 실행 중 나타날 수 있는 운영체제의 `"Isaac Sim" is not responding` 경고. 정상 동작이므로 강제 종료하지 말고 **Wait** 를 눌러 기다립니다.
```

### 5. 데모 실행

```bash
# Set your team id / token first, then go to the demo directory.
export MARC_TEAM_ID=u1
export MARC_TOKEN=<your-token>
cd demo                  # demo/ is at the starter-kit root
docker compose up        # organizers score with the same command
```

데모를 실행하면 에이전트가 동작하는 전체 흐름을 확인할 수 있습니다.

1. 에이전트가 플랫폼에 접속(등록)합니다.
2. Stage 1 문제를 받아, 대상을 어디에서 찾았는지 위치를 답안으로 제출합니다.
3. Stage 2 에서는 로봇이 목표 지점으로 이동합니다.

로봇이 움직이기 시작하면 참가자의 에이전트와 플랫폼이 정상적으로 연결되어 처음부터 끝까지 정상
동작한다는 의미입니다.

```{note}
**데모(베이스라인 코드)는 문제를 실제로 해결하는 프로그램이 아닙니다.** 흐름을 보여 주기 위해 Stage 1
답안은 미리 저장한 값을 제출하고, Stage 2 에서는 미리 정해 둔 위치로 로봇을 이동시켜 정해진
동작으로 물건을 집습니다. CCTV 영상을 실제로 분석하거나 스스로 판단하지는 않습니다.

데모는 참가자가 코드를 추가하기 시작하는 베이스라인 코드입니다. 플랫폼과의 통신 및 로봇 제어
연결은 이미 구현되어 있으므로, 미리 저장된 답안·위치를 생성하던 부분(모의 구현 부분)을 참가자의
실제 인식·판단 코드로 교체합니다.
```

---

## 환경 셋업

아래 항목은 반드시 충족해야 하는 소프트웨어 요구사항과 참고용인 개발·검증 기준 하드웨어로
구분됩니다. 표마다 "구분"을 함께 표기했으므로 어디까지가 필수이고 어디까지가 참고인지 확인합니다.

### 소프트웨어 요구사항 (정확히 맞춰야 함)

| 항목 | 구분 | 요구사항 |
|---|---|---|
| OS | 필수 | Ubuntu 22.04 LTS |
| NVIDIA 드라이버 | 필수 | production 드라이버(검증본 580.x, 최소 570)로 실행하십시오. 590+ 베타/개발자(Vulkan beta) 드라이버는 RTX 렌더러 크래시를 유발할 수 있습니다([FAQ](faq.md) 참조). |
| Docker | 필수 | Docker Engine + NVIDIA Container Runtime(GPU 사용) |
| Docker Compose | 필수 | v2(`docker compose`) |
| ROS 2 | 필수 | Humble |
| Python | 필수 | 3.10 (ROS 2 Humble 기준) |
| NGC 계정 | 필수 | NVIDIA NGC 계정(무료) + API Key ([Quickstart 2단계](#2-nvidia-ngc-로그인-nvcr-io) 참조) |

### 개발·검증 기준 하드웨어 (참고 — 최소 사양 아님)

주최 측은 아래 사양에서 플랫폼을 개발·검증했습니다. 최소 사양이 아닌 기준(참고) 사양이며, 더 낮은
사양에서도 동작할 수 있으나 성능은 달라질 수 있습니다. 특히 GPU 는 **NVIDIA RTX 계열이 필수**이며
VRAM 이 클수록 유리합니다.

| 항목 | 기준 사양 |
|---|---|
| OS | Ubuntu 22.04.5 LTS |
| CPU | Intel Core i7-12700K (12코어 / 20스레드) |
| RAM | 128 GB |
| GPU | NVIDIA RTX PRO 5000 Blackwell (48 GB VRAM) |
| GPU 드라이버 | 580.159.03 (CUDA 13.0 지원) |

### Docker · Docker Compose

플랫폼은 Docker 로 실행하므로, 아래 세 가지가 준비되어 있어야 합니다.

**1) Docker Engine.** 최신 Docker 를 설치합니다. 설치가 완료되면 다음 명령으로 확인합니다.

```bash
docker --version
```

아래와 같이 버전이 한 줄 출력되면 정상입니다(숫자는 환경마다 다릅니다).

```text
Docker version 27.3.1, build ...
```

**2) NVIDIA Container Runtime (GPU 사용).** 시뮬레이션은 GPU 를 사용하므로, 컨테이너가 GPU 에
접근할 수 있어야 합니다. 아래 명령으로 컨테이너 내부에서 GPU 가 인식되는지 확인합니다.

```bash
docker run --rm --gpus all nvidia/cuda:12.4.1-base-ubuntu22.04 nvidia-smi
```

컨테이너 내부에서 아래와 같이 그래픽카드 정보 표가 출력되면 정상입니다(참가자 PC 의 GPU 이름과
드라이버·CUDA 버전이 표시됩니다).

```text
+-----------------------------------------------------------------------------------------+
| NVIDIA-SMI 580.159.03             Driver Version: 580.159.03     CUDA Version: 13.0     |
|-----------------------------------------+------------------------+----------------------+
| GPU  Name                 Persistence-M | Bus-Id          Disp.A | Volatile Uncorr. ECC |
|=========================================+========================+======================|
|   0  NVIDIA RTX PRO 5000 Blac...    Off |   00000000:01:00.0  On |                  Off |
+-----------------------------------------+------------------------+----------------------+
```

`Failed to initialize NVML` 이나 `could not select device driver ... gpu` 같은 오류가 발생하면
드라이버 또는 NVIDIA Container Runtime 설정을 다시 확인합니다.

**3) Docker Compose v2.** 이 가이드의 모든 실행 명령은 최신 표준인 Docker Compose v2, 즉
띄어쓰기가 있는 `docker compose` 명령을 기준으로 합니다. 최신 Docker 를 설치하면 v2 가 함께
설치됩니다. 다음 명령으로 설치 여부를 확인합니다.

```bash
docker compose version
```

아래와 같이 버전이 출력되면 정상입니다(`v2` 로 시작하면 v2 입니다).

```text
Docker Compose version v2.29.7
```

```{note}
`docker compose` 명령이 동작하지 않는다면 Docker 버전이 오래된 것입니다. Docker 를 최신 버전으로
업그레이드하면 v2(`docker compose`)가 함께 설치됩니다.
```

### 시뮬레이션 플랫폼과 참가자 플랫폼 연동 구조

예선 및 본선 심사(채점) 환경에서는 시뮬레이션 플랫폼과 참가자 프로그램을 네트워크로
연결된 서로 다른 컴퓨터에서 실행하여 채점합니다. 다만 **개발 단계에서는 한 대의 컴퓨터에서 둘을
함께 실행해도 무방합니다.**

채점 환경과 동일한 조건에서 미리 검증하려는 경우, 두 컴퓨터를 기가비트(1 Gbps) 이상 LAN 으로
연결할 것을 권장합니다. 고정 CCTV 의 고해상도(8MP) 영상이 네트워크로 전송되므로 대역폭이
충분해야 안정적으로 동작합니다.

### 환경변수

| 변수 | 기본값 | 설명 |
|---|---|---|
| `MARC_TEAM_ID` | `u1` | 할당받은 팀 ID |
| `MARC_TOKEN` | — | 세션 토큰(필수) |
| `ROS_DOMAIN_ID` | `0` | ROS 2 도메인; 플랫폼과 일치해야 함 |
