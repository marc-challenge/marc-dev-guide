# MARC 2026 Developer Guide

Welcome to the **MARC (MetaSejong AI Robot Challenge) 2026** developer guide.

This guide covers everything a participating team needs to go from a clean machine
to a working agent: **environment setup → SDK → scoring → submission → troubleshooting**.
The 2026 challenge is built on **Isaac Sim 5.1.0** and centers on a
**VLA (Vision-Language-Action) / SAR (Search-and-Rescue)** mission set.

> **Status note (draft tone).** Dates, image tags, and wheel versions in this guide are
> **provisional / under internal review** until the release freeze. Treat version strings
> (e.g. `2026.1.0`, `v2026.x`) as examples.

## Who this is for

Developers on participating teams. Working knowledge of **Python**, **ROS 2**, and
**Docker** is assumed. Robotics/ML background helps but the baseline agent gives you a
running start.

## Quick links

- [Getting Started](getting-started.md) — 30-minute Quickstart + environment setup
- [Technical Guide](technical-guide.md) — `marc_sdk` reference + baseline agent + manipulation kit
- [API Reference](api-reference.md) — ROS 2 interface (topics, messages, QoS, frames)
- [Submission Guide](submit-guide.md) — submission format, scoring methodology, submission procedure
- [FAQ](faq.md) — troubleshooting + required notices

```{toctree}
:maxdepth: 2
:caption: Contents

getting-started
technical-guide
api-reference
submit-guide
faq
```

## Important notices (read first)

```{admonition} Three required notices
:class: warning

1. **The evaluation runtime has no internet access.** You may use the internet *at build
   time* (to bake weights and dependencies into your image), but at runtime external
   network access, public APIs, and downloads are **prohibited**.
2. **Third-party OSS / USD assets carry their own licenses.** Honour all license and
   attribution terms for assets you use or redistribute.
3. **The competition background location may change.** The only publicly distributed
   background USD is the practice scene (**chungmu**); the actual competition may use a
   different background.
```

See [FAQ → Notices](faq.md#notices) for the full text.

## Versioning

This guide is published as **versioned documentation** on Read the Docs and is aligned to
release tags (`v2026.x`). The current draft targets release **2026.1.0** (provisional).

## Contact

For questions about the challenge, the platform, or this guide, email
**[marc2026@iotcoss.ac.kr](mailto:marc2026@iotcoss.ac.kr)**.
