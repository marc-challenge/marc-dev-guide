# 제출 가이드

이 페이지는 완성한 참가자 애플리케이션을 대회에 제출하는 방법을 설명합니다. 제출물은 JSON 파일이나 학습된 모델이 아니라, `docker compose up` 한 줄로 실행되는 참가자 애플리케이션 전체(리포지토리)입니다.

> 잠정 안내: 아래 일정·collaborator 계정·예선 채점 HW 스펙은 내부 검토 단계이며 변경될 수 있습니다.

---

## 무엇을 제출하나

제출물은 "정답"을 담은 파일이 아니라 "정답을 스스로 만들어 제출하는 프로그램"입니다. 주최측은 참가자가 올린 리포지토리를 그대로 clone 하여 `docker compose up` 한 줄로 실행하고, 실행된 에이전트가 대회가 진행되는 동안 ROS 2 로 답안을 제출합니다.

채점 대상은 그 프로그램이 실제로 낸 성적입니다. 제출하기 전에 자기 점수를 미리 확인하는 방법은 [기술 가이드 → 시뮬레이션 플랫폼(연습용)](technical-guide.md)의 "참가자 프로그램 실행 및 점수 확인"을 참고하십시오. 답안 payload 의 정확한 필드 규격은 [API 레퍼런스](api-reference.md)에 있습니다.

---

## 마감일에 할 일

코드 제출 마감일에는 다음 두 가지를 반드시 완료해야 합니다. 이 두 가지가 곧 "제출"입니다.

1. 팀의 GitHub Private 리포지토리 `master` 브랜치에 push 합니다. 모든 MARC 리포지토리는 Gitflow 를 따르며, `master` 가 제출·채점 대상이 되는 안정 브랜치입니다.
2. 리포지토리 설정에서 `marc-challenge-office` 계정을 collaborator 로 추가합니다. 리포지토리가 Private 이므로, 이 초대가 없으면 주최측이 리포지토리를 clone 할 수 없습니다.

주최측 안내에 따라 제출 시점 커밋에 태그를 다는 경우도 있습니다. 주최측은 이렇게 동결된 지점을 clone 하여 팀을 한 팀씩 순차적으로 채점합니다.

```{admonition} 반드시 Private 리포지토리로 제출하십시오
:class: warning
공개(Public) 리포지토리에 올리면 아래에서 설명하는 토큰이 그대로 노출됩니다. Private 리포지토리에 `marc-challenge-office` 를 collaborator 로 추가하는 것이 유일한 제출 경로입니다.
```

---

## `docker compose up` 한 줄로 실행되게 만들기

주최측은 참가자 리포지토리를 새로 clone 한 상태에서 정확히 `docker compose up` 만 실행합니다. 다른 스크립트를 먼저 돌리거나 파일을 손으로 배치하는 등의 추가 단계는 개입하지 않습니다. 따라서 제출 전에 다음을 보장해야 합니다.

- 리포지토리 루트에 `docker-compose.yml` 이 있고, `docker compose up` 만으로 이미지 빌드부터 에이전트 실행까지 한 번에 끝나야 합니다.
- 개발하던 폴더가 아니라 다른 위치에 리포지토리를 새로 clone 하여, 그 상태에서 `docker compose up` 이 그대로 동작하는지 반드시 확인하십시오. 로컬에만 있는 파일이나 이미 받아 둔 캐시에 의존하면 주최측 환경에서 실패합니다.

스타터킷의 `demo/docker-compose.yml` 을 출발점으로 삼으면, 표준 진입점과 빌드 컨텍스트가 이미 맞춰져 있어 그대로 이어서 개발할 수 있습니다.

---

## 환경변수 설정

팀 식별과 인증에 필요한 값은 compose 파일의 `environment:` 에 기입합니다. 아래는 스타터킷 `demo/docker-compose.yml` 의 해당 부분입니다.

```yaml
# docker-compose.yml (participant app)
services:
  agent:
    environment:
      MARC_TEAM_ID: "u1"                    # replace with your assigned team ID
      MARC_TOKEN:   "PASTE_YOUR_TOKEN_HERE" # replace with your assigned token
      ROS_DOMAIN_ID: "0"                    # same value as the platform machine
      RMW_IMPLEMENTATION: "rmw_fastrtps_cpp"
```

- `MARC_TEAM_ID` 와 `MARC_TOKEN` 에는 배정받은 팀 식별자와 토큰을 채웁니다. 이 값으로 채점 결과가 팀에 귀속됩니다.
- `ROS_DOMAIN_ID` 와 `RMW_IMPLEMENTATION`, 그리고 `network_mode: host` 는 스타터킷 compose 의 기본값을 그대로 두면 됩니다. 참가자 애플리케이션과 플랫폼이 같은 LAN·같은 ROS 도메인에서 DDS 로 통신하도록 이미 맞춰져 있습니다.
- 토큰은 Private 리포지토리의 compose 파일에만 두십시오. 공개 리포지토리나 공개 이미지에 넣지 마십시오.

```{admonition} 런타임 인터넷 차단
:class: warning
심사 실행환경은 인터넷이 차단됩니다. 모든 가중치·의존성을 빌드 시점에 이미지에 포함(baking)시키고, 런타임에는 어떤 다운로드나 공개 API 호출도 하지 마십시오. 빌드 시점에는 인터넷을 사용할 수 있습니다.
```

---

## 예선 채점 하드웨어 (참고)

에이전트 규모를 가늠하기 위한 참고값이며 잠정입니다.

| 항목 | 스펙 |
|---|---|
| OS | Ubuntu 22.04 |
| CPU | Intel Core i7-12700K |
| GPU | RTX PRO 5000, 48 GB |
| 메모리 | 약 125 GiB |

참가자 애플리케이션은 플랫폼과 별도의 하드웨어에서 실행되며(동일 LAN·ROS 도메인, DDS 네트워크 경유), 팀은 한 팀씩 순차적으로 채점됩니다.
