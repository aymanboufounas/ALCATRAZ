# Production plan and verification

**Baseline `f97d1e8` · proposed production targets, not measured runtime results.** The [requirements register](Requirements.csv) supplies stable IDs and dependencies. This plan does not commit a budget, asset purchase or delivery date.

## 1. Delivery order

| Gate | Work and role | Evidence required to leave gate |
| --- | --- | --- |
| G0 / Reproduce and stabilize | Gameplay + QA: visible player, one camera owner, local floor support, movement and safe activity exit in all enabled scenes. | Exact commit and scene, reproduction steps, before/after Unity captures, no blocking Console errors, passing applicable live fixtures. |
| G1 / Finish Chapter 01 | Narrative + gameplay: full state path, text/audio consistency, failure/retry, checkpoint coverage and ten functional menu pages. | Recorded complete first-time path and each failure branch; save/load stage matrix; known blocker list empty. |
| G2 / Polish one complete route | Technical art + animation + audio: cell→yard→service area→coast route with consistent materials, physical feedback and licensed vehicle loops. | Day/interior/water captures, close animation review, audible mix review and target-PC profiler capture. |
| G3 / Build proposed escape chapter | Narrative + gameplay: 02A→02B→02C, gated items/doors, bounded boat corridor and ending. | Full built-player completion and corridor cleanup/failure/save regression results. |
| G4 / Release candidate | QA + release: final asset rights, accessibility scope, hardware profiles, packaging and accurate store material. | Reproducible Windows build, actual size report, clean-machine install/play test and signed-off acceptance matrix. |

Do not schedule more uploaded scenery ahead of G0. Estimate each work item after reproducing it and identifying dependencies; assign people and dates separately. Preserve reproducible source revisions for art, audio and animation. Reassess scope if a dependency is blocked rather than declaring the gate complete.

## 2. Visual production specification

Use a consistent physical scale, meter units and material response. Confirm mesh normals/tangents, texture color space, roughness/smoothness mapping and exposure before raising resolution. Scanned exteriors need readable entrances and clean gameplay collision. Interiors need ambient light and local shadow tuning without losing navigation cues.

Character acceptance includes correct body height, skin bounds, visible orange uniform, fitted helmet/vest, hands aligned to weapon grips and no equipment floating through the torso. Static supplied police must be labelled by capability; add rigging/retargeting as a new task if animated movement is required.

Create licensed animation sets for lateral/backward travel, crouch-walk, jump/landing, swimming and combat when the existing clip/procedural combinations cannot meet review. Retarget to the current skeleton, preserve in-place/controller authority, measure motion, align gait phases and annotate contact times. Review at 30/60/120 FPS and from near camera angles. Rockstar titles are a style reference; their animations are not available project assets.

Asset acceptance requires sensible LODs, collision appropriate to traversal and explicit dependency/license records. Only use 4K maps where camera distance and material detail justify them. The imported prison toilet has 4K maps; that does not establish 4K source quality for every asset. Do not invent detail by upscaling an image or duplicate files to reach a size target.

## 3. Graphics and performance targets

Current source offers Low, Medium, High and Ultra, shared by story/exploration. High/Ultra use native render scale, no global mip reduction, four main-light cascades, 4096 shadow atlas and SMAA High. Ultra uses 180 m shadow distance, forced anisotropy and a higher LOD bias. Rendering resource binding and saved SSAO preparation are part of the source pipeline; successful editor preparation and shader compilation remain unverified.

| Proposed benchmark | Target and interpretation |
| --- | --- |
| Reference lab PC | Provisional Ryzen 7 7800X3D-class CPU, RTX 4080-class GPU, 32 GB RAM and SSD. Record the actual test machine; this is not a minimum system requirement. |
| 1440p High | Target stable 60 FPS, 95th-percentile frame time ≤16.7 ms in an uncapped benchmark capture. |
| 4K High | Target stable 60 FPS on the reference class; revise preset cost after profiling if the target is missed. No measured promise currently exists. |
| 4K Ultra | Measure separately; allow a clearly described quality/performance tradeoff. Do not advertise a guaranteed framerate. |
| RAM/VRAM | Proposed working goals ≤12 GB RAM and ≤10 GB dedicated VRAM on the reference PC, measured across a route rather than inferred from mip-streaming budget. |
| Loading | Proposed scene entry ≤15 seconds on the reference SSD after shaders/import caches are established; also measure cold launch separately. |
| Stability | One 30-minute mixed-route session per mode without a crash, stuck control, invalid checkpoint or sustained memory growth; then a longer final soak. |

