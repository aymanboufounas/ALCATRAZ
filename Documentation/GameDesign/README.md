# ALCATRAZ design documentation

**Design revision 1 · 16 October 2026 · source baseline `f97d1e8`**

Start with the [Game Design Document](GameDesignDocument.md). This package turns the requested prison game into a concrete design, implementation backlog and verification plan. It uses inspected project code and the accessible references in [Research](Research.md).

| Document | Purpose |
| --- | --- |
| [Game Design Document](GameDesignDocument.md) | Pitch, audience, pillars, core loop, product scope and release decisions. |
| [Systems](Systems.md) | Movement, visible player, combat, water, health, NPCs, activities, controls, UI and save contracts. |
| [World and Missions](WorldAndMissions.md) | Cast, scene structure, current Chapter 01 and proposed escape chapter. |
| [Production and QA](ProductionAndQA.md) | Art/audio production, high-end graphics targets, milestones, risks and acceptance tests. |
| [Requirements](Requirements.md) / [CSV](Requirements.csv) | Prioritized, traceable work items with status, dependencies, evidence and acceptance criteria. |
| [Research](Research.md) | Read references, their uses, and blocked sources. |
| [Research manifest](ResearchManifest.json) | Reference revisions and content hashes. |

## Reading status correctly

**SOURCE** means an implementation exists in the inspected code; it does not mean Unity gameplay passed. **PROPOSED** means a design or production requirement still to implement. **BLOCKED** means a known prerequisite is unavailable. These statuses appear in the requirements register.

The latest recorded source run passed 24 checks, including 220,928 executable C# assertions; see [the recorded report](../../Validation/HourlyChecksAndGraphics.json). This documentation task does not repeat or replace that run. Unity compilation, imported assets, rendered player visibility, live physics/audio, full playthroughs, performance and a player build remain unverified.

The supplied VSQUAD article could not be read because the environment proxy denied access. The design therefore does not claim to reproduce its contents. Four accessible GitHub reference repositories were read instead. No game code, scene or runtime asset is changed by this documentation package.

## Keeping this useful

Update the requirements row and its evidence whenever implementation changes. Record a Unity result against a commit, scene, hardware and reproduction steps before calling a feature verified. New content must pass the core movement/camera/save checks before it expands the campaign. Earlier revision notes remain historical snapshots; this package states its own inspected baseline.
