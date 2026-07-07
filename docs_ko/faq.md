# FAQ

## 트러블슈팅

### 뷰포트가 검정 화면 / 첫 실행 때 멈춘 것처럼 보임

**증상:** `docker compose up` 후 Isaac Sim 창의 뷰포트가 검게 보이고 제목이 `"New Stage*"`,
로딩 바가 정지된 것처럼 보입니다.

**정상 동작입니다.** 최초 기동은 3차원 가상 캠퍼스 데이터를 불러오므로 수 분(보통 2~5분,
첫 실행은 더 오래) 걸리며, 그동안 강제 종료하지 마십시오. 로그에
`[Runtime] Startup complete in <N>s` 와 이어서 `Auto-plan: waiting for a participant to
register...` 가 나오면 기동 완료이며, 그때 씬이 나타납니다. 진행은 `docker compose logs -f` 로
확인하십시오.

### ROS 2 Humble <-> Isaac Sim Python 충돌

**증상:** 플랫폼 기동 시 import 오류 / 잘못된 Python; 참가자 SDK(Python 3.10)와 Isaac Sim(Python
3.11)이 충돌.

**해결:** 셸을 분리합니다. Isaac Sim 셸에서 `PYTHONPATH`·`LD_LIBRARY_PATH` 의 `/opt/ros` 를
제거합니다(플랫폼 실행 스크립트가 이미 처리). 참가자 에이전트는 ROS 2 Humble(3.10) 셸에서, 플랫폼은
자체 셸에서 실행합니다.

### GPU 인식 실패

NVIDIA Container Runtime 설치, 호스트 드라이버 최신화, 컨테이너의 GPU 요청(`--gpus all` 또는
compose `deploy.resources` 블록)을 확인합니다. 호스트와 컨테이너 내부에서 `nvidia-smi` 로 검증합니다.

### 기동 직후 RTX 렌더러 크래시 (Segmentation fault)

**증상:** GPU 는 정상 인식되고 익스텐션도 모두 로드되지만, 로그에 `rclpy loaded` 가 찍힌 직후
씬을 불러오는 도중 프로그램이 종료됩니다. 로그 마지막에는 `librtx.scenedb.plugin.so` 또는
`libcarb.scenerenderer-rtx` 프레임과 함께 `Segmentation fault` 가 남습니다.

**원인:** 그래픽카드 자체의 문제가 아니라 드라이버가 원인인 경우가 많습니다. Isaac Sim 5.1 이
검증한 production 드라이버(580.159.03)보다 지나치게 앞선 베타/개발자(Vulkan beta)
드라이버(예: 595.71.05 등 590 번대)에서는 RTX 가 씬을 빌드하는 도중 크래시가 발생합니다(정상
카드인 RTX 4090 에서도 재현됨).

**해결:** 먼저 설치된 드라이버 버전을 확인합니다.

```bash
nvidia-smi --query-gpu=driver_version --format=csv,noheader
```

아래처럼 한 줄로 드라이버 버전이 출력됩니다. 여기서 590 번대 이상의 베타/개발자 드라이버가
나오면 원인일 가능성이 높습니다.

```text
595.71.05
```

이 경우 드라이버를 production 계열(검증본 580.x, 최소 570)로 교체합니다. 교체한 뒤에는 이전
드라이버로 만들어진 셰이더 캐시를 비우고 다시 실행합니다(캐시 경로는 플랫폼 폴더 기준입니다).

```bash
rm -rf ../.runtime-data/cache/*
```

그래도 같은 지점에서 종료된다면, 2순위로 BIOS 에서 IOMMU(VT-d) 를 끄고 재시도합니다.

### `docker compose up` 실패: `unknown or invalid runtime name: nvidia`

compose 파일은 `runtime: nvidia` 를 요구합니다. 호스트에서 `docker run --gpus all` 이 동작하더라도
(CDI 경로) Docker 데몬에 이름이 `nvidia` 인 런타임이 등록되지 않았을 수 있습니다. 한 번 등록하고
Docker 를 재시작하십시오:

```bash
sudo nvidia-ctk runtime configure --runtime=docker
sudo systemctl restart docker
docker info | grep -i runtimes   # "nvidia" should now appear
```

### DDS 통신 안 됨

두 머신이 동일 `ROS_DOMAIN_ID` 와 동일 LAN 을 공유하는지, 방화벽이 DDS(UDP, 디스커버리용
멀티캐스트)를 허용하는지 확인합니다. 데모는 `network_mode: host` 로 호스트 NIC 상에서
디스커버리합니다. 8MP CCTV 스트리밍에는 기가비트 이상 LAN 이 필요합니다.

플랫폼은 ROS 2 Humble 의 기본 미들웨어인 Fast DDS(RMW)를 사용합니다. 참가자도 기본 설정을
그대로 두는 것을 권장합니다. RMW 를 다른 것(예: Cyclone DDS)으로 바꾸면 서로 통신(디스커버리)이
안 될 수 있습니다.

### 빌드 실패: `marc-base:ros2-isaacsim-5.1: pull access denied`

**증상:** 플랫폼 빌드가 `marc-base:ros2-isaacsim-5.1: pull access denied, repository does not
exist` 로 실패합니다.

