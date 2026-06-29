# FAQ

## Troubleshooting

### Viewport is black / looks frozen on first launch

**Symptom:** after `docker compose up` the Isaac Sim window shows a **black viewport**, the
title reads *"New Stage\*"*, and the loading bar seems stuck.

**This is normal — wait.** First startup builds the world (scene, people poses, landmarks,
robot) and compiles shaders, which takes **several minutes** (2–5 min typical, longer on the
very first run). Do **not** kill it. Startup is done when the logs show
`[Runtime] Startup complete in <N>s` followed by
`Auto-plan: waiting for a participant to register...`; the scene then appears. Follow
progress with `docker compose logs -f`.

### ROS 2 Humble <-> Isaac Sim Python conflict

**Symptom:** import errors / wrong Python when launching the platform; the participant SDK
(Python 3.10) and Isaac Sim (Python 3.11) collide.

**Fix:** keep the shells separate. Remove `/opt/ros` from `PYTHONPATH` and
`LD_LIBRARY_PATH` in the Isaac Sim shell (the platform launch scripts already do this). Run
your participant agent in the ROS 2 Humble (3.10) shell, and the platform in its own.

### GPU not detected

Check the **NVIDIA Container Runtime** is installed, the host driver is current, and the
container requests the GPU (`--gpus all` or the compose `deploy.resources` block). Verify
with `nvidia-smi` on the host and inside the container.

### `docker compose up` fails: `unknown or invalid runtime name: nvidia`

The compose file requests `runtime: nvidia`. Even if `docker run --gpus all` works on your
host (CDI path), the **named `nvidia` runtime may not be registered** with the Docker daemon.
Register it once and restart Docker:

```bash
sudo nvidia-ctk runtime configure --runtime=docker
sudo systemctl restart docker
docker info | grep -i runtimes   # should now list "nvidia"
```

### DDS communication not working

Confirm both machines share the **same `ROS_DOMAIN_ID`**, are on the same LAN, and that the
firewall allows DDS (UDP, multicast for discovery). The demo uses `network_mode: host` so
discovery happens on the host NIC. 8MP CCTV streaming needs gigabit-or-better LAN.

### Build fails

The Dockerfiles COPY `simulation_app/`, `resources/`, and `scenarios/`, so the **build
context must be the repo root**:

```bash
docker build -f simulation-platform/Dockerfile.practice -t marc-platform:practice .
```

Also make sure you pulled the Isaac Sim **base image** and accepted its license (the
platform is Dockerfile-only; prebuilt images are not redistributed).

### Performance

If frame rate or VRAM is tight, reduce resolution, lower the number of concurrent CCTV
streams you subscribe to, and keep heavy inference on your own (separate) hardware.

### Reusing an environment from a past MARC challenge (Docker conflicts)

If you develop on a machine you used for an earlier MARC challenge, leftover Docker images,
containers, or volumes can conflict or serve stale cache.

- Reusing the same tag (e.g. `:latest`) may pick up an old image — **build and run new
  images under a unique tag**.
- Clean up old containers, volumes, and networks: inspect with `docker ps -a`,
  `docker volume ls`, `docker network ls` and remove what you no longer need (use
  `docker system prune` with care).
- If you suspect stale cache, rebuild with `docker build --no-cache`.
- Remove unused old base images with `docker image ls` if you hit disk-space or base-image
  conflicts.

---

## Notices

These three notices are **mandatory** and govern how you build and submit.

### 1. The evaluation runtime has no internet access

You may use the internet **at build time** to bake model weights and dependencies into your
image. At **runtime**, external network access, public APIs, and downloads are
**prohibited**. Design your agent to be fully self-contained.

### 2. Third-party OSS / USD licenses and attribution

The platform, SDK, and assets include third-party open-source software and USD assets, each
under its own license. Honour all license and attribution requirements for anything you use
or redistribute. A consolidated third-party notices list ships with the public materials.

### 3. The competition background location may change

The only publicly distributed background USD is the practice scene (**chungmu**). The actual
competition may use a **different background**; do not hard-code assumptions tied to the
practice scene's layout.

---

## General

**Where is the schedule?** Key dates (announcement, submission, finalist announcement,
finals) are **provisional** and published on the competition homepage rather than detailed
here. The finals are in Xi'an (date under internal review).

**What is the Stage 2 destination?** Items are delivered to the **designated location**.
