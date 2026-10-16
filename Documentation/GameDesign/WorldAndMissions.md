# World, cast and mission design

**Baseline:** `f97d1e8`. Current behavior is SOURCE; the escape chapter below is PROPOSED. No mission walkthrough has been executed in Unity during this documentation task.

## 1. Setting and geography

ALCATRAZ is a fictional active contemporary prison. Use the real island's recognizable silhouette and landmarks as inspiration, while keeping gameplay adaptations clear. Do not claim historical accuracy for modern gangs, vehicles, interiors or the narrative.

| Space | Current purpose and boundaries |
| --- | --- |
| Supplied scanned exterior | Default exploration; coastal routes, prison entrance, helipad, coastal house/dock, boat and supplied police/dog. |
| Connected cellhouse | Authored interior entered from the supplied island; cells, galleries, stairs, dining and service access. |
| Connected annex | Separate authored activity/asset area reached through a service transition; factory, warehouse, workshop, poker, bag, carport and detailed solitary props. Its offset space is not geographically adjacent scanned terrain. |
| Original authored island | Alternative exploration world with adapted Alcatraz landmarks, multiple elevations and a separate map/collision layout. |
| Chapter 01 | Separate story scene using the authored prison and mission state machine. Its isolation cell is distinct from the annex solitary display area. |

[AlcatrazLayout.json](../AlcatrazLayout.json) records 17 authored landmark records, 19 road/path records and 512 cell records. These are authoring counts, not a verified promise that every room is enterable. [AlcatrazActors.json](../AlcatrazActors.json) records 30 authored actor bindings; actor populations differ by mode and supplied additions.

A useful route must have supported walking space, clear collision, a readable destination and a safe return. Put set dressing outside movement/interaction clearances. Route overlays should distinguish stairs, door transitions and water; a roof must not count as the street beneath it.

## 2. Cast and relationships

| Character | Role and relationship | Presentation need |
| --- | --- | --- |
| Elias Vale | Playable inmate B-04, framed by Cinder Syndicate; Theo's brother. | Orange uniform, visible body, readable gait and action silhouettes. |
| Theo Vale | Brother who brings news of their father's kidnapping. | Visitation blocking, emotional line timing and subtitle readability. |
| Niko Serrin | Blue Meridian member; knife incident and phone contact. | Knife handoff/concealment staging must be legible. |
| Malik Reed | Blue Meridian leader; gang entry and escape agreement. | Clear dialogue focus and progression feedback. |
| Rafi | Tattooist. | Seated interaction/pose with acquired tattoo state. |
| Tomas | Social introduction and exploration boxing contact. | Distinguish conversation, training and ambient states. |
| Samir | Cook/social contact and poker opponent. | Correct interaction priority near poker/dining. |
| Jonah | Workshop contact and prison routine introduction. | Objective marker and clear access route. |
| Officer Harrow | Story guard and arrest/isolation consequences. | Uniform/equipment consistency; no implied general pursuit AI. |
| Iron Rooks rival | Scripted story fight opponent. | Readable attack cadence, damage and arrest trigger. |
| Luis and other inmates | Poker/ambient population. | Correct seated/standing support and nonduplicated identities. |

The father and Cinder Syndicate motivate the story. They do not establish playable mainland missions. Current static supplied police and display figures are asset roles separate from the rigged story cast.

## 3. Current Chapter 01 critical path

The authoritative state machine has 19 stages in [PrisonStoryState.cs](../../Assets/Game/Scripts/Missions/PrisonStoryState.cs), executed by [PrisonStoryDirector.cs](../../Assets/Game/Scripts/Missions/PrisonStoryDirector.cs). The table groups them by displayed mission, rather than inventing additional completed chapters.

| Mission | Trigger and goal | Completion/reward | Failure and checkpoint expectation |
| --- | --- | --- | --- |
| FIRST RESPECT / introduction | Leave B-04 and meet Tomas, Samir and Jonah. | Three acquaintances allow the next social gate. | Contacts must not be awarded twice; save/load preserves flags. |
| FIRST RESPECT / yard incident | After contacts, at least 240 active social seconds and presence within 19 m of yard spawn, observe the incident. | A 22-second opportunity to conceal Niko's fallen knife. Concealment sets respect to 15. | Missing it shows missed/retry feedback; retry resets opportunity without awarding knife or respect. |
| FIRST RESPECT / initiation | Thank Niko, meet Malik, join Blue Meridian and receive Rafi's tattoo. | Respect milestones 30 and 50; gang/tattoo flags. | Dialogue and activity interruption must restore control. |
| FIRST RESPECT / stash | Put the quest knife under the B-04 mattress. | Knife location becomes cell stash; next task unlocks. | Carrying/concealment and stored states must never both be shown. |
| TRUST LINE | Receive Niko's phone and answer Malik's call. | Phone flag and respect 65. Knife remains stored. | A held phone must not enable unrelated equipment or duplicate progression. |
| YARD TROUBLE / rival | Approach the rival and land three valid nearby visible punches. | Scripted arrest transition. | Rival strikes can damage player; death follows health restart rules. Ordinary exploration firearms are unavailable. |
| YARD TROUBLE / isolation | Survive isolation, represented by sleeping through 24 fictional hours in 60 active seconds. | Day becomes 2 and visitation is enabled. | Pausing stops the countdown; save flags cannot skip required release steps. |
| YARD TROUBLE / revelation | Meet Theo, learn about father, reflect in cell and agree with Malik to escape. | Respect 80; escape agreement; ChapterComplete. | Terminal objective states that the continuation is in a later chapter. |