Measure CPU main/render threads, GPU passes, p50/p95/p99 frame times, spikes, peak RAM/VRAM and resolution/preset. Frame-time budgets are per-frame critical-path goals, not an instruction to add overlapping CPU/GPU durations. Use a standalone player for release measurements. Log driver, OS, build hash and benchmark route.

Optimize the measured bottleneck: visibility/LOD and draw calls, shadow casters/distance, additional lights, post effects, texture residency or scripts/allocations. Do not switch rendering pipelines or buy new content without evidence that it solves the bottleneck. Dynamic resolution/upscaling is a future option, not a currently verified feature.

## 4. Audio production specification

Existing sources include 68 dialogue WAVs, 44 foundation effects and 25 original chapter/music/ambience WAVs at the audited baseline. Source hooks support spatial playback, surfaces, impacts, occlusion and pause. Counts describe files, not an approved final mix.

Add licensed helicopter rotor/engine and boat engine loops with idle/load/start/stop treatment as needed. Ensure looping, transitions, Doppler and distance attenuation remain believable without masking speech. Speaker/radio props require an explicit playback feature before they can be treated as sound sources.

Review gunshots/reloads by weapon class, punch/knife windup versus contact, water movement, UI confirmations and mission success/failure. Replace mismatched placeholder recordings where needed. Correct the poker welcome text/audio together. Preserve creator, license, source hash, edit chain and output format for every replacement.

Audible acceptance: no missing clip, click or clipping at normal settings; dialogue understandable outdoors/indoors; separate master/music/effects/dialogue controls behave; pause/lost focus and vehicle camera transitions leave one appropriate listener. The current cloud cannot provide that listening test.

## 5. Test layers and evidence policy

The latest recorded offline run in [HourlyChecksAndGraphics.json](../../Validation/HourlyChecksAndGraphics.json) reports 24/24 checks and 220,928 executable C# assertions. These are existing baseline results, not a new execution for the documentation. They cover rule logic, grammar and source/native integrity; they do not compile all Unity APIs, import assets, render a character or prove live collision.

The [source-check workflow](../../.github/workflows/source-checks.yml) is configured at minute 17 of each UTC hour and on pushes/PRs/manual runs. It keeps logs/artifacts for 14 days. Configuration and a passing local run do not prove a scheduled GitHub execution occurred. There is no ongoing AI agent applying hourly fixes.

Unity verification starts with **Alcatraz → Run All Gameplay Checks (Play Mode)** after entering/resuming gameplay on safe ground. Record passed, failed and skipped suites separately; a skipped required fixture leaves that case unverified. Follow with manual walkthroughs and a standalone build. Never mark a rendering bug fixed because a pure-rule test passed.

Each result record needs requirement ID, commit/build hash, scene, platform/hardware, input device, resolution/preset, setup steps, expected/actual result and capture/log path. Each defect needs a reproducible trigger and its next verification step.

## 6. Required test matrix

