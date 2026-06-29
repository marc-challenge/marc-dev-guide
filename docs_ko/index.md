# MARC 2026 개발자 가이드

**MARC (MetaSejong AI Robot Challenge) 2026** 개발자 가이드입니다.

참가팀 개발자가 깨끗한 머신에서 동작하는 에이전트까지 도달하는 데 필요한 모든 것을 다룹니다:
**환경 셋업 → SDK → 채점 → 제출 → 트러블슈팅**. 2026 대회는 **Isaac Sim 5.1.0** 기반이며
**VLA(Vision-Language-Action) / SAR(Search-and-Rescue)** 미션을 다룹니다.

> **상태 안내(초안 톤).** 본 가이드의 일정·이미지 태그·wheel 버전은 릴리스 동결 전까지
> **잠정 / 내부 검토** 단계입니다. 버전 문자열(예: `2026.1.0`, `v2026.x`)은 예시로 보십시오.

## 대상 독자

참가팀 개발자. **Python**, **ROS 2**, **Docker** 기초 지식을 전제합니다. 로보틱스/ML 배경이
있으면 도움이 되지만, 베이스라인 에이전트가 출발점을 제공합니다.

## 빠른 링크

- [시작하기](getting-started.md) — 30분 Quickstart + 환경 셋업
- [기술 가이드](technical-guide.md) — `marc_sdk` 레퍼런스 + 베이스라인 에이전트 + 매니퓰레이션 키트
- [API 레퍼런스](api-reference.md) — ROS 2 인터페이스(토픽·메시지·QoS·좌표계)
- [제출 가이드](submit-guide.md) — 제출 규격, 채점 방법론, 제출 절차
- [FAQ](faq.md) — 트러블슈팅 + 필수 공지

```{toctree}
:maxdepth: 2
:caption: 목차

getting-started
technical-guide
api-reference
submit-guide
faq
```

## 필수 공지 (먼저 읽으세요)

```{admonition} 필수 공지 3종
:class: warning

1. **심사 실행환경은 인터넷이 차단됩니다.** *빌드 시점*에는 인터넷을 사용할 수 있습니다(가중치·의존성을
   이미지에 baking). 그러나 *런타임*에는 외부 네트워크 접속·공개 API·다운로드가 **금지**됩니다.
2. **제3자 OSS / USD 자산은 각자의 라이선스를 따릅니다.** 사용·재배포하는 자산의 라이선스·attribution
   요건을 준수하십시오.
3. **대회 배경 장소는 변경될 수 있습니다.** 공개 배경 USD 는 연습용(**chungmu**) 1종뿐이며, 실제
   대회는 다른 배경일 수 있습니다.
```

전문은 [FAQ → 공지](faq.md#공지)를 참조하십시오.

## 버전

본 가이드는 Read the Docs 의 **버전드 문서**로 발행되며 릴리스 태그(`v2026.x`)에 정렬됩니다.
현재 초안의 목표 릴리스는 **2026.1.0**(잠정)입니다.

## 문의

대회·플랫폼·가이드 관련 문의는
**[marc2026@iotcoss.ac.kr](mailto:marc2026@iotcoss.ac.kr)** 로 보내주세요.
