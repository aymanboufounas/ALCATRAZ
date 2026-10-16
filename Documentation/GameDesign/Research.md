# Game design research and sources

Research date: **16 October 2026**. This research supports the original ALCATRAZ design package in this directory. It supplies a document structure; the project's source code, asset catalogs and verified results supply its current implementation facts.

The requested [VSQUAD article](https://vsquad.art/blog/articles/how-to-create-a-game-design-document-from-scratch/) could not be read: the environment's network proxy rejected the connection with `CONNECT 403`. Its title and URL identify the user's reference, but no advice or article contents are attributed to it here. Public GitHub search succeeded, and four alternative repositories were reviewed at fixed commits. The machine-readable [research manifest](ResearchManifest.json) records the precise files, hashes and read scope.

## Reviewed alternatives

| Source | Material actually read | Useful structural ideas | Limits of this review |
| --- | --- | --- | --- |
| [LazyHatGuy / GDDMarkdownTemplate](https://github.com/LazyHatGuy/GDDMarkdownTemplate/tree/c06d8bd1fc951e6b82132b7147964f3bdf5f07e0) | Entire pinned `README.md`, 174 lines. | A broad checklist covering game overview, mechanics, screen flow, story, levels, interface, AI, technical requirements, art, management and asset lists. | The README is an outline with wiki links. Those linked wiki pages and the earlier template it credits were not read. |
| [kosinaz / game-design-document-template-for-beginners](https://github.com/kosinaz/game-design-document-template-for-beginners/tree/2568e7bdb4c0f208ba011039263240ab8fbfd43c) | Entire pinned `docs/Game Design Document.md`, 61 lines. | A short introduction, player-facing description and focused feature list, useful for a readable pitch before detailed specifications. | The reviewed file is a short introductory template, not a complete technical specification. Its commercial examples and claims about successful game names were not adopted as evidence. |
| [mikewesthad / Game-Design-Document-Resources](https://github.com/mikewesthad/Game-Design-Document-Resources/tree/14039415a6de8beba15a8e29de9bb1a645dd3d63) | Entire pinned `README.md`, 28 lines. | A resource index distinguishing templates from examples, with both a one-page template and larger design references. This informs the package's overview-plus-detail organization. | The linked Google Docs, videos and historical game documents were not opened. Their content, authenticity and applicability were not assessed. |
| [saeidzebardast / game-design-document](https://github.com/saeidzebardast/game-design-document/tree/2fc1c4caedafe96881d754fe0ead12b16831374e) | Entire pinned `game-design-document-outline.md`, 145 lines. | Progression, explicit mechanics, screen relationships, area connections, character roles, mission paths, controls, audio, AI and target hardware. | The linked university source document was not opened. This is an outline, not proof that a particular implementation works. |

The pinned files contain **32,940 bytes in total**. SHA-256 identifies exactly the reviewed snapshots; it does not establish endorsement, licensing for unrelated game assets, or correctness of advice linked by the authors. Downloaded template copies remain research scratch files and are not redistributed in this package.

## How the structure is applied

The documents use original ALCATRAZ wording. They paraphrase structural ideas from the reviewed outlines and add project-specific specifications rather than copying template prose, example pitches or historical game documents.

| Design question | Application in this package | Research basis |
| --- | --- | --- |
| What is the game, who is it for, and what does the player do? | [GameDesignDocument.md](GameDesignDocument.md): pitch, target player, pillars, scope and core loop. The loop connects the player's repeated actions to progression rather than becoming a feature shopping list. | Beginner template's introduction/description/features; Markdown template's game overview and play flow. The explicit core loop is our synthesis. |
| What rules determine success, failure and feedback? | [Systems.md](Systems.md): movement and third-person camera, interactions, combat, NPC behavior, swimming, wanted/death restarts, activities, saves and settings. Values and current limitations come from repository evidence. | Markdown and outline templates' mechanics, controls, AI, options and replay/save sections. |
| How does the player move through screens? | [Systems.md](Systems.md): title, gameplay, activities, pause pages, confirmations and recovery. A decorative menu image is distinguished from functional navigation and live game data. | Both broad outlines explicitly include screen flow and interface. |
| How do the world and missions fit together? | [WorldAndMissions.md](WorldAndMissions.md): named cast, connected spaces, mission gates, objectives, pacing, failure/retry and the current chapter endpoint. Proposed future chapters remain labelled as proposals. | Story, world, character, level and critical-path sections in the Markdown and outline sources. |
| What must the art, animation and audio communicate? | [GameDesignDocument.md](GameDesignDocument.md), [Systems.md](Systems.md) and [ProductionAndQA.md](ProductionAndQA.md): visual direction, animation quality, audio coverage, asset provenance and measurable review gates. | The broad outlines' art, look/feel, camera, lighting, animation, sound and music sections. |
| What can actually be built and supported? | [ProductionAndQA.md](ProductionAndQA.md): Unity/toolchain, high-end PC target at 1440p/4K, deliverables, production dependencies, risks and outstanding decisions. Installed size is measured from a real build; a requested 10 GB size is not treated as evidence of quality. | Technical and target-hardware sections in both broad outlines; management and risk sections in the Markdown source. Hardware preference and build limitations come from this project. |
| How will completion be demonstrated? | [Requirements.csv](Requirements.csv) and [ProductionAndQA.md](ProductionAndQA.md): traceable requirements, acceptance criteria, evidence, offline checks and Unity play/build/performance tasks. | The Markdown template includes test planning. Traceable evidence states and project-specific acceptance gates are additions for ALCATRAZ. |

## Evidence rules for this design package

1. **User requests define intent.** The reference article and supplied visuals help identify the requested kind of documentation. They do not prove that a gameplay feature is present or tested.
2. **Current source defines the present implementation.** Runtime scripts, enabled scenes, catalogs and configuration take precedence over older revision notes. Contradictions are recorded for correction; a historical report is not silently treated as a current test.
3. **A proposal remains a proposal.** A complete escape campaign, new animation capture, missing vehicle audio and other future work must have an implementation task and an acceptance gate before being described as delivered.
4. **Verification names its boundary.** Source inspection, pure C# tests, static asset checks, Unity import, Play Mode, a packaged build and GPU performance measurements are different evidence types. No source template or offline preview substitutes for the missing Unity checks.
5. **References are not asset permission.** The templates' links to commercial games do not authorize copying those games' animation, character models, audio, interface art or narrative. Existing project assets retain their own provenance and license records.

## Unread references and follow-up research

The VSQUAD article and attempted Unity/Steam documentation pages were inaccessible through this environment's proxy. They are explicitly `NOT_READ` in the manifest. No Unity API or Steam release requirement is attributed to their unread contents. Before release, review current official documentation using an available connection and record the exact version/page and access date.

The search entry point was [GitHub repository search for game design document templates](https://github.com/search?q=game+design+document+template&type=repositories). It was used for discovery, not as proof of template quality. A useful next editorial step is to review this package against the user's priorities, then keep requirement statuses synchronized with actual implementation and test evidence.