| Case | Steps | Pass condition |
| --- | --- | --- |
| QA-01 / Visibility | Fresh Play and every scene start; move, orbit, near wall/corner, crouch, jump, aim, V/R3 restore. | Correctly scaled body visible in ordinary space, supported feet, one camera driver; no permanent rendering-off or head view. |
| QA-02 / Movement | Walk/jog/sprint, sprint→walk30s→stop, reverse, wall, stairs, slopes and ceiling at 30/60/120 FPS. | Coherent travel/animation/contact; ordinary stop after long walking; no residual wall push or ceiling penetration. |
| QA-03 / NPC support | Walk all routes and inspect every living standing actor on exterior/interior tiers; interrupt with poker/sparring. | Actor stays on intended local floor; no snaps to roof/table; seated/sleeping/dead actors keep state. |
| QA-04 / Combat | Exploration guns/reload/swap/knife/punch against target, standing and seated NPC, with clear line and blocked wall. | One correctly timed hit, valid ammo/stamina changes, no self-hit or through-wall damage; death stops routine. Story remains mission-controlled. |
| QA-05 / Water | Swim in/out, obstructed pier, low/high bank, boat exit and sampled warning/restriction; repeat in all map contexts. | Surface support and collision, clear low-bank clamber only, appropriate warning then 3 active seconds WANTED→restart; no interior false positive. |
| QA-06 / Health | Start, damage, hard fall, lethal hit, pause/lost focus during failure, restart with/without valid latest save. | HUD starts at 100%, reaches 0% correctly, control blocked, DEAD countdown pauses appropriately, same scene restarts at 100%. |
| QA-07 / Activity ownership | Enter/leave poker, training, boat, helicopter, dialogue; trigger incident/death/title transition from each allowed state. | No stuck external control, orphan seat/camera, duplicate sounds or hidden weapons/body. |
| QA-08 / Save/load | Latest + 3 manual slots, corrupt primary/backup, unsafe destination, scene mismatch and each main story gate. | Restore documented fields only; invalid saves refuse/recover visibly; safe checkpoint survives death/wanted; no reward duplication. |
| QA-09 / Menus | All 10 pause sections and title settings; keyboard/mouse/controller; 720p/1080p/1440p/4K, ultrawide and4:3. | Legible text, reachable actions, visible focus, modal confirmation blocks underlying input; reopening settings does not revert current resolution. |
| QA-10 / Chapter01 | Complete all contacts→knife→gang/tattoo→stash→phone→rival→isolation→visitation→agreement; repeat missed knife/retry. | Every gate and terminal objective correct; no softlock or accidental exploration equipment. |
| QA-11 / Graphics/audio | Compare High/Ultra interior/coast/water/night-style menu; listen through surface/combat/vehicle/activity changes. | No missing/pink materials or shader errors, stable source pipeline on scene transition, clear audio mix and valid settings. |
| QA-12 / Build | Clean machine launch, supported controllers, complete route, profiler run and quit/relaunch. | Reproducible Windows player, readable install requirements, actual size/performance record and no release blockers. |
| QA-13 / Proposed escape | When implemented, complete 02A→02B→02C and test every exit from escape-corridor exemption. | Escape succeeds only with valid mission state; no permanent bypass after abort/death/load/scene change. |

Repeat the relevant matrix in supplied exploration, original exploration and Chapter01. Do not mechanically require exploration-only equipment in story or story progression in exploration. Test 4K on the selected high-end target and verify settings still work at lower resolutions.

## 7. Save, packaging and release

Retain compatibility namespaces and filenames unless an explicit migration is implemented. Existing exploration checkpoints intentionally omit NPC deaths/world physics; tell players this in save UI. A future persistent-world save is a separate versioned feature, not an implied guarantee.

Build Windows x64 through the project's supported Unity menu/script with Windows Build Support installed. A successful build writes its actual report to `Builds/Reports/LatestPlayerBuild.json`. Record both installed bytes and distribution download bytes with their measurement method. Do not pad content toward 10 GB. No finished player or 10 GB build has been produced here.

Before distribution, confirm rights/attributions for every uploaded asset and voice dependency, accurate screenshots from the actual build, final controls and accessible settings, and truthful feature/system-requirement text. Release checklist items need evidence; the GDD itself is not that evidence.

## 8. Principal risks and responses

| Risk | Impact | Response |
| --- | --- | --- |
| Reported invisible prisoner remains unverified | Core game cannot be judged/playable | Make QA-01 a G0 blocker; capture exact scene/import/camera report before adding content. |
| Authored and scanned spaces use different support assumptions | Roof snaps, falling, incorrect water/save position | Keep scene/context-specific probes and test each floor/transition. |
| Mixed asset fidelity and static police | Uneven presentation, unsupported animation expectations | Material/scale audit and explicit rigging work, not blanket high-quality claims. |
| Missing audio and placeholder animation | Weak physical feedback | Complete one route's animation/audio library and compare recorded review captures. |
| Proposed boat escape conflicts with water restriction | Escape always fails or permanent boundary bypass | Mission-scoped corridor with cleanup tests before final mission work. |
| New campaign systems expand scope | Chapter01 remains unfinished | Finish G0/G1 before scheduling continuation; limit first escape to one route. |
| Blocked uploads/license uncertainty | Missing content or nonredistributable release | Keep blocked, reacquire valid files and record actual rights before inclusion. |
| No licensed Unity editor in cloud | Runtime verification/build unavailable | Perform Unity gates on supported licensed editor/target PC; retain source-only evidence boundaries. |

## 9. Change control

A feature becomes SOURCE only after a concrete implementation and supporting evidence path exist. Unity acceptance is a separate recorded outcome. Update affected requirements, controls, narrative/voice and QA cases together. Historical reports keep their original counts/date; new results get their own commit and run identity.
