# MARC 2026 Developer Guide

Welcome to the **MARC (MetaSejong AI Robot Challenge) 2026** developer guide.

## MARC 2026 at a glance

MARC 2026 is a robot-simulation competition in which you build a single **AI agent** that
understands a person's spoken request, locates the target in campus **CCTV** footage, and — when
asked — drives a robot to retrieve it. Everything runs in a digital twin of the Sejong University
campus on **Isaac Sim 5.1.0**, and the mission centers on **VLA (Vision-Language-Action)**
grounding together with a **SAR (Search-and-Rescue)** perception task. The contest has two stages:
**Stage 1 — find and report the location** (coordinate submission; required of every team) and
**Stage 2 — retrieve the object** with the robot (navigation + manipulation; optional). For the
full challenge story, rules, schedule, and organizers, see the
**[competition homepage](https://marc-challenge.github.io/en/challenge/)**.

## What this guide covers

This guide is your hands-on reference for **development and submission**. It walks you through the
whole journey in order — from a clean machine with nothing installed, to building and running your
own agent, to finally submitting it to the competition. Here is how each page helps you along the
way:

- **[Getting Started](getting-started.md)** — the first page to read. It checks the hardware and
  tools you need (Ubuntu, an NVIDIA GPU, Docker, ROS 2, and so on), then takes the shortest path to
  downloading the starter kit, bringing the platform up, and watching the demo agent move — in about
  **30 minutes**. Start here if you just want to see something running first.
- **[Technical Guide](technical-guide.md)** — once the demo runs, this is where you add your own
  "intelligence" on top of it. It explains the **participant SDK (`marc_sdk`)** you use to talk to
  the platform, the structure of the **baseline agent** you build from, and the **manipulation
  learning kit** for practising how the robot arm picks objects up. It points out exactly where to
  swap in your own implementation.
- **[API Reference](api-reference.md)** — the reference for the **contract** by which the robot and
  sensors actually communicate: the commands that drive the robot, the sensor inputs (CCTV, cameras,
  lidar), and the coordinate frames, message formats, and units — all laid out in tables. Open this
  when you need to know "what value do I send, where, and in what format?"
- **[Submission Guide](submit-guide.md)** — how to **score your agent on your own machine** to see
  how well it does, and how to prepare your submission in the right format and follow the submission
  procedure. It also covers how to read your score and per-round details after a run, and roughly how
  scoring works (the methodology).
- **[FAQ](faq.md)** — the page to check first when you get stuck. It gathers fixes for the problems
  teams hit most often (troubleshooting), along with the **notices you must read** before you take
  part.

For the competition rules, schedule, evaluation policy, and organizers, see the
[competition homepage](https://marc-challenge.github.io/en/challenge/).

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

```{admonition} Two required notices
:class: warning

1. **The evaluation runtime has no internet access.** You may use the internet *at build
   time* (to bake weights and dependencies into your image), but at runtime external
   network access, public APIs, and downloads are **prohibited**.
2. **The competition background location may change.** The only publicly distributed
   background USD is the practice scene (**chungmu**); the actual competition may use a
   different background.
```

See [FAQ → Notices](notices) for the full text.

## Contact

For questions about the challenge, the platform, or this guide, email
**marc2026@iotcoss.ac.kr**.
