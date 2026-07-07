# FAQ

## Troubleshooting

### Viewport is black / looks frozen on first launch

**Symptom:** after `docker compose up` the Isaac Sim window shows a **black viewport**, the
title reads *"New Stage\*"*, and the loading bar seems stuck.

**This is normal — wait.** Loading the 3D virtual campus data takes several minutes (2–5 min
typical, longer on the very first run); do not kill it during that time. Startup is done when
the logs show `[Runtime] Startup complete in <N>s` followed by
`Auto-plan: waiting for a participant to register...`, and the scene then appears. Follow
progress with `docker compose logs -f`.

### ROS 2 Humble <-> Isaac Sim Python conflict

**Symptom:** import errors occur or the wrong Python is picked up when launching the platform.
The participant SDK (Python 3.10) and Isaac Sim (Python 3.11) collide.

**Fix:** keep the shells separate. Remove `/opt/ros` from `PYTHONPATH` and `LD_LIBRARY_PATH`
in the Isaac Sim shell (the platform launch scripts already do this). Run your participant
agent in the ROS 2 Humble (3.10) shell, and the platform in its own shell.

### GPU not detected

**Symptom:** the GPU is not visible inside the container, or the run fails with an error like
`Failed to initialize NVML` or `could not select device driver`.

**Fix:** check that the NVIDIA Container Runtime is installed, the host driver is current, and
the container requests the GPU (`--gpus all` or the compose `deploy.resources` block). Verify
with `nvidia-smi` both on the host and inside the container.

### RTX renderer crash right after startup (Segmentation fault)

**Symptom:** the GPU is detected fine and all extensions load, but the program exits while
loading the scene right after the log prints `rclpy loaded`. The end of the log shows a
`librtx.scenedb.plugin.so` or `libcarb.scenerenderer-rtx` frame followed by
`Segmentation fault`.

**Cause:** this is often the driver, not the card itself. A beta/developer (Vulkan beta) driver
too far ahead of the production driver Isaac Sim 5.1 validated (580.159.03) — e.g. 595.71.05 or
another 590-series — crashes while RTX builds the scene (reproduced even on a healthy
RTX 4090).

**Fix:** first check the installed driver version.

```bash
nvidia-smi --query-gpu=driver_version --format=csv,noheader
```

The driver version prints on one line as below. If it is a 590-series or newer beta/developer
driver, it is likely the cause.

```text
595.71.05
```

In that case, switch to a production-line driver (validated 580.x, min 570). After switching,
clear the shader cache built by the old driver and run again (the cache path is relative to the
platform folder).

```bash
rm -rf ../.runtime-data/cache/*
```

If it still exits at the same point, as a secondary step disable IOMMU (VT-d) in BIOS and retry.

### `docker compose up` fails: `unknown or invalid runtime name: nvidia`

**Symptom:** `docker compose up` fails with `unknown or invalid runtime name: nvidia`.

**Cause:** the compose file requests `runtime: nvidia`, but even if `docker run --gpus all`
works on your host (CDI path), the named `nvidia` runtime may not be registered with the Docker
daemon.

**Fix:** register it once and restart Docker.

```bash
sudo nvidia-ctk runtime configure --runtime=docker
sudo systemctl restart docker
docker info | grep -i runtimes   # should now list "nvidia"
```

### DDS communication not working

**Symptom:** the participant application and the platform cannot find each other (discovery
fails) or topics do not flow.

**Fix:** confirm both machines share the same `ROS_DOMAIN_ID`, are on the same LAN, and that
the firewall allows DDS (UDP, multicast for discovery). The demo uses `network_mode: host` so
discovery happens on the host NIC. 8MP CCTV streaming needs gigabit-or-better LAN. Also, the
platform uses Fast DDS (RMW), the default middleware of ROS 2 Humble, so keep your default
settings too. Switching the RMW to something else (e.g. Cyclone DDS) can break discovery.

### Build fails: `marc-base:ros2-isaacsim-5.1: pull access denied`

**Symptom:** the platform build fails with `marc-base:ros2-isaacsim-5.1: pull access denied,
repository does not exist`.

**Cause:** the base image the platform image is built on (`marc-base:ros2-isaacsim-5.1`) is not
pulled from a registry — it is a local image you build on your own PC. If you have not built
this base image first, the build tries to pull it and hits the error above.

**Fix:** run the `marc.sh setup` step from [Getting Started step 3](getting-started.md) first to
build the base image (once). This command also shows the NGC login reminder.

```bash
bash simulation-platform/marc.sh setup
```

You can confirm the base image was built with the command below.

```bash
docker image ls marc-base:ros2-isaacsim-5.1
```

On success the image is listed on one line as below.

```text
REPOSITORY   TAG                 IMAGE ID       CREATED         SIZE
marc-base    ros2-isaacsim-5.1   0123456789ab   3 minutes ago   XX.XGB
```

### Build fails with `401 Unauthorized` even though the content image is public

**Symptom:** you opened the content image for public (anonymous) pull, yet the platform build
still fails with an error like the following.

```text
failed to fetch anonymous token: unexpected status from GET request ... 401 Unauthorized
```

**Cause:** the image itself is open to the public, but your PC's `~/.docker/config.json` still
holds an expired `ghcr.io` credential from an earlier login. The build tool (buildx) sends this
dead token first and never falls back to anonymous access, so it gets a 401.

**Fix:** log out of `ghcr.io` so it falls back to anonymous access, then pull the image once on
its own to confirm it opens normally.

```bash
docker logout ghcr.io
docker pull ghcr.io/marc-challenge/marc-platform-content:2026   # standalone check
```

On success it pulls the layers and prints a `Status:` line like the following at the end.

```text
2026: Pulling from marc-challenge/marc-platform-content
...
Status: Downloaded newer image for ghcr.io/marc-challenge/marc-platform-content:2026
```

### Performance is slow or VRAM is short

**Symptom:** the frame rate is low or VRAM is short.

**Fix:** reduce resolution, lower the number of concurrent CCTV streams you subscribe to, and
keep heavy inference on your own (separate) hardware.

### The organizers republished and announced an updated image (re-pulling the latest)

**Symptom:** the organizers republished a fixed image under the same tag and announced it, but
the previously pulled image is still used. Docker does not re-pull the same tag automatically.

**Fix:** what the organizers republish is the platform content image
(`ghcr.io/marc-challenge/marc-platform-content:2026`). Re-pull that image explicitly, then
rebuild the platform.

```bash
# 1) Re-pull the updated content image (the same tag is refreshed to the latest digest)
docker pull ghcr.io/marc-challenge/marc-platform-content:2026

# 2) Rebuild and run the platform image with that content
cd simulation-platform
bash marc.sh platform
```

If the announcement gives a different tag or a separate image name, pull the announced name
instead of the one above.

---

(notices)=
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