Respect is milestone state, not a general kill/loot score. The saved `escapeDaysRemaining = 6` is narrative metadata; a six-day simulation clock is not implemented by this chapter.

## 4. Dialogue, cinematics and localization

Keep each dialogue entry tied to its actor, subtitle, audio clip and state gate. [Chapter01_Dialogue.md](../Chapter01_Dialogue.md) and [story-dialogue.json](../../Assets/Game/Resources/Blackstone/story-dialogue.json) need a consistency pass against the current mode and activities.

A known mismatch remains: the welcome dialogue/audio says Five-card draw while [PrisonPokerTable.cs](../../Assets/Game/Scripts/Activities/PrisonPokerTable.cs) implements Texas Hold’em. Rewrite the line and regenerate its audio together; do not silently call the existing recording corrected.

Cutscenes must release camera ownership on completion, skip/cancel where supported, restart, scene load and return to title. A close dialogue shot can temporarily differ from normal third-person framing; it must not leave the free-play camera inside the character. Arabic design notes are story reference material, not a complete localized UI or recorded Arabic voice set.

## 5. Proposed Chapter 02: The Silent Blueprint

**This continuation is designed, not implemented.** Its purpose is to complete one escape route using the existing prison, service areas and boat. It requires explicit new mission stages, interactions, checkpoints, dialogue and authored escape access. Exploration equipment availability must not bypass story gates.

| Proposed mission | Player actions | Required implementation | Success and retry |
| --- | --- | --- | --- |
| 02A / The Blueprint | Speak with Malik and Jonah, inspect a service plan, choose the boat route and identify the service exit. | Plan quest item, inspected-location flags, new dialogue, journal entry and map markers. Existing radio/workshop props are only visual candidates. | Unlock service preparation after all required information; save at a safe cell point. Missed conversation remains replayable. |
| 02B / Quiet Passage | Acquire an authorized story key/tool, open a specific service passage, reach a marked coastal access point. | New item acquisition and door gates, authored supported route, encounter scripting and clear failure warning. Do not assume existing arbitrary doors already form this route. | Reach staging point with Elias and required story state; on death restore that mission checkpoint without duplicating rewards. |
| 02C / Across the Bay | Board the assigned boat, leave along a marked corridor and reach an authored extraction trigger. | Mission-specific boat ownership, extraction corridor, failure/restart state, ending scene and save migration. | Show an explicit escape completion and lead about father; preserve a completed campaign checkpoint. |

Proposed water-zone change is essential: the current global restriction would fail an offshore escape. Only while 02C is active may an authored corridor lead to extraction; outside that corridor retain WANTED/restart. Aborting, dying, loading, leaving the boat or returning to another mode must clear the exemption. This requires regression tests and visual boundary cues before implementation is considered complete.

Police reactions in this route can be authored encounter beats. A general police search/pursuit simulation is outside this initial continuation. The helicopter remains a sandbox activity; an alternative helicopter ending needs its own navigation, AI, collision, failure and cinematic work before it becomes a committed route.

Proposed pacing is a short, replayable route with safe checkpoints between preparation, passage and extraction. Determine duration from first-time playtests; do not promise a campaign length before measuring it.

## 6. Placement and asset register

The current primary catalog has nine supplied entries; the extras catalog has 29. They cover scenery, weapons, activity props, factory/workshop structures, bridge/stairs, watchtower, vegetation/beach sets, carport and detailed solitary door/toilet. See [primary catalog](../../Assets/Game/Supplied/Resources/AlcatrazSupplied/Catalog.json) and [extras catalog](../../Assets/Game/Supplied/Resources/AlcatrazExtras/Catalog.json).

For every release asset, record creator, source, redistribution/modification license evidence, source checksum, import changes, runtime prefab/materials, LOD/collision policy and placement. Upload provenance alone does not grant a new license. Imported low-poly, scanned and stylized assets need consistent materials and purposeful placement; proximity in an asset annex is not finished world integration.

Chevrolet Kodiak C70, abandoned garage and rusty-roof house remain BLOCKED: the supplied archives exceeded the available 32 MiB transfer limit and were not imported. Reacquire usable source files before scheduling their integration. Do not show these as completed content in screenshots or store descriptions.

Explosive barrels currently provide solid scenery, speakers/radios are static props, Adrian Shephard is a static supplied figure, and the police source is a static model. Explosion damage, radio playback, a newly rigged figure and fully animated police require separate production tasks.

## 7. World and narrative acceptance

A full Chapter 01 recording must cover all contacts, missed knife/retry, stash, phone, brawl, isolation, visitation and agreement. Checkpoint reloads at each major milestone must reach the next gate without replaying rewards or skipping required flags.

In supplied exploration, run the connected cellhouse, annex, solitary-prop, factory/carport and dock routes; verify correct floor, collision, map context and safe return. In original exploration, test only the authored routes and activities actually present in that scene. Keep the story isolation cell and annex solitary location identifiable. Every standing living actor must occupy its intended floor; seated/sleeping/dead actors must retain their state.

The proposed escape chapter is accepted only when the complete critical path, corridor exception cleanup, ending, checkpoint restore and failure paths run in a built player. A design table and source flags alone cannot establish a complete playable campaign.
