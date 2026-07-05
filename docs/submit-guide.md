# Submission Guide

This page covers the **submission JSON format**, the **scoring methodology** (method only —
no numbers), **local scoring**, and the **submission procedure**.

> Provisional notice: tags, dates, and the evaluation hardware spec below are **under
> internal review** and may change.

---

## Submission format

You do not upload a JSON file. Your agent **submits results over ROS 2** during the run; the
"submission" is your Dockerized agent (see [procedure](#submission-procedure)). The result
payloads your agent emits are:

### Stage 1 — grounding (msg 301)

One submission per round, single-target model.

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

- Lost-and-found problems supply `relation` (spatial relation).
- SAR person problems set `target_type: "person"` and supply `situation`
  (`accident` / `emergency` / `abnormal` / `normal`).

### Stage 2 — interpretation (msg 311) + completion (msg 302)

Stage 2 has two parts: submit one grounding (same payload shape as msg 301) for the
`task_description`, then navigate and pick-and-place, delivering the item to the
**designated location**, and finally emit `task_complete` (msg 302, irreversible).

The SDK wraps all of this — see [Technical Guide → MARC Client SDK](submission-api).

---

## Scoring methodology

Scoring is reported as **methodology only**. Exact thresholds, weights, and tuning constants
are **not published**.

- **Camera selection** — did you pick the correct camera for the target?
- **Object / situation interpretation** — `target_type`, and for people the `situation`
  (hazard/abnormality recognition) category.
- **Landmark + relation** — correct reference landmark and spatial relation (lost-and-found).
- **Anchor / target localization** — accuracy of the estimated 3D coordinates, scored as a
  distance-based partial credit (closer is better; the exact distance constants are not
  disclosed).
- **Stage 2 collection** — success of delivering the item to the designated location within
  the time limit.

A per-round result (msg 401) returns sub-scores and a `total`; the final result combines
Stage 1 (round average) and Stage 2 with stage weights. The **values** of any distance
thresholds, acquisition radii, seeds, or weights are intentionally omitted.

```{admonition} What is never published
:class: warning
Ground-truth coordinates, the `hash_seed`, scoring constants (e.g. distance/acquisition
thresholds), the operations backend, and any runtime ground truth are **out of scope** for
this guide. Only the methodology is described.
```

---

## Local scoring

Run the practice runtime (`marc.sh platform`) together with your agent (`demo/`) — the
runtime auto-scores each round and streams a per-round result on `msg 401` (see
`Scoring methodology` above). Your agent receives these scores directly (`[Score] round
N: total=XX`), and the final Stage 1 average + Stage 2 total is published on stage
completion. Local scores are indicative only — the official run uses an unreleased
competition scenario and background.

---

(submission-procedure)=
## Submission procedure

Participant applications are **developed and submitted as Docker** (required). The standard
entry point is `docker compose up`.

1. **Develop in Docker.** Build and run your agent with `docker compose up`; put your
   `MARC_TEAM_ID` / `MARC_TOKEN` in `docker-compose.yml`.
2. **Verify the standard entry point.** The organizers score you by running the *same*
   `docker compose up` — make sure it builds and runs cleanly from a fresh clone.
3. **Add the office account as a collaborator.** Push your agent to a **Private** repository
   and add **`marc-challenge-office`** as a collaborator. Keep the token in the Private repo's
   compose file only (never a public repo).
4. **Freeze and tag.** The organizers clone your frozen tag and score teams **sequentially**.

```{admonition} Offline at runtime
:class: warning
The evaluation runtime has **no internet access**. Bake all weights and dependencies into
your image at build time; do not download anything or call public APIs at runtime.
```

---

## Qualifier evaluation hardware (reference)

Provided for sizing your agent; provisional.

| Item | Spec |
|---|---|
| OS | Ubuntu 22.04 |
| CPU | Intel Core **i7-12700K** |
| GPU | **RTX PRO 5000, 48 GB** |
| Memory | ~125 GiB |

The participant application runs on **separate hardware** from the platform (same LAN /
ROS domain, DDS over the network), and teams are scored sequentially.
