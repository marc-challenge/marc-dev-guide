# Getting Started

This page gets you from a clean machine to a running demo agent, then documents the full
environment you need to keep building.

> All version strings (image tags, wheel versions, dates) on this page are **provisional /
> under internal review**. Treat `2026.1.0` and `v2026.x` as examples until the release freeze.

---

## Quickstart (target: 30 minutes)

The shortest path: **get it → bring it up → run the demo**.

### 0. Confirm prerequisites

Make sure your machine meets the [environment setup](#environment-setup) below
(Ubuntu 22.04, NVIDIA RTX GPU, Docker + NVIDIA Container Runtime, ROS 2 Humble).

### 1. Get the starter kit

```bash
git clone https://github.com/marc-challenge/marc-starter-kit.git
cd marc-starter-kit
```

The starter kit bundles the SDK, the demo agent, Docker recipes, the public scenario, and
the **chungmu** practice background USD.

### 2. Build the platform / trainer locally (Dockerfile-only)

The simulation platform and trainer images are **Dockerfile-only**: prebuilt images are
**not** redistributed (Isaac Sim redistribution license). You pull the base image yourself
and build locally.

```bash
# Build context is the repo root (the Dockerfile COPYs simulation_app/, resources/, scenarios/).
docker build -f deploy/marc-dev-platform/Dockerfile.practice -t marc-platform:practice .
```

```{note}
The first build pulls the Isaac Sim base image and requires accepting its license. This
step needs internet — that is fine, the **build phase is online**. Only the *evaluation
runtime* is offline.
```

### 3. Bring up the runtime

```bash
docker compose up
```

`docker compose up` is the canonical entry point. A convenience wrapper (`marc.sh`) is also
provided for local use.

### 4. Install the SDK

```bash
pip install marc-sdk==2026.1.0
```

### 5. Run the demo agent

```bash
# From the demo directory; set your team id / token first.
export MARC_TEAM_ID=u1
export MARC_TOKEN=<your-token>
cd participant_sdk/demo
docker compose up        # same command the organizers use to score you
```

You should see the agent register, receive Stage 1 missions, submit groundings, and (in
Stage 2) drive the robot. If the robot moves, your loop is closed.

```{tip}
Every command on this page is copy-ready (`sphinx-copybutton`). When the real tags are
frozen, pull/build/install commands are checked **character-for-character** against the
published image tags and wheel version before release.
```

---

## Environment setup

| Item | Requirement |
|---|---|
| OS / HW | Ubuntu **22.04**, NVIDIA **RTX** GPU with sufficient VRAM. |
| Docker | Docker + **NVIDIA Container Runtime** (GPU pass-through). |
| Python | Participant SDK = **3.10** (ROS 2 Humble). Platform-internal = 3.11 (Isaac Sim, separate shell). |
| Middleware | ROS 2 **Humble**, **Fast DDS**. Align `ROS_DOMAIN_ID` across machines. |
| Topology | Your agent runs on **separate hardware** from the platform (same LAN / same ROS domain, DDS over the network). |

### Separate-hardware topology

The participant application is expected to run on a **different machine** from the
simulation platform. The two machines share a LAN and the **same `ROS_DOMAIN_ID`**; DDS
discovery and traffic flow over the network (UDP). The demo `docker-compose.yml` uses
`network_mode: host` so discovery happens on the host NIC.

Because 8MP CCTV imagery is streamed over the network, a **gigabit-or-better LAN** is
recommended.

### Python shell separation (critical)

System ROS 2 Humble runs on **Python 3.10**, while Isaac Sim runs on **Python 3.11**.
Mixing them breaks imports. The platform launch scripts remove `/opt/ros` paths from
`PYTHONPATH` and `LD_LIBRARY_PATH` so the Isaac Sim shell stays clean. See
[FAQ → Troubleshooting](faq.md#troubleshooting) if you hit import errors.

### Environment variables

| Variable | Default | Description |
|---|---|---|
| `MARC_TEAM_ID` | `u1` | Your assigned team id. |
| `MARC_TOKEN` | — | Session token (required). |
| `ROS_DOMAIN_ID` | `0` | ROS 2 domain; must match the platform. |

```{note}
The agent is configured via **`MARC_*`** environment variables such as `MARC_TOKEN` and `ROS_DOMAIN_ID`.
```
