# Scene sprite extraction review ? 2026-09-28

## Full Disc 1 rerun

Ran `python tools/so2_scene_npc_extract.py --all` and `python tools/so2_scene_sprite_indexer.py`, retaining the mode-dependent 12/16-byte descriptor-header fix. No git commands were run.

| Measure | Saved earlier catalog | Fixed-header run |
| --- | ---: | ---: |
| Archives scanned | 948 | 948 |
| Archives producing sprites | 484 | 626 |
| Extracted frames | 42,694 | 47,228 |
| Archive 3418 frames | 382 | 429 |
| Archive 3418 populated sections | 23 | 25 |

Net increase: 142 archives and 4,534 frames. On the same disc bytes, replaying the old header interpretation versus the fixed interpretation changes 570 sections across 358 archives: those sections yielded 1 accepted frame with the old interpretation and 4,535 with the fix. This is decode acceptance, not a visual review of every recovered frame.

The index declares 48,239 frames across 3,939 sections and 250 selector IDs. Declared descriptors are not the same as written PNGs. Of 827 tag-2 archives, 201 have zero sections; 626 have sprite sections. The scanner also encounters 40 archives without tag 2 and 81 rejected by the existing container-parts bound. Those 81 have not been established to be valid sprite-bearing scene containers.

## Bounds and blank scan

`tools/so2_scene_sprite_audit.py` independently inspects descriptor dimensions, pixel bounds and skips, and scans every `scene_*/*.png` for both fully transparent alpha and all-black RGB. Machine-readable results: `artifacts/so2-sprites/scene_extraction_audit.json`.

All 47,228 expected output filenames are present. Initial scan covered 47,702 PNGs with zero fully transparent and zero all-black images. Of the 474 extra files, 473 belong to earlier audit/reference directories and one was stale current-folder output: `scene_3864/sec10_f00.png`. That old decode was preserved under `artifacts/so2-sprites/previous_decode/scene_3864/sec10_f00.png` and removed from the current scene folder by moving it. The post-move scan covered 47,701 PNGs (47,228 current outputs plus 473 prior audit/reference images), again with zero fully transparent or all-black images and no missing current frames.

Observed dimensions across parsed descriptors reach width 220 and height 180. Width and height are unsigned bytes, so `>256` cannot trigger for this layout. No odd widths, out-of-payload pixel ranges, palette-bound failures or rejected frame counts were observed among the parsed sections. No size cap was raised.

765 zero-dimension descriptors and 246 all-zero indexed-pixel frames are skipped. Their exact locations are recorded in the audit; intentional emptiness versus another format issue has not been proven for each. Nonblank output also does not prove correct colors, animation, or all format interpretations.

## Frame-specific visual evidence

`tools/so2_scene_selector_evidence.json` records 62 personally viewed non-hero selector samples with exact archive, section, frame and filename. These are rendered in section 2.1 of `docs/SO2-SCENE-SPRITE-INDEX.md` and embedded in the master JSON. All 62 references were checked against the index's selector IDs and existing files. Final visual review used `artifacts/so2-sprites/evidence_final_0.png` and `evidence_final_1.png`, generated after the complete extraction.

Examples of recovered content outside 3418:

- Selector 157: red-and-gold chest, `artifacts/so2-sprites/scene_3207/sec15_f00.png`.
- Selector 32766: purple orb on slender gold stand, `artifacts/so2-sprites/scene_3211/sec00_f00.png`.
- Selector 10000: orange/yellow glowing orb, `artifacts/so2-sprites/scene_3212/sec03_f00.png`.

Additional observations include humanoids, winged creatures and large crouching furred creatures. None establishes a switch interaction, a named boss, a particular dungeon role, or an identity across every occurrence of a selector. Specifically, selector 56's cited sample is a small green-hooded humanoid and selector 79's is a black-haired moustached humanoid. These statements concern their cited frames only.

The existing hero mapping is retained as inherited project evidence. Non-hero `classify_selector()` behavior remains Unclassified; visual observations are deliberately a separate, scoped evidence table. All unreviewed instances and named identities remain unresolved. The stale monkey extraction comment was removed from the generator and regenerated Markdown.

## Remaining tasks

- No new named selector identity or selector-to-NPC script mapping was established. The story-script doc mentions behaviors but does not document a concrete named-NPC-to-selector operand; no inference was made from dialogue proximity.
- Tasks 1?2 need controlled human-created before/after save states for one isolated action. No new controlled pair was available, and no new claim about primary-array +0x5A was made.
- Task 3a: combat sub-blob loader/rendering structure not investigated in this pass.
- Task 3b: full visual review of hero-style archives 3111..3206 not performed.
- Task 3c: real creature-shaped field frames were viewed, but switch-creature identity/location remains unresolved.
- Task 4: damage formulas unchanged.

No media or verbatim game dialogue was written outside artifacts/. Review source changes in the extractor docstring, indexer, new audit tool, evidence JSON, and regenerated scene index. Local run logs, baseline catalog, audit JSON and contact sheets are under artifacts/so2-sprites/.
