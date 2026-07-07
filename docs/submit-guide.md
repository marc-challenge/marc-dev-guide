# Submission Guide

This page explains how to submit your completed participant application to the competition.

What you submit is the **entire participant application code — a single repository — that the organizers can run as-is**. You are not submitting a JSON file or a trained model; you submit the whole application that runs with a single `docker compose up`.

---

## What you submit

The organizers clone the repository you pushed as-is, run it with a single `docker compose up`, and the running agent submits its answers over ROS 2 while the competition proceeds.

What is scored is the result your program actually produces. For how to check your own score before submitting, see the [Technical Guide](technical-guide.md) section on running your agent and checking your score. The exact field spec of the answer payloads is in the [API Reference](api-reference.md).

---

## What to do at the deadline

At the code submission deadline you must complete the following three things. These three are the "submission."

1. Make the repository run with a single `docker compose up`. See "Making it run with a single `docker compose up`" below for the requirements.
2. Push to the `master` branch of your team's private GitHub repository and tag the submission commit (`qualifier` for the qualifier; see "Tagging the submission commit" below). `master` is the stable branch that is submitted and scored.
3. In the repository settings, add the `marc-challenge-office` account as a collaborator. Because the repository is private, the organizers cannot clone it without this invitation.

```{admonition} Submit as a private repository
:class: warning
If you push to a public repository, your code and the team's authentication token are exposed as-is. Adding `marc-challenge-office` as a collaborator on a private repository is the only submission path.
```

### Making it run with a single `docker compose up`

The organizers run exactly `docker compose up` on a fresh clone of your repository, with no extra steps — they do not run other scripts first or place files by hand. So before submitting, make sure of the following.

- The repository root has a `docker-compose.yml`, and `docker compose up` alone takes it all the way from image build to agent run.
- Clone the repository fresh into a different location (not your working folder) and confirm that `docker compose up` works from there. If it depends on files that exist only locally or on caches you already downloaded, it will fail in the organizers' environment.

If you start from the starter kit's `demo/docker-compose.yml`, the standard entry point and build context are already set up, so you can build straight on top of it.

```{admonition} No internet at runtime
:class: warning
The judging runtime has no internet. Bake all weights and dependencies into the image at build time; at runtime, no downloads or public API calls are possible. Before submitting, be sure to verify it works with the internet disconnected.
```

### Tagging the submission commit

The organizers clone a **point frozen by a tag** to make the submission commit unambiguous. After your final push to `master`, tag the commit you are submitting and push the tag as well. Use the `qualifier` tag for the qualifier submission.

```bash
# On the commit you are submitting (usually the tip of master):
git tag -a qualifier -m "MARC 2026 qualifier submission"
git push origin qualifier
```

Tags are not sent by a plain `git push`, so push them explicitly with `git push origin <tag>`. The organizers check out this tag and score exactly that snapshot.

---

## Environment variables

Fill in the values needed for team identification and authentication under the compose file's `environment:`. Below is that part of the starter kit's `demo/docker-compose.yml`.

```yaml
# docker-compose.yml (participant app)
services:
  agent:
    environment:
      # For submission, hardcode your credentials by editing the defaults after ':-'
      # (the organizer runs a bare `docker compose up`, with no env exports).
      MARC_TEAM_ID:  "${MARC_TEAM_ID:-u1}"                  # your assigned team ID
      MARC_TOKEN:    "${MARC_TOKEN:-PASTE_YOUR_TOKEN_HERE}" # your assigned token
      ROS_DOMAIN_ID: "${ROS_DOMAIN_ID:-0}"                 # same value as the platform machine
      RMW_IMPLEMENTATION: "rmw_fastrtps_cpp"
```

- Set `MARC_TEAM_ID` and `MARC_TOKEN` by editing the defaults after `:-` to your assigned team identifier and token. The organizers run with no environment variables, so these defaults are your submitted values, and your scoring results are attributed to the team by them.
- Leave `ROS_DOMAIN_ID`, `RMW_IMPLEMENTATION`, and `network_mode: host` at the starter kit compose defaults. They are already set so that the participant application and the platform communicate over DDS on the same LAN and the same ROS domain.
- Keep the token only in the compose file of your private repository. Do not put it in a public repository or a public image.

---

## Final code submission for finalists

The submission described so far is for the **qualifier** scoring. The qualifier results decide which teams advance to the finals, and teams that advance can keep improving their code afterward.

Finalist teams submit their improved final code at the paper camera-ready submission time. So even after the qualifier submission, you have a chance to refine your code up until the finals. The final code submission works the same way as the qualifier procedure above (`master` push + collaborator + a commit tag); only the tag differs — use `finals`.

```bash
# On the final commit you are submitting for the finals:
git tag -a finals -m "MARC 2026 finals (camera-ready) submission"
git push origin finals
```

The finals also run in an internet-blocked environment, so the same precautions as the qualifier apply. In short, your final code completes the same three things as the qualifier.

1. Make the repository run with a single `docker compose up`, working with no internet.
2. Push to the `master` branch of your private repository and tag the submission commit with `finals`.
3. Add `marc-challenge-office` as a collaborator (keep it if already added).

---

## Qualifier evaluation hardware (reference)

Provided for sizing your agent.

| Item | Spec |
|---|---|
| OS | Ubuntu 22.04 |
| CPU | Intel Core i7-12700K |
| GPU | RTX PRO 5000, 48 GB |
| Memory | ~125 GiB |

The participant application runs on separate hardware from the platform (same LAN and ROS domain, over the DDS network), and teams are scored one at a time, in sequence.
