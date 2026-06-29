# FAQ

## 트러블슈팅

### 뷰포트가 검정 화면 / 첫 실행 때 멈춘 것처럼 보임

**증상:** `docker compose up` 후 Isaac Sim 창의 **뷰포트가 검정**이고 제목이 *"New Stage\*"*,
로딩 바가 멈춘 듯 보입니다.

**정상입니다 — 기다리세요.** 최초 기동은 월드(씬·사람 포즈·랜드마크·로봇)를 구성하고 셰이더를
컴파일하므로 **수 분**(보통 2~5분, 첫 실행은 더 오래) 걸립니다. **강제 종료하지 마세요.** 로그에
`[Runtime] Startup complete in <N>s` 와 이어서 `Auto-plan: waiting for a participant to
register...` 가 나오면 기동 완료이며, 그때 씬이 나타납니다. 진행은 `docker compose logs -f` 로
확인하세요.

### ROS 2 Humble <-> Isaac Sim Python 충돌

**증상:** 플랫폼 기동 시 import 오류 / 잘못된 Python; 참가자 SDK(Python 3.10)와 Isaac Sim(Python
3.11)이 충돌.

**해결:** 셸을 분리합니다. Isaac Sim 셸에서 `PYTHONPATH`·`LD_LIBRARY_PATH` 의 `/opt/ros` 를
제거합니다(플랫폼 실행 스크립트가 이미 처리). 참가자 에이전트는 ROS 2 Humble(3.10) 셸에서, 플랫폼은
자체 셸에서 실행합니다.

### GPU 인식 실패

**NVIDIA Container Runtime** 설치, 호스트 드라이버 최신화, 컨테이너의 GPU 요청(`--gpus all` 또는
compose `deploy.resources` 블록)을 확인합니다. 호스트와 컨테이너 내부에서 `nvidia-smi` 로 검증합니다.

### `docker compose up` 실패: `unknown or invalid runtime name: nvidia`

compose 파일은 `runtime: nvidia` 를 요구합니다. 호스트에서 `docker run --gpus all` 이 동작하더라도
(CDI 경로) Docker 데몬에 **이름이 `nvidia` 인 런타임이 등록되지 않았을 수** 있습니다. 한 번 등록하고
Docker 를 재시작하세요:

```bash
sudo nvidia-ctk runtime configure --runtime=docker
sudo systemctl restart docker
docker info | grep -i runtimes   # 이제 "nvidia" 가 보여야 함
```

### DDS 통신 안 됨

두 머신이 **동일 `ROS_DOMAIN_ID`** 와 동일 LAN 을 공유하는지, 방화벽이 DDS(UDP, 디스커버리용
멀티캐스트)를 허용하는지 확인합니다. 데모는 `network_mode: host` 로 호스트 NIC 상에서
디스커버리합니다. 8MP CCTV 스트리밍에는 기가비트 이상 LAN 이 필요합니다.

### 빌드 실패

Dockerfile 이 `simulation_app/`, `resources/`, `scenarios/` 를 COPY 하므로 **빌드 컨텍스트는 리포
루트** 여야 합니다:

```bash
docker build -f simulation-platform/Dockerfile.practice -t marc-platform:practice .
```

또한 Isaac Sim **base 이미지** 를 pull 하고 라이선스에 동의했는지 확인하십시오(플랫폼은
Dockerfile-only 이며 프리빌트 이미지는 재배포하지 않습니다).

### 성능

프레임레이트나 VRAM 이 빠듯하면 해상도를 낮추고, 구독하는 동시 CCTV 스트림 수를 줄이고, 무거운 추론은
참가자 자신의 (별도) 하드웨어에서 수행하십시오.

### 이전 MARC 대회 환경을 재사용하는 경우 (Docker 충돌)

이전 MARC 대회에 참가했던 머신에서 그대로 개발하면, 그때 남은 Docker 이미지·컨테이너·볼륨이
충돌하거나 오래된 캐시가 잡힐 수 있습니다.

- 같은 태그(`:latest` 등)를 재사용하면 옛 이미지가 빌드/실행될 수 있으니 **새 이미지는 고유 태그로
  빌드/실행** 합니다.
- 옛 컨테이너·볼륨·네트워크를 정리합니다: `docker ps -a`, `docker volume ls`, `docker network ls`
  로 확인 후 불필요한 것을 제거(`docker system prune` 은 신중히 사용).
- 캐시가 의심되면 `docker build --no-cache` 로 다시 빌드합니다.
- 디스크 부족이나 옛 base 이미지 충돌 시 `docker image ls` 로 사용하지 않는 이미지를 제거합니다.

---

## 공지

다음 3종 공지는 **필수** 이며 빌드·제출 방식을 규정합니다.

### 1. 심사 실행환경은 인터넷이 차단됩니다

**빌드 시점** 에는 인터넷으로 모델 가중치·의존성을 이미지에 baking 할 수 있습니다. **런타임** 에는
외부 네트워크 접속·공개 API·다운로드가 **금지** 됩니다. 에이전트는 완전 자기완결형으로 설계하십시오.

### 2. 제3자 OSS / USD 라이선스 및 attribution

플랫폼·SDK·자산에는 각자의 라이선스를 가진 제3자 오픈소스 SW 와 USD 자산이 포함됩니다. 사용·재배포하는
모든 자산의 라이선스·attribution 요건을 준수하십시오. 통합 제3자 공지 목록이 공개 자료와 함께
제공됩니다.

### 3. 대회 배경 장소는 변경될 수 있습니다

공개 배경 USD 는 연습용(**chungmu**) 1종뿐입니다. 실제 대회는 **다른 배경** 일 수 있으므로, 연습 씬
레이아웃에 종속된 가정을 하드코딩하지 마십시오.

---

## 일반

**일정은 어디서 보나요?** 주요 일정(공개·제출·본선 발표·본선)은 **잠정** 이며, 여기서 상세히 다루지
않고 대회 홈페이지에 게시됩니다. 본선은 Xi'an(일자 내부 검토 중)입니다.

**Stage 2 도착지는 어디인가요?** 물품은 **지정된 장소** 로 배치합니다.
