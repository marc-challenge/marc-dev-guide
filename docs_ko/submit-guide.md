# 제출 가이드

이 페이지는 **제출 JSON 규격**, **채점 방법론**(방법론만 — 수치 비공개), **로컬 채점**, **제출
절차**를 다룹니다.

> 잠정 안내: 아래 태그·일정·예선 채점 HW 스펙은 **내부 검토** 단계이며 변경될 수 있습니다.

---

## 제출 규격

JSON 파일을 업로드하지 않습니다. 에이전트가 실행 중 **ROS 2 로 결과를 제출** 하며, "제출물"은
Docker 화된 에이전트입니다([절차](#제출-절차) 참조). 에이전트가 발행하는 결과 payload 는 다음과 같습니다.

### Stage 1 — grounding (msg 301)

라운드당 1회 제출, 단일 대상 모델.

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

- 분실물 문제는 `relation`(공간 관계)을 제공합니다.
- SAR 사람 문제는 `target_type: "person"` 과 `situation`
  (`accident` / `emergency` / `abnormal` / `normal`)을 제공합니다.

### Stage 2 — 해석 (msg 311) + 완료 (msg 302)

Stage 2 는 두 단계입니다: `task_description` 에 대해 grounding 1회 제출(msg 301 과 동일 payload),
이후 navigation 과 pick-and-place 로 물품을 **지정된 장소** 에 배치하고, 마지막에 `task_complete`
(msg 302, 취소 불가)를 발행합니다.

SDK 가 전 과정을 감쌉니다 — [기술 가이드 → 제출 API](technical-guide.md#제출-api)를 참조하십시오.

---

## 채점 방법론

채점은 **방법론만** 공개합니다. 정확한 임계값·가중치·튜닝 상수는 **비공개**입니다.

- **카메라 선택** — 대상에 맞는 카메라를 골랐는가?
- **객체 / 상황 해석** — `target_type`, 사람의 경우 `situation`(위험·이상 인지) 카테고리.
- **랜드마크 + 관계** — 올바른 기준 랜드마크와 공간 관계(분실물).
- **anchor / target 위치추정** — 추정 3D 좌표의 정확도. 거리 기반 부분 점수로 채점(가까울수록
  높음; 정확한 거리 상수는 비공개).
- **Stage 2 수거** — 제한 시간 내 지정된 장소로 물품 배치 성공 여부.

라운드 결과(msg 401)는 세부 점수와 `total` 을 반환하고, 최종 결과는 Stage 1(라운드 평균)과 Stage 2
를 stage 가중치로 결합합니다. 거리 임계값·획득 반경·시드·가중치의 **값** 은 의도적으로 생략합니다.

```{admonition} 절대 공개하지 않는 것
:class: warning
정답 좌표, `hash_seed`, 채점 상수(예: 거리/획득 임계값), 운영 백엔드, 런타임 정답(GT)은 본 가이드의
범위 밖입니다. 방법론만 서술합니다.
```

---

## 로컬 채점

제출 전, 스타터킷의 연습 채점 도구로 **공개 연습 시나리오** 에 대해 자기 점수를 추정하십시오. 로컬
점수는 참고용일 뿐이며, 공식 실행은 미공개 대회 시나리오·배경을 사용합니다.

---

## 제출 절차

참가자 애플리케이션은 **Docker 로 개발·제출** 합니다(필수). 표준 진입점은 `docker compose up` 입니다.

1. **Docker 로 개발.** `docker compose up` 으로 빌드/실행하고, `MARC_TEAM_ID` / `MARC_TOKEN` 을
   `docker-compose.yml` 에 기입합니다.
2. **표준 진입점 검증.** 주최측은 *동일한* `docker compose up` 으로 채점하므로, fresh clone 에서
   깨끗이 빌드·실행되는지 확인하십시오.
3. **office 계정을 collaborator 로 추가.** 에이전트를 **Private** 리포에 push 하고
   **`marc-challenge-office`** 를 collaborator 로 추가합니다. 토큰은 Private 리포의 compose 파일에만
   두십시오(공개 리포 금지).
4. **동결 및 태그.** 주최측이 동결 태그를 clone 하여 팀을 **순차** 채점합니다.

```{admonition} 런타임 인터넷 차단
:class: warning
심사 실행환경은 **인터넷이 차단** 됩니다. 모든 가중치·의존성을 빌드 시점에 이미지에 baking 하고,
런타임에는 어떤 다운로드나 공개 API 호출도 하지 마십시오.
```

---

## 예선 채점 하드웨어 (참고)

에이전트 규모 산정을 위한 참고값이며 잠정입니다.

| 항목 | 스펙 |
|---|---|
| OS | Ubuntu 22.04 |
| CPU | Intel Core **i7-12700K** |
| GPU | **RTX PRO 5000, 48 GB** |
| 메모리 | 약 125 GiB |

참가자 애플리케이션은 플랫폼과 **별도 하드웨어**(동일 LAN / ROS 도메인, DDS 네트워크 경유)에서
실행되며, 팀은 순차 채점됩니다.
