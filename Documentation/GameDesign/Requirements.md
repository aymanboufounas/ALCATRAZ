# Prioritized requirements

Design revision 1, source baseline `f97d1e8`. This table is generated from [Requirements.csv](Requirements.csv). **SOURCE** records a code path, not a passed Unity test. Proposed and blocked rows remain unfinished. P0 blocks a reliable playable release; P1 is the polish/usability pass; P2 follows the core gates. Dependency IDs determine delivery order, not historical implementation order. Owners are roles until people are assigned.

| ID | Priority | Status | Requirement | Depends on |
| --- | --- | --- | --- | --- |
| VIS-001 | P0 | SOURCE | Visible, correctly scaled prisoner in all three enabled scenes | — |
| MOV-001 | P0 | SOURCE | Grounded walking, jogging, sprinting, reversal, stairs and slopes | VIS-001 |
| MOV-002 | P0 | SOURCE | Jump, crouch, ceiling clearance and low-bank exit control | MOV-001 |
| ANM-001 | P1 | SOURCE | Recent sprint memory, transitions and foot contact | MOV-001 |
| ANM-002 | P1 | PROPOSED | Licensed extended movement, swimming and combat animation set | ANM-001 |
| NPC-001 | P0 | SOURCE | Living standing actors supported on the intended local floor | MOV-001 |
| CAM-001 | P0 | SOURCE | One camera owner through activities, cinematics and vehicles | VIS-001 |
| CBT-001 | P1 | SOURCE | Exploration firearm hits and ammunition/reload ownership | CAM-001 |
| CBT-002 | P1 | SOURCE | Exploration knife/punch contact and NPC damage | CBT-001 |
| WTR-001 | P0 | SOURCE | Surface swimming, dry-shore clamber and safe boat exit | MOV-002 |
| WTR-002 | P0 | SOURCE | Sampled offshore warning, then WANTED and restart | WTR-001 |
| HLT-001 | P0 | SOURCE | 100% health, damage, DEAD and full-health restart | WTR-002 |
| ACT-001 | P1 | SOURCE | Poker, training and vehicle control-state restoration | CAM-001 |
| VEH-001 | P1 | SOURCE | Flyable helicopter and buoyant patrol boat | ACT-001 |
| NPC-002 | P1 | PROPOSED | Animated police rig and matching equipment fit | NPC-001 |
| AI-001 | P2 | PROPOSED | Authored reactions for proposed escape encounters | MIS-002 |
| MIS-001 | P0 | SOURCE | Complete Chapter 01 arrival-to-agreement path | HLT-001, SAV-001 |
| MIS-002 | P2 | PROPOSED | Chapter 02 blueprint and service-passage missions | MIS-001, NPC-001 |
| MIS-003 | P2 | PROPOSED | Boat escape corridor and complete ending | MIS-002, WTR-002, VEH-001 |
| TXT-001 | P1 | PROPOSED | Correct Five-card draw text/audio to Texas Hold’em | ACT-001 |
| UI-001 | P0 | SOURCE | Ten functional pause pages and truthful live values | CAM-001 |
| UI-002 | P1 | PROPOSED | Readable adaptive text and focus at 4K and narrow aspect ratios | UI-001 |
| SAV-001 | P0 | SOURCE | Latest checkpoint plus three manual slots with validated restore | HLT-001 |
| GFX-001 | P1 | SOURCE | Shared High/Ultra and native 1440p/4K settings | UI-001 |
| GFX-002 | P1 | SOURCE | Post-processing/shadow resources and environment-reflective water | GFX-001 |
| GFX-003 | P1 | PROPOSED | Profile and optimize a high-end 1440p/4K route | GFX-002, VIS-001 |
| ART-001 | P1 | PROPOSED | Cohesive scale, material and LOD pass on one complete route | VIS-001, NPC-001 |
| AUD-001 | P1 | SOURCE | Spatial footstep, combat, dialogue and UI audio hooks | CBT-002 |
| AUD-002 | P1 | PROPOSED | Licensed helicopter/boat loops and transitions | VEH-001, AUD-001 |
| AST-001 | P1 | SOURCE | Nine primary and 29 extra catalog entries | ART-001 |
| AST-002 | P2 | BLOCKED | Kodiak C70, abandoned garage and rusty-roof house imports | — |
| LIC-001 | P0 | PROPOSED | Release asset-rights and attribution register | AST-001 |
| ACC-001 | P1 | PROPOSED | Accessibility: remapping, text size, toggles and reduced shake | UI-002 |
| LOC-001 | P2 | PROPOSED | Localization beyond current English | TXT-001, UI-002 |
| QA-001 | P0 | SOURCE | Hourly source-check reporting | — |
| BLD-001 | P0 | PROPOSED | Reproducible tested Windows player and actual size report | MIS-001, VIS-001, GFX-003, LIC-001 |

The CSV contains source evidence, owner roles and concrete acceptance criteria for every row. [Production and QA](ProductionAndQA.md) defines the referenced QA cases. Passing source checks does not complete the required Unity walkthroughs.