**원인:** 플랫폼 이미지의 바탕이 되는 base 이미지(`marc-base:ros2-isaacsim-5.1`)는 레지스트리에서
내려받는 이미지가 아니라 참가자 PC 에서 직접 빌드하는 로컬 이미지입니다. 이 base 이미지를 먼저
빌드하지 않으면 pull 을 시도하다 위 오류가 납니다.

**해결:** [시작하기 3단계](getting-started.md)의 `marc.sh setup` 을 먼저 실행하여 base 이미지를
빌드합니다(최초 1회). 이 명령은 NGC 로그인 안내도 함께 표시합니다.

```bash
bash simulation-platform/marc.sh setup
```

base 이미지가 빌드되었는지는 아래 명령으로 확인할 수 있습니다.

```bash
docker image ls marc-base:ros2-isaacsim-5.1
```

성공했다면 아래와 같이 이미지가 한 줄 표시됩니다.

```text
REPOSITORY   TAG                 IMAGE ID       CREATED         SIZE
marc-base    ros2-isaacsim-5.1   0123456789ab   3 minutes ago   XX.XGB
```

### 공개(public) content 이미지인데도 빌드가 `401 Unauthorized` 로 실패

**증상:** content 이미지를 공개(anonymous pull)로 열어 두었는데도 플랫폼 빌드가 아래와 같은
오류로 실패합니다.

```text
failed to fetch anonymous token: unexpected status from GET request ... 401 Unauthorized
```

**원인:** 이미지 자체는 공개로 열려 있으나, 참가자 PC 의 `~/.docker/config.json` 에 예전에 로그인해
둔 `ghcr.io` 자격증명이 만료된 채 남아 있는 경우입니다. 빌드 도구(buildx)가 이 만료된 토큰을 먼저
보내면서 익명 접근으로 넘어가지 못하고 401 을 받습니다.

**해결:** `ghcr.io` 에서 로그아웃하여 익명 접근으로 떨어지게 한 뒤, 이미지를 단독으로 한 번 받아
정상적으로 열리는지 확인합니다.

```bash
docker logout ghcr.io
docker pull ghcr.io/marc-challenge/marc-platform-content:2026   # 단독 검증
```

성공하면 레이어를 받은 뒤 마지막에 아래와 같은 `Status:` 줄이 출력됩니다.

```text
2026: Pulling from marc-challenge/marc-platform-content
...
Status: Downloaded newer image for ghcr.io/marc-challenge/marc-platform-content:2026
```

### 성능

프레임레이트나 VRAM 이 부족하면 해상도를 낮추고, 구독하는 동시 CCTV 스트림 수를 줄이고, 무거운 추론은
참가자의 별도 하드웨어에서 수행하십시오.

### 이전 MARC 대회 환경을 재사용하는 경우 (Docker 충돌)

이전 MARC 대회에 참가했던 머신에서 그대로 개발하면, 그때 남은 Docker 이미지·컨테이너·볼륨이
충돌하거나 오래된 캐시가 적용될 수 있습니다.

- 같은 태그(`:latest` 등)를 재사용하면 옛 이미지가 빌드/실행될 수 있으니 새 이미지는 고유 태그로
  빌드/실행 합니다.
- 옛 컨테이너·볼륨·네트워크를 정리합니다: `docker ps -a`, `docker volume ls`, `docker network ls`
  로 확인 후 불필요한 것을 제거(`docker system prune` 은 신중히 사용).
- 캐시가 의심되면 `docker build --no-cache` 로 다시 빌드합니다.
- 디스크 부족이나 옛 base 이미지 충돌 시 `docker image ls` 로 사용하지 않는 이미지를 제거합니다.

---

## 공지

다음 3종 공지는 필수이며 빌드·제출 방식을 규정합니다.

### 1. 심사 실행환경은 인터넷이 차단됩니다

빌드 시점에는 인터넷으로 모델 가중치·의존성을 이미지에 baking 할 수 있습니다. 그러나 런타임에는
외부 네트워크 접속·공개 API·다운로드가 **금지**됩니다. 에이전트는 완전 자기완결형으로 설계하십시오.

### 2. 제3자 OSS / USD 라이선스 및 attribution

플랫폼·SDK·자산에는 각자의 라이선스를 가진 제3자 오픈소스 SW 와 USD 자산이 포함됩니다. 사용·재배포하는
모든 자산의 라이선스·attribution 요건을 준수하십시오. 통합 제3자 공지 목록이 공개 자료와 함께
제공됩니다.

### 3. 대회 배경 장소는 변경될 수 있습니다

공개되는 배경 USD 는 연습용 1종뿐입니다. 실제 대회는 다른 배경일 수 있으므로, 연습 씬
레이아웃에 종속된 가정을 하드코딩하지 마십시오.

---

## 일반

**일정은 어디에서 확인할 수 있습니까?** 주요 일정(공개·제출·본선 발표·본선)은 잠정이며, 여기서 상세히
다루지 않고 대회 홈페이지에 게시됩니다. 본선은 Xi'an(일자 내부 검토 중)입니다.

**Stage 2 도착지는 어디입니까?** 물품은 "지정된 장소" 로 배치합니다.
