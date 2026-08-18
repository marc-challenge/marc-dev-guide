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

### No window appears, or no camera images, on WSL2

**Symptom:** the 3D viewport window never appears even though you run with `HEADLESS=false`.
When running headless, the CCTV camera topics (`/marc/env/cctv/...`) are missing from
`ros2 topic list`. Non-camera topics such as IMU and odometry, however, show up normally.

**Cause:** WSL2 (Linux running inside Windows) is not a supported environment. The platform
runs on Isaac Sim, which is built around the RTX renderer, and both the viewport image and the
CCTV / robot camera images are products of that renderer. WSL2 is not in the list of operating
systems Isaac Sim supports, and this render path is not guaranteed to work where the GPU is
passed through a virtualization layer. In practice, WSL2 has been observed to show no viewport
window and to publish no camera topics. When no images are produced, no camera topics are
published either. Sensor values that do not go through the renderer are unaffected, so this
contrast means the problem is the renderer, not DDS communication.

**How to check:** if the driver version reported by `nvidia-smi` inside Ubuntu matches a
Windows driver number (for example 581.xx), you are on WSL2 — Linux drivers are numbered like
`580.159.03`. The commands below also identify WSL2; either one is conclusive.

```bash
uname -r        # ends with -microsoft-standard-WSL2 on WSL2
ls /dev/dxg     # this device node exists only on WSL2
```

**Fix:** install and run on native Ubuntu 22.04 (dual boot, or a separate Linux machine).
Neither WSL2 nor virtual machines are supported. Note that the platform and your participant
application may run on different machines, so a single Linux machine for the platform is
enough.

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

### Constant `TF_OLD_DATA` warnings when viewing lidar/TF in RViz2

**Symptom:** The point cloud shows up in RViz2, but `TF_OLD_DATA ignoring data from the
past ...` warnings stream continuously and drown out the log.

**Cause:** The platform stamps messages with simulation time (sim time), while RViz2
defaults to wall clock. When the two time sources disagree, this warning appears. It is not
a malfunction -- the display itself is correct.

**Fix:** Run RViz2 with sim time.

```bash
rviz2 --ros-args -p use_sim_time:=true
```

- Set Fixed Frame to `world`.
- Set the PointCloud2 display's Reliability Policy to `Best Effort` for stable reception
  (Reliable also works but may miss frames depending on discovery timing).

### Standard tf2 tools receive nothing on `/tf_static` (incompatible QoS) — fixed (2026.R01)

This was fixed in the 2026.R01 release. The platform now publishes `/tf_static` as
`TRANSIENT_LOCAL` (latched), so standard tf2 listeners and RViz2 receive it normally. CCTV
camera extrinsics can be looked up by their camera id frame (e.g. `rig_1_a`) relative to `world`.

```bash
ros2 run tf2_ros tf2_echo world rig_1_a
```

If you are on an older version, update to the latest content image (see "The organizers
republished and announced an updated image" above).

### `no SESSION_ACK within 30s` in the manipulation practice environment

**Symptom:** you start the practice environment (`manip-trainer`) and run your client, but
registration never completes and the following is logged. The control panel also stays at
`no client - Register / connect first`.

```text
[REGISTER] starting handshake to /marc/ops/register
[REGISTER] no SESSION_ACK within 30s - check token/runtime
```

**Cause:** this is not an error but the normal behaviour of the practice environment. It
provides only robot I/O and does not carry the competition layer that registers teams and
issues sessions, so nothing is there to answer the registration request. Your assigned token
is not needed either. The `/marc/ops/register` topic appears in the topic list because your
own client created it.

**Fix:** do not wait for a registration result — go straight to controlling the robot. Pass a
short timeout and do not check the return value. By the time `connect()` returns, the ROS 2
node and its communication channels already exist, so arm control and state queries work
normally.

```python
client = MARCClient.from_env()   # MARC_TOKEN may be any non-empty value here
client.connect(timeout=3.0)      # the trainer has no registration - ignore the result
client.send_arm_command(...)     # commands take effect right away
```

If you started from the baseline code (`participant_app.py`), note that it targets the
competition runtime and stops when `connect()` fails. Remove that stop when you use it against
the practice environment.

The panel changes to `team <id> connected` once your client starts sending arm joint commands.
The `no client - Register / connect first` message shown until then does not mean registration
is required; the wording itself will be corrected in the next release. The `MARC_TEAM_ID` of
your client and of the practice environment must match.

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

## Change history

Key changes to the distributed images and kit, by version. To pick up a new revision, `git pull`
the starter kit and rebuild the platform (`bash marc.sh platform`), which pulls the referenced
content image.

### 2026.R03

- Fixed the ground-truth (bounding box) coordinates produced by the dataset generator.
  **Please regenerate your training data after updating.** Objects that are dropped onto the
  ground (cans, tissues) and objects placed tipped over (bicycles, kick scooters, trash cans)
  had coordinates recorded above their actual position. Content that stays where it is first
  placed - people, benches, vehicles - was not affected.
- The annotation format and the submission format are unchanged, so nothing in your code needs
  to change. This affects training data only and has no effect on competition scoring.
- To make regenerating the data less tedious, you can now create many scenes in one run. Set
  `TRAINER_AUTO_SCENES` to the number of scenes you want and they are generated without the GUI.
  See "Generating many scenes at once" in the technical guide.
- Each scene is now saved with an inspection image (`<camera>_overlay.png`) that has the
  ground-truth boxes drawn on it, so a single glance confirms the labels sit on the objects.
- We also fixed a difference in rendered brightness between running with the GUI and running
  without it (`HEADLESS`). Both now produce the same images, matching the competition scoring
  environment, so either way of generating data is fine.
- We confirmed this thanks to a team that verified their generated dataset and sent us example
  images. Thank you.

### 2026.R02

- The training data (Dataset Generator GT files) format is unchanged — data and models you have
  already produced remain valid, and no retraining is required.
- Stage 1 scoring now resolves the reference landmark's expected coordinate within the camera the
  problem specifies. Previously, when landmarks with the same name were placed under several
  cameras, the expected coordinate could come from a same-named landmark under a different camera —
  for example, a problem about the parking-lot camera could be scored against a trash can of the
  same name in the park.
- Because of this correction, the `anchor_coord` result changes for some problems. Treat scores
  from earlier practice runs as indicative only, and re-run after updating. The submission format
  and the scored items are unchanged, so there is nothing to change in your code.
- The demo's reference answer data (`demo/mock_demo_data.yaml`) was regenerated as well. If you use
  the demo as a reference implementation, `git pull` on the starter kit picks it up.
- We identified this from a detailed report by a participating team. Thank you for reporting it.

### 2026.R01

- The training data (Dataset Generator GT files) format is unchanged — data and models you have
  already produced remain valid, and no retraining is required.
- CCTV camera extrinsics are now published on `/tf_static` with the camera id as the frame name.
  You can look up the transform between `world` and a camera id with standard tf2, and it is
  published latched (`TRANSIENT_LOCAL`) so RViz2 and tf2 listeners receive it.
- Added a per-camera ground-height topic `/marc/env/cctv/{id}/ground_height` (`std_msgs/Float32`,
  latched). Use it when back-projecting pixels to world coordinates.
- Expanded the coordinate-convention notes (CCTV frame = ROS optical, GT file euler = USD prim;
  see api-reference and technical-guide).
