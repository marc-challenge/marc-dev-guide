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

### 2. Log in to NVIDIA NGC (`nvcr.io`)

The platform / dataset-gen images are **Dockerfile-only**, so you pull the Isaac Sim base image
(`nvcr.io/nvidia/isaac-sim:5.1.0`) **under your own account** and build locally — pulling it
yourself means **you accept the Isaac Sim EULA as the licensee**. That requires an NGC login.

1. **Create a free account** at [ngc.nvidia.com](https://ngc.nvidia.com) and sign in.
2. **Generate an API key** — top-right profile → **Setup → Generate API Key** (or
   *Generate Personal Key*). The key is **shown only once**; copy it immediately.
3. **Log in to the registry.** The username is the literal string `$oauthtoken`; the
   password is your API key.

```bash
docker login nvcr.io
# Username: $oauthtoken      ← this exact string, no quotes
# Password: <your NGC API key>
```

```{tip}
Non-interactive (CI) login:
`echo "<API_KEY>" | docker login nvcr.io -u '$oauthtoken' --password-stdin`.
The `marc.sh setup` wrapper only *reminds* you to log in — it never logs in for you, since
the credentials are yours.
```

### 3. Build the platform / dataset-gen locally (Dockerfile-only)

The simulation platform and dataset-gen (object-detection label generator) images are **Dockerfile-only**: prebuilt images are
**not** redistributed (Isaac Sim redistribution license). With NGC login in place, build
locally — the build pulls the base image you just authenticated for.

```bash
# Build context is the repo root (the Dockerfile COPYs simulation_app/, resources/, scenarios/).
docker build -f simulation-platform/Dockerfile.practice -t marc-platform:practice .
```

```{note}
The first build pulls the Isaac Sim base image (hence the NGC login above). This step
needs internet — that is fine, the **build phase is online**. Only the *evaluation
runtime* is offline.
```

```{note}
At build time the simulation content is pulled from GHCR by default. **If GHCR access is
difficult** (network environment, etc.), use the **fallback path** that builds from the
local content bundled in the kit — the result is identical. (See the starter-kit README for
the fallback flag and steps.)
```

### 4. Bring up the runtime

The compose file groups services under profiles (`platform`, `dataset-gen`, `manip-trainer`);
pick the profile you want. For the practice runtime use `platform`:

```bash
# Canonical (compose with profile)
docker compose -f simulation-platform/docker-compose.yml --profile platform up

# Or the convenience wrapper
bash simulation-platform/marc.sh platform
```

```{note}
`docker compose up` alone selects no service because every service in
`simulation-platform/docker-compose.yml` is gated behind a profile. Pass `--profile platform`
(or use `marc.sh platform`, which sets it for you).
```

```{important}
**First startup is slow — it is not frozen.** Building the world (scene, people poses,
landmarks, robot) plus shader compilation takes **several minutes** (typically 2–5 min, and
longer on the very first run while caches warm up). During this time the **viewport stays
black**, the title may read *"New Stage\*"*, and the loading bar can appear stuck. This is
normal — **wait, do not kill it.** Startup is complete only when the logs show:

    [Runtime] Startup complete in <N>s
    Auto-plan: waiting for a participant to register...

At that point the chungmu scene appears in the viewport and the platform is ready for your
agent to register. Watch progress with `docker compose logs -f`.
```

### 5. Reference the SDK

```bash
# Standard (Docker submission): marc_sdk ships as SOURCE — your image COPYs it and adds
#   it to PYTHONPATH (see demo/Dockerfile). No pip step needed.
# Host-side / local dev only (ROS2 Humble sourced): install from the starter-kit ROOT —
pip install -e .                                   # run where pyproject.toml lives (kit root), NOT inside marc_sdk/
# or the release wheel:
pip install marc_sdk-2026.1.0-py3-none-any.whl     # attached to the marc-starter-kit GitHub Release
```

### 6. Run the demo agent

```bash
# From the kit root, switch to the demo directory; set your team id / token first.
export MARC_TEAM_ID=u1
export MARC_TOKEN=<your-token>
cd demo                  # demo/ ships at the starter-kit root
docker compose up        # same command the organizers use to score you
```

```{note}
`cd participant_sdk/demo` is the path inside the organizer monorepo. The public starter kit
ships the demo at `demo/` directly under the kit root.
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
| NGC account | **NVIDIA NGC account** (free) + **API key** — required to pull the Isaac Sim base image from `nvcr.io` (see [Quickstart step 2](#2-log-in-to-nvidia-ngc-nvcr-io)). |
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
