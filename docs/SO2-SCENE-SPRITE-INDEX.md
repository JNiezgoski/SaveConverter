# Star Ocean: The Second Story (PS1) - 2D Scene & Field Sprite Master Index

**Scene Sprite Distribution and Frame-specific Evidence**  
*Total Indexed Scenes: 626 | Declared Frame Descriptors: 48,239 | Entity Archetypes: 250*

---

## 1. Executive Summary & Scene Sprite Architecture

In *Star Ocean: The Second Story*, all town environments, dungeon corridors, castle interiors,
and story setpieces are packaged as multi-part container archives (`Archives 3207..4154`).

While `tag == 0` stores the 3D polygon collision walkmesh and `tag == 1` stores script bytecode,
**`tag == 2` serves as the 2D Field NPC Sprite Bank** (verified present in 827 of 948 scene archives).

### Section Binary Layout in `tag == 2`
Each section within `tag == 2` begins with a 32-byte header followed by dynamic sprite descriptors:
```
Section Header Layout:
  +0x00: record_count (uint32 LE) - Number of animation records (typically 1 or 2)
  +0x04: selector_id  (uint32 LE) - Entity selector identifier (observed values include 32767)
  +0x08: anim_min     (uint32 LE) - Minimum animation state index (e.g. 0)
  +0x0C: anim_max     (uint32 LE) - Maximum animation state index (e.g. 13 = idle/walk)
  +0x18: animation record offset (relative to section; mode byte at offset + 2)
  +0x1C: sprite_ptr   (uint32 LE) - Relative offset to Sprite Container Block (p3)
```

When an NPC entity is spawned on the field, the game engine's animation dispatcher (`0x8003F518`)
matches the entity's selector (`obj->0x16`) against `selector_id` in `tag == 2` to bind
its 12-byte frame descriptors and 16-color BGR555 CLUT palette.
The descriptor block starts after a 12-byte header for mode 1, otherwise a 16-byte header.
Frame totals here count declared descriptors, including frames the extractor may skip.

---

## 2. Entity Selectors

Only the `0..11` hero range is asserted as a specific identity below - that mapping is
independently grounded in this project's already-verified 12-character ID scheme used
throughout the save format itself. Every other selector ID is intentionally left
unclassified: an earlier draft of this doc guessed specific content ("switch monkey",
"town children", "guards", etc.) purely from selector ID / pixel-dimension coincidences,
with zero visual confirmation. On manager review, every one of those guesses that was
actually checked against a real extracted frame turned out to be wrong - dimensions
guessed as a "quadruped switch monkey" were, in every checked instance, an ordinary
humanoid NPC or child. Do not reintroduce specific content labels for non-hero selectors
without first visually inspecting an extracted frame for that exact selector.

| Selector ID | Category |
| :---: | :--- |
| **`0..11`** | **Playable Heroes** - Claude, Rena, Celine, Bowman, Dias, Precis, Ashton, Leon, Opera, Ernest, Noel, Chisato |
| everything else | **Unclassified** - see the per-scene tables below for each selector's raw ID and dimensions; extract and view the actual frame ([`tools/so2_scene_npc_extract.py`](file:///C:/CodeTesting/SaveConverter/tools/so2_scene_npc_extract.py)) before assuming what it depicts |

---

### 2.1 Frame-specific visual evidence

These are visual descriptions of personally viewed decoded frames, not named character
identifications. Each observation applies only to the cited archive/section/frame; it
does not classify every occurrence of that selector or establish a gameplay role.
Other selectors remain unclassified. The hero mapping above is inherited project evidence.

| Selector | Visual observation | Exact viewed frame (local artifact) |
| :---: | :--- | :--- |
| 12 | Green-clad humanoid wearing a pointed hat | `artifacts/so2-sprites/scene_3287/sec01_f00.png` |
| 13 | Purple-hooded humanoid | `artifacts/so2-sprites/scene_3287/sec00_f00.png` |
| 14 | Blue-helmeted humanoid in a tunic | `artifacts/so2-sprites/scene_3287/sec02_f00.png` |
| 15 | White-haired humanoid in blue and brown clothing | `artifacts/so2-sprites/scene_3233/sec04_f00.png` |
| 16 | Female humanoid in blue apron dress with white puff sleeves, brown hair in a bun | `artifacts/so2-sprites/scene_3243/sec00_f00.png` |
| 17 | Male humanoid wearing blue bandanna/cap and white shopkeeper apron over brown tunic | `artifacts/so2-sprites/scene_3282/sec05_f00.png` |
| 18 | Small brown and tan quadruped creature / raccoon-like forest mammal with round ears | `artifacts/so2-sprites/scene_3219/sec13_f00.png` |
| 20 | Brown-haired humanoid in a turquoise top | `artifacts/so2-sprites/scene_3230/sec03_f00.png` |
| 21 | Humanoid with a closed blue helmet | `artifacts/so2-sprites/scene_3240/sec01_f00.png` |
| 22 | Small young girl humanoid in orange/red dress with red hair ribbons and green hair | `artifacts/so2-sprites/scene_3225/sec16_f00.png` |
| 23 | Small child humanoid with blonde/greenish hair in blue vest and white shirt | `artifacts/so2-sprites/scene_3240/sec02_f00.png` |
| 24 | Balding pointed-eared humanoid in green | `artifacts/so2-sprites/scene_3442/sec06_f00.png` |
| 25 | White-haired bearded humanoid in yellow and blue | `artifacts/so2-sprites/scene_3464/sec04_f00.png` |
| 26 | Elderly male humanoid with white hair, pointed ears, wearing white robe with gold trim | `artifacts/so2-sprites/scene_3439/sec29_f00.png` |
| 27 | Small brown puppy/dog creature | `artifacts\so2-sprites\scene_3234\sec17_f00.png` |
| 28 | Blue-haired humanoid in blue and white clothing | `artifacts/so2-sprites/scene_3442/sec04_f00.png` |
| 29 | Young male humanoid with green hair, white tunic with brown leather straps and green boots | `artifacts/so2-sprites/scene_3442/sec09_f00.png` |
| 30 | Young woman humanoid with long light brown hair in green dress with white collar | `artifacts/so2-sprites/scene_3224/sec12_f00.png` |
| 31 | Young girl humanoid with pink pigtails in lavender/light blue pinafore dress | `artifacts/so2-sprites/scene_3230/sec02_f00.png` |
| 32 | Small purple-hooded humanoid | `artifacts/so2-sprites/scene_3207/sec13_f00.png` |
| 33 | Small boy humanoid with brown cap/hair, yellow hooded collar, blue pants | `artifacts/so2-sprites/scene_3329/sec03_f00.png` |
| 35 | Elderly scholar/monk humanoid with pointed hood/headdress and brown/purple robes | `artifacts/so2-sprites/scene_3398/sec16_f00.png` |
| 36 | Small young girl humanoid wearing pink pointed mushroom-like hat, green apron/dress | `artifacts/so2-sprites/scene_3353/sec09_f00.png` |
| 37 | Small child humanoid with pink hair buns in white/blue outfit | `artifacts/so2-sprites/scene_3328/sec02_f00.png` |
| 38 | Small pale long-eared animal | `artifacts/so2-sprites/scene_3219/sec16_f00.png` |
| 39 | Brown and white sitting dog / puppy with floppy ears | `artifacts/so2-sprites/scene_3219/sec14_f00.png` |
| 40 | Balding humanoid in a green top | `artifacts/so2-sprites/scene_3250/sec08_f00.png` |
| 41 | Young male humanoid in hooded blue winter coat and boots | `artifacts/so2-sprites/scene_3281/sec20_f00.png` |
| 42 | Female scholar humanoid with white headdress, holding a red book, wearing blue coat | `artifacts/so2-sprites/scene_3282/sec26_f00.png` |
| 43 | Female scholar humanoid with white headdress, blue outfit holding a red book (variant palette) | `artifacts/so2-sprites/scene_3312/sec26_f00.png` |
| 44 | Bald humanoid in purple holding a cane | `artifacts/so2-sprites/scene_3224/sec06_f00.png` |
| 45 | Elderly male humanoid with walking cane, wearing light blue hat and coat | `artifacts/so2-sprites/scene_3331/sec21_f00.png` |
| 46 | Elderly male humanoid with grey beard, grey knit cap and purple coat | `artifacts/so2-sprites/scene_3351/sec05_f00.png` |
| 47 | Small girl child humanoid with blue pigtails and white bonnet/headdress, yellow apron | `artifacts/so2-sprites/scene_3207/sec12_f00.png` |
| 48 | Small girl humanoid with reddish-pink pigtails, blue dress and white collar | `artifacts/so2-sprites/scene_3207/sec14_f00.png` |
| 49 | Humanoid in pale blue uniform and peaked cap | `artifacts/so2-sprites/scene_3265/sec04_f00.png` |
| 50 | Young boy humanoid wearing grey flat cap and striped grey overalls | `artifacts/so2-sprites/scene_3219/sec10_f00.png` |
| 51 | Elderly woman humanoid with white hair in a bun, green dress and apron, hands folded | `artifacts/so2-sprites/scene_3251/sec11_f00.png` |
| 52 | Elderly woman humanoid with glasses, white hair, yellow sweater and blue skirt | `artifacts/so2-sprites/scene_3398/sec17_f00.png` |
| 53 | Woman humanoid with purple hair in green tunic and purple boots | `artifacts/so2-sprites/scene_3419/sec03_f00.png` |
| 54 | Young girl humanoid in purple hooded cape and green dress | `artifacts/so2-sprites/scene_3629/sec09_f00.png` |
| 55 | Young child humanoid in purple cowl/hood and green tunic | `artifacts/so2-sprites/scene_3281/sec22_f00.png` |
| 56 | Small green-hooded humanoid in brown clothing | `artifacts/so2-sprites/scene_3329/sec07_f00.png` |
| 57 | Young female humanoid with pink twin buns wearing blue/grey coat with fur trim | `artifacts/so2-sprites/scene_3442/sec07_f00.png` |
| 58 | Nedian woman humanoid with pointed ears, teal hair, purple vest and dark skirt | `artifacts/so2-sprites/scene_3442/sec08_f00.png` |
| 59 | Elderly scholar humanoid with white beard, ornate headdress, wearing red/brown robes with scroll | `artifacts/so2-sprites/scene_3331/sec07_f00.png` |
| 60 | Scholar humanoid wearing blue pointed hood with gold trim, long robes | `artifacts/so2-sprites/scene_3391/sec02_f00.png` |
| 62 | Small child humanoid with winged green hat/helmet and brown coat | `artifacts/so2-sprites/scene_3419/sec10_f00.png` |
| 63 | Elderly female humanoid wearing purple hooded cape over white/green dress | `artifacts/so2-sprites/scene_3335/sec03_f00.png` |
| 64 | Grey-bearded humanoid in a blue cap holding a staff | `artifacts/so2-sprites/scene_3333/sec04_f00.png` |
| 65 | Small burst/spark particle effect | `artifacts\so2-sprites\scene_3219\sec15_f00.png` |
| 66 | Purple penguin-shaped creature | `artifacts\so2-sprites\scene_3225\sec18_f00.png` |
| 67 | Male humanoid with spiky silver/light-blue hair, pink vest, dark pants | `artifacts/so2-sprites/scene_3207/sec10_f00.png` |
| 68 | Male humanoid with green hair, green vest over white shirt | `artifacts/so2-sprites/scene_3207/sec11_f00.png` |
| 71 | Female humanoid with teal hair in teal coat with pink scarf/trim | `artifacts/so2-sprites/scene_3312/sec27_f00.png` |
| 72 | Female humanoid with pink hair in light-blue hooded coat | `artifacts/so2-sprites/scene_3324/sec03_f00.png` |
| 73 | Small boy humanoid with green hair, purple hooded collar, blue pants | `artifacts/so2-sprites/scene_3331/sec19_f00.png` |
| 74 | Small child humanoid wearing red aviator cap/helmet and blue tunic with red cape | `artifacts/so2-sprites/scene_3331/sec22_f00.png` |
| 75 | White-haired humanoid in a blue coat holding a cane | `artifacts/so2-sprites/scene_3224/sec10_f00.png` |
| 76 | Tan quadruped with pointed ears and a raised dark-tipped tail | `artifacts/so2-sprites/scene_3219/sec17_f00.png` |
| 77 | Small blue-white bird or dove object | `artifacts\so2-sprites\scene_3268\sec12_f00.png` |
| 78 | Performer humanoid with styled pink hair, purple vest/tunic, white pants | `artifacts/so2-sprites/scene_3265/sec00_f00.png` |
| 79 | Black-haired moustached humanoid in a pale shirt and blue trousers | `artifacts/so2-sprites/scene_3265/sec05_f00.png` |
| 80 | Mature woman humanoid with silver-white hair, blue dress with white blouse (Rena's mother Westa) | `artifacts/so2-sprites/scene_3225/sec15_f00.png` |
| 81 | Humanoid wearing a white chef hat and uniform | `artifacts/so2-sprites/scene_3258/sec01_f00.png` |
| 82 | Young male humanoid with dark hair, white buttoned shirt and grey pants | `artifacts/so2-sprites/scene_3329/sec05_f00.png` |
| 83 | Young male humanoid with spiky silver/grey hair, white shirt and grey pants | `artifacts/so2-sprites/scene_3329/sec06_f00.png` |
| 84 | Small blue round-headed robot creature | `artifacts\so2-sprites\scene_3225\sec17_f00.png` |
| 85 | Male humanoid with blue hair, ornate blue and gold tunic/armor | `artifacts/so2-sprites/scene_3230/sec04_f00.png` |
| 86 | Woman humanoid with blonde hair in red hooded cloak with white fur trim | `artifacts/so2-sprites/scene_3331/sec09_f00.png` |
| 87 | Small rifle or long weapon object | `artifacts\so2-sprites\scene_3331\sec08_f00.png` |
| 88 | Armored humanoid with a blue helmet and long pole weapon | `artifacts/so2-sprites/scene_3216/sec05_f00.png` |
| 89 | Armored humanoid with a pale helmet and long pole weapon | `artifacts/so2-sprites/scene_3216/sec06_f00.png` |
| 90 | Small pale oval object (food or item) | `artifacts\so2-sprites\scene_3293\sec23_f00.png` |
| 91 | Elderly woman humanoid in grey headscarf/bonnet and olive green apron dress | `artifacts/so2-sprites/scene_3293/sec20_f00.png` |
| 92 | Blonde soldier/knight humanoid in blue tunic and silver breastplate armor | `artifacts/so2-sprites/scene_3250/sec07_f00.png` |
| 93 | Elderly king/regal humanoid with white beard and golden crown, red and gold royal robes | `artifacts/so2-sprites/scene_3293/sec19_f00.png` |
| 94 | Blue mechanical egg-shaped robot with red antenna/visor and red feet | `artifacts/so2-sprites/scene_3225/sec27_f00.png` |
| 95 | Queen/noblewoman humanoid with blonde hair wearing ornate white and pink royal gown with tiara | `artifacts/so2-sprites/scene_3293/sec18_f00.png` |
| 96 | Male researcher/scientist humanoid with blonde hair in long white lab coat | `artifacts/so2-sprites/scene_3449/sec07_f00.png` |
| 97 | Small grey and white pigeon / bird resting/pecking on the ground | `artifacts/so2-sprites/scene_3216/sec09_f00.png` |
| 99 | Gold-colored cup-shaped object | `artifacts/so2-sprites/scene_3587/sec07_f00.png` |
| 100 | Small shiny gold coin / circular token prop | `artifacts/so2-sprites/scene_3259/sec01_f00.png` |
| 101 | Blonde female humanoid in ornate white/red heraldic priestess gown | `artifacts/so2-sprites/scene_3282/sec09_f00.png` |
| 102 | Humanoid wearing a tall blue and gold hat and robe | `artifacts/so2-sprites/scene_3224/sec11_f00.png` |
| 103 | Male humanoid with green hair in blue/purple knight tunic with gold accents | `artifacts/so2-sprites/scene_3281/sec24_f00.png` |
| 104 | Male humanoid with black hair in red jacket/coat and dark trousers | `artifacts/so2-sprites/scene_3216/sec08_f00.png` |
| 105 | Young woman humanoid with long dark-blue hair in purple apron dress | `artifacts/so2-sprites/scene_3349/sec10_f00.png` |
| 106 | Male humanoid with dark hair, purple scholar robe with pink trim | `artifacts/so2-sprites/scene_3277/sec00_f00.png` |
| 107 | Green-haired humanoid wearing a white coat | `artifacts/so2-sprites/scene_3376/sec09_f00.png` |
| 108 | Pink-haired humanoid wearing a white coat | `artifacts/so2-sprites/scene_3376/sec10_f00.png` |
| 109 | Young male humanoid with dark hair in white shirt and tan vest/shorts | `artifacts/so2-sprites/scene_3351/sec06_f00.png` |
| 110 | Young boy humanoid with light brown hair in blue denim overalls | `artifacts/so2-sprites/scene_3895/sec08_f00.png` |
| 111 | Young girl humanoid with long blue hair, headband, orange apron dress | `artifacts/so2-sprites/scene_3281/sec28_f00.png` |
| 112 | Girl humanoid with brown bob cut and white headband, blue pinafore dress | `artifacts/so2-sprites/scene_3281/sec29_f00.png` |
| 113 | Male researcher/doctor humanoid with glasses and white lab coat | `artifacts/so2-sprites/scene_3237/sec07_f00.png` |
| 114 | Winged angelic figure holding a glowing light orb | `artifacts\so2-sprites\scene_3355\sec04_f00.png` |
| 115 | Armored winged angelic/guardian figure | `artifacts\so2-sprites\scene_3218\sec08_f00.png` |
| 116 | Humanoid in a white uniform and cap with a pink cross | `artifacts/so2-sprites/scene_3649/sec04_f00.png` |
| 118 | Woman humanoid with blue hair in green dress and red shawl | `artifacts/so2-sprites/scene_3391/sec05_f00.png` |
| 119 | Military/naval officer humanoid with peaked cap and brown uniform with gold epaulets | `artifacts/so2-sprites/scene_3315/sec12_f00.png` |
| 120 | Middle-aged male humanoid with mustache, white work shirt and brown trousers | `artifacts/so2-sprites/scene_3390/sec11_f00.png` |
| 121 | Armored robotic or mechanical knight figure | `artifacts\so2-sprites\scene_3453\sec00_f00.png` |
| 122 | Dark bird silhouette / shadow flying in profile (large shadow bird/hawk) | `artifacts/so2-sprites/scene_3665/sec02_f00.png` |
| 123 | Dark gliding creature shadow / silhouette viewed from above (flying squirrel / ray shadow) | `artifacts/so2-sprites/scene_3663/sec04_f00.png` |
| 124 | Long pink serpentine creature | `artifacts/so2-sprites/scene_3278/sec13_f00.png` |
| 125 | Figure in dark robes holding an ornate glowing golden staff/relic topped with a sphere | `artifacts/so2-sprites/scene_3370/sec08_f00.png` |
| 126 | Female humanoid with long reddish hair, silver breastplate armor and blue trim | `artifacts/so2-sprites/scene_3676/sec23_f00.png` |
| 127 | Muscular shirtless male martial artist humanoid with spiky dark hair and red waist sash | `artifacts/so2-sprites/scene_3512/sec06_f00.png` |
| 128 | Male humanoid in brown hooded cloak and leather tunic | `artifacts/so2-sprites/scene_3217/sec10_f00.png` |
| 129 | Young woman humanoid with pink hair in purple apron dress with white lace | `artifacts/so2-sprites/scene_3495/sec07_f00.png` |
| 131 | Blue-tunic swordsman/pirate humanoid with blue bandana, brandishing a curved green cutlass | `artifacts/so2-sprites/scene_3963/sec03_f09.png` |
| 133 | Large bird with spread purple and gold wings | `artifacts/so2-sprites/scene_3592/sec00_f00.png` |
| 135 | Chunky robot/humanoid with white spiked mask/helmet, blue overalls, yellow eye/visor | `artifacts/so2-sprites/scene_3649/sec07_f01.png` |
| 136 | Armored gladiator/guard figure with horned helmet, silver chestplate and purple plume | `artifacts/so2-sprites/scene_3649/sec08_f00.png` |
| 137 | Calnus starship commander in red uniform with peaked cap and gold braid (Admiral Ronixis J. Kenni) | `artifacts/so2-sprites/scene_3211/sec01_f00.png` |
| 138 | Federation officer humanoid with slicked silver hair, white dress uniform with red collar/trim | `artifacts/so2-sprites/scene_3211/sec02_f00.png` |
| 139 | Federation crewman humanoid with beret, brown and white uniform | `artifacts/so2-sprites/scene_3211/sec04_f00.png` |
| 140 | Male humanoid wearing safari pith helmet, tan explorer outfit with satchel | `artifacts/so2-sprites/scene_3832/sec09_f00.png` |
| 141 | Bald elderly male humanoid in green athletic tracksuit/tunic | `artifacts/so2-sprites/scene_3376/sec11_f00.png` |
| 142 | Elderly gentleman humanoid with grey beard in stylish yellow suit and tie | `artifacts/so2-sprites/scene_3829/sec03_f00.png` |
| 143 | Young male federation crewman humanoid with brown hair in silver/grey bodysuit | `artifacts/so2-sprites/scene_3211/sec03_f00.png` |
| 144 | Small blonde toddler/child humanoid in pink/peach smock | `artifacts/so2-sprites/scene_3835/sec02_f00.png` |
| 145 | Small child humanoid with blue hair, blue beret/cap, red tunic with yellow collar | `artifacts/so2-sprites/scene_3221/sec15_f00.png` |
| 146 | Male knight/officer humanoid with short blue hair in silver armor with orange pauldrons | `artifacts/so2-sprites/scene_3508/sec00_f00.png` |
| 147 | Blue mechanical robot figure | `artifacts\so2-sprites\scene_3488\sec10_f00.png` |
| 148 | Helmeted armored figure with a shield emblem | `artifacts\so2-sprites\scene_3645\sec03_f00.png` |
| 149 | Armored figure with a horned/ram helmet | `artifacts\so2-sprites\scene_3648\sec02_f00.png` |
| 150 | Red and gold treasure chest | `artifacts/so2-sprites/scene_3326/sec13_f00.png` |
| 151 | Red and gold treasure chest | `artifacts/so2-sprites/scene_3623/sec01_f00.png` |
| 152 | Red and gold treasure chest | `artifacts/so2-sprites/scene_3583/sec00_f00.png` |
| 153 | Red and gold treasure chest | `artifacts/so2-sprites/scene_3240/sec03_f00.png` |
| 154 | Red and gold treasure chest | `artifacts/so2-sprites/scene_3257/sec00_f00.png` |
| 155 | Red and gold treasure chest | `artifacts/so2-sprites/scene_3245/sec00_f00.png` |
| 156 | Red and gold treasure chest | `artifacts/so2-sprites/scene_3225/sec13_f00.png` |
| 157 | Red and gold treasure chest | `artifacts/so2-sprites/scene_3207/sec15_f00.png` |
| 158 | Red and gold treasure chest | `artifacts/so2-sprites/scene_3272/sec00_f00.png` |
| 159 | Red and gold treasure chest | `artifacts/so2-sprites/scene_3278/sec11_f00.png` |
| 160 | Red and gold treasure chest | `artifacts/so2-sprites/scene_3274/sec01_f00.png` |
| 161 | Red and gold treasure chest | `artifacts/so2-sprites/scene_3574/sec00_f00.png` |
| 167 | Bald elderly humanoid carrying a bag | `artifacts\so2-sprites\scene_3454\sec05_f00.png` |
| 168 | Nedian woman humanoid with pointed ears, teal hair, ornate blue and white ceremonial robe | `artifacts/so2-sprites/scene_3784/sec01_f00.png` |
| 169 | Blue quadrupedal dragon-like creature with red wings | `artifacts/so2-sprites/scene_3476/sec04_f00.png` |
| 170 | Blue-haired humanoid in a white coat | `artifacts/so2-sprites/scene_3476/sec02_f00.png` |
| 171 | Bulky horned armored figure carrying a curved blade | `artifacts/so2-sprites/scene_3579/sec01_f00.png` |
| 172 | Purple ray-like creature with a curled tail | `artifacts/so2-sprites/scene_3436/sec28_f00.png` |
| 174 | Small child humanoid with blue hair and cap, green tunic with gold trim (variant child palette) | `artifacts/so2-sprites/scene_3606/sec05_f00.png` |
| 175 | Male humanoid with mustache and sunglasses/dark goggles in dark futuristic coat | `artifacts/so2-sprites/scene_3850/sec07_f00.png` |
| 177 | Heavy armored knight in full silver/grey plate armor with plumed helmet and blue boots | `artifacts/so2-sprites/scene_3670/sec04_f00.png` |
| 178 | Small orange blocky mechanical/robotic creature | `artifacts\so2-sprites\scene_3663\sec00_f00.png` |
| 180 | Green winged humanoid creature | `artifacts/so2-sprites/scene_3655/sec00_f00.png` |
| 181 | Large crouching green and brown furred creature | `artifacts/so2-sprites/scene_3219/sec01_f00.png` |
| 182 | Blue humanoid-shaped figure | `artifacts/so2-sprites/scene_3686/sec00_f00.png` |
| 183 | Gold armored humanoid-shaped figure | `artifacts/so2-sprites/scene_3676/sec11_f00.png` |
| 184 | Horned beast / satyr-like creature with curved ram horns, white fur, claws | `artifacts/so2-sprites/scene_3730/sec00_f00.png` |
| 185 | Green reptilian humanoid with a tail | `artifacts/so2-sprites/scene_3679/sec04_f00.png` |
| 187 | Dark mechanical-looking legs and lower torso | `artifacts/so2-sprites/scene_3849/sec05_f00.png` |
| 188 | Purple winged humanoid-shaped creature | `artifacts/so2-sprites/scene_3654/sec13_f00.png` |
| 189 | Purple-tinted armored soldier/sentinel with helmet visor walking forward | `artifacts/so2-sprites/scene_3679/sec02_f00.png` |
| 190 | Large crouching red and brown furred creature | `artifacts/so2-sprites/scene_3679/sec03_f00.png` |
| 191 | Prone furred creature | `artifacts/so2-sprites/scene_3669/sec05_f00.png` |
| 192 | Small elderly humanoid with goggles/bandaged head, green hooded cape and walking cane | `artifacts/so2-sprites/scene_3439/sec32_f00.png` |
| 193 | Young girl humanoid with pink hair, wearing white/blue hooded cloak holding hands together | `artifacts/so2-sprites/scene_3439/sec31_f00.png` |
| 194 | Winged dark-robed humanoid with bat-like wings | `artifacts\so2-sprites\scene_3439\sec33_f00.png` |
| 195 | Woman standing beside a large spider-like creature | `artifacts\so2-sprites\scene_3404\sec07_f00.png` |
| 196 | Nedian youth humanoid with pointed ears, blue hair, white/blue tunic with yellow belt | `artifacts/so2-sprites/scene_3517/sec01_f00.png` |
| 197 | Gold armored winged dragon-like creature | `artifacts\so2-sprites\scene_3432\sec23_f00.png` |
| 198 | Small winged fairy-shaped humanoid creature | `artifacts\so2-sprites\scene_3509\sec01_f00.png` |
| 199 | Large round pale pink creature with long ears | `artifacts/so2-sprites/scene_3444/sec04_f00.png` |
| 200 | Large red bird/phoenix-like creature with spread wings | `artifacts\so2-sprites\scene_3803\sec00_f00.png` |
| 201 | Mechanical wall bracket / bronze machinery fixture with cogwheels and pipes | `artifacts/so2-sprites/scene_3864/sec09_f00.png` |
| 202 | Floor lever mechanism with teal/metal cylindrical base and upright lever handle | `artifacts/so2-sprites/scene_3864/sec10_f08.png` |
| 204 | Large dark whale-or-sea-creature silhouette (partial frame) | `artifacts\so2-sprites\scene_3587\sec01_f00.png` |
| 205 | Female humanoid/sorceress with dark horns/headdress in an elaborate red slit dress | `artifacts/so2-sprites/scene_3912/sec01_f00.png` |
| 206 | Drider / Arachne creature: female humanoid upper body with blonde hair atop a massive multi-legged spider body | `artifacts/so2-sprites/scene_3624/sec01_f00.png` |
| 207 | Large quadruped purple demonic beast with long black tail, dorsal spikes, and sharp white claws | `artifacts/so2-sprites/scene_3918/sec00_f03.png` |
| 209 | Pair of pink glowing platform pads / oval energy steps | `artifacts/so2-sprites/scene_3934/sec01_f00.png` |
| 210 | Horizontal green metallic grated panel / floor strip | `artifacts/so2-sprites/scene_3923/sec01_f01.png` |
| 211 | Massive crumbled stone golem boss statue / ancient stone colossus head and shoulder fragments (216x180) | `artifacts/so2-sprites/scene_3970/sec01_f00.png` |
| 212 | Ancient sage / Wise Man boss figure with long white beard, purple and green robes, holding crystal staff (96x74) | `artifacts/so2-sprites/scene_3993/sec03_f04.png` |
| 213 | Green mechanical-looking legs and lower torso | `artifacts/so2-sprites/scene_3810/sec00_f00.png` |
| 214 | Ornate winged golden relic / mechanical dagger obelisk flanked by skull pedestal shoulders (76x112) | `artifacts/so2-sprites/scene_4014/sec03_f00.png` |
| 215 | Dark winged fairy / valkyrie boss figure with halo, dark feathered wings, holding silver lance/glaive (92x130) | `artifacts/so2-sprites/scene_4022/sec00_f04.png` |
| 216 | Large red bird creature with spread wings | `artifacts\so2-sprites\scene_4016\sec00_f00.png` |
| 217 | Pulsating pink organic bio-cocoon / alien egg sac with vein-like ridges (100x76) | `artifacts/so2-sprites/scene_3982/sec02_f05.png` |
| 218 | Young boy humanoid with green headband, white shirt and green shorts | `artifacts/so2-sprites/scene_3240/sec04_f00.png` |
| 219 | Red crustacean-like creature with claws | `artifacts/so2-sprites/scene_3619/sec03_f00.png` |
| 220 | Gold winged humanoid creature | `artifacts/so2-sprites/scene_3755/sec12_f00.png` |
| 221 | Colossal grey leviathan / whale monster head and maw (Phynal setpiece, 116x109) | `artifacts/so2-sprites/scene_3794/sec00_f00.png` |
| 223 | Soldier humanoid in green helmet and military fatigues | `artifacts/so2-sprites/scene_3353/sec08_f00.png` |
| 227 | Masked ninja / assassin humanoid in grey garb wielding a curved scimitar/dagger | `artifacts/so2-sprites/scene_3965/sec00_f09.png` |
| 228 | Grayscale (monochrome) hooded/robed humanoid figure | `artifacts\so2-sprites\scene_3925\sec00_f00.png` |
| 229 | Grayscale (monochrome) robed humanoid figure | `artifacts\so2-sprites\scene_3927\sec00_f00.png` |
| 230 | Grayscale (monochrome) hooded humanoid figure | `artifacts\so2-sprites\scene_3924\sec00_f00.png` |
| 231 | Grayscale (monochrome) robed humanoid figure | `artifacts\so2-sprites\scene_3924\sec01_f00.png` |
| 232 | Grayscale (monochrome) humanoid figure | `artifacts\so2-sprites\scene_3928\sec00_f00.png` |
| 233 | Grayscale (monochrome) robed humanoid figure | `artifacts\so2-sprites\scene_3927\sec01_f00.png` |
| 234 | Grayscale (monochrome) humanoid figure | `artifacts\so2-sprites\scene_3925\sec01_f00.png` |
| 235 | Gold bird with spread wings | `artifacts/so2-sprites/scene_3566/sec01_f00.png` |
| 237 | Nedian male humanoid with pointed ears, mustache, wearing brown patterned tunic | `artifacts/so2-sprites/scene_3540/sec02_f00.png` |
| 238 | Male researcher/clerk humanoid with dark hair, white buttoned lab coat/shirt | `artifacts/so2-sprites/scene_3393/sec15_f00.png` |
| 239 | Nedian male humanoid with pointed ears, silver hair, white and purple formal vest | `artifacts/so2-sprites/scene_3539/sec06_f00.png` |
| 501 | Wooden barrel / stool topped with a round red cushioned seat (8bpp prop) | `artifacts/so2-sprites/scene_3224/sec17_f00.png` |
| 502 | Row of red hardbound books on a shelf / red book spine (8bpp prop) | `artifacts/so2-sprites/scene_3225/sec09_f00.png` |
| 503 | Row of white/cream parchment books or paper folios on a shelf (8bpp prop) | `artifacts/so2-sprites/scene_3225/sec10_f00.png` |
| 504 | Wooden doorway frame draped with vertical green curtain blinds / noren (8bpp prop) | `artifacts/so2-sprites/scene_3225/sec11_f00.png` |
| 505 | Angled perspective wooden door / doorway shutter pane with blue slats (8bpp prop) | `artifacts/so2-sprites/scene_3225/sec12_f00.png` |
| 506 | Square dark wooden trapdoor / cellar hatch with metal studs (8bpp prop) | `artifacts/so2-sprites/scene_3251/sec06_f00.png` |
| 507 | Dark brown wooden cellar hatch / floor panel (8bpp prop) | `artifacts/so2-sprites/scene_3251/sec07_f01.png` |
| 508 | Large angled dark wooden cellar door hatch viewed in 3/4 perspective (8bpp prop) | `artifacts/so2-sprites/scene_3251/sec08_f02.png` |
| 509 | Vertical dark wooden cellar door panel with metal bands (8bpp prop) | `artifacts/so2-sprites/scene_3251/sec09_f03.png` |
| 510 | Dark wooden cellar door panel matching 509 pair (8bpp prop) | `artifacts/so2-sprites/scene_3251/sec10_f04.png` |
| 513 | Blue striped doorway curtain / awning cloth piece in Clik coastal town style (8bpp prop) | `artifacts/so2-sprites/scene_3312/sec14_f00.png` |
| 514 | Narrow vertical blue striped window shutter / door slat (8bpp prop) | `artifacts/so2-sprites/scene_3312/sec15_f00.png` |
| 515 | Double blue wooden shutters with brass handles (8bpp prop) | `artifacts/so2-sprites/scene_3312/sec16_f00.png` |
| 516 | Blue window shutter pane with horizontal gold trim (8bpp prop) | `artifacts/so2-sprites/scene_3312/sec17_f00.png` |
| 517 | Angled perspective blue window shutter panel pair (8bpp prop) | `artifacts/so2-sprites/scene_3312/sec18_f00.png` |
| 518 | Blue arched doorway shutter with brass horizontal bar (8bpp prop) | `artifacts/so2-sprites/scene_3314/sec01_f00.png` |
| 519 | Arched blue doorway shutter with brass horizontal bar, wide variant (8bpp prop) | `artifacts/so2-sprites/scene_3314/sec02_f00.png` |
| 520 | Angled perspective blue door panel with brass handle (8bpp prop) | `artifacts/so2-sprites/scene_3314/sec03_f00.png` |
| 521 | Blue wooden arched door with gold doorknob (8bpp prop) | `artifacts/so2-sprites/scene_3314/sec04_f00.png` |
| 522 | Arched blue door with circular window and brass latch (8bpp prop) | `artifacts/so2-sprites/scene_3282/sec01_f00.png` |
| 523 | Rectangular blue wooden door with red sign plaque and brass latch (8bpp prop) | `artifacts/so2-sprites/scene_3282/sec02_f00.png` |
| 524 | Arched blue wooden door with circular glass window (8bpp prop) | `artifacts/so2-sprites/scene_3282/sec03_f00.png` |
| 525 | Dark brown panel door with rectangular window panes (8bpp prop) | `artifacts/so2-sprites/scene_3350/sec00_f00.png` |
| 526 | Arched dark blue door with horizontal gold brass plate (8bpp prop) | `artifacts/so2-sprites/scene_3349/sec00_f00.png` |
| 527 | Arched dark blue door panel with square brass plate (8bpp prop) | `artifacts/so2-sprites/scene_3349/sec01_f00.png` |
| 528 | Angled dark red wooden door with brass handle (8bpp prop) | `artifacts/so2-sprites/scene_3349/sec02_f00.png` |
| 529 | Arched dark blue door with central rectangular gold plate (8bpp prop) | `artifacts/so2-sprites/scene_3349/sec03_f00.png` |
| 530 | Angled dark blue arched door panel with brass plate (8bpp prop) | `artifacts/so2-sprites/scene_3349/sec04_f00.png` |
| 531 | Tilted red hardbound book on a desk / shelf with gold page edges (8bpp prop) | `artifacts/so2-sprites/scene_3376/sec05_f00.png` |
| 532 | Red rectangular door hatch / window frame with black horizontal slit (8bpp prop) | `artifacts/so2-sprites/scene_3425/sec05_f00.png` |
| 533 | Arched blue wooden door with brass knocker and handle (8bpp prop) | `artifacts/so2-sprites/scene_3423/sec00_f00.png` |
| 534 | Tall arched wooden door with glass window and red OFF LIMITS / warning sign placard (8bpp prop) | `artifacts/so2-sprites/scene_3417/sec07_f00.png` |
| 535 | Red hardbound book with white label on front cover (8bpp prop) | `artifacts/so2-sprites/scene_3422/sec02_f00.png` |
| 10000 | Orange and yellow glowing orb | `artifacts/so2-sprites/scene_3212/sec03_f00.png` |
| 32766 | Purple orb on a slender gold stand | `artifacts/so2-sprites/scene_3211/sec00_f00.png` |
| 32767 | Small yellow pointed streak | `artifacts/so2-sprites/scene_3212/sec00_f00.png` |

## 3. Regional Scene Sprite Breakdown

### 3.16 Opening / Expel Setpieces & Intro Sequences
*Active Scenes: 17 | Total Sprite Frames: 2,701*

| Archive | Scene ID | Sections | Frames | Heroes Present | Other Selectors (ID: dims) |
| :---: | :---: | :---: | :---: | :--- | :--- |
| **`3207`** | `Scene 000` | 16 | 318 | Celine Jules, Bowman Jean, Dias Flac, Precis F. Neumann, Ashton Anchors, Leon D.S. Gehste, Opera Vectra, Ernest Ravine, Noel Chandler, Chisato Madison | 67: 24x46, 68: 24x45, 47: 24x31, 32: 20x31, 48: 24x34, 157: 28x27 |
| **`3208`** | `Scene 001` | 16 | 318 | Celine Jules, Bowman Jean, Dias Flac, Precis F. Neumann, Ashton Anchors, Leon D.S. Gehste, Opera Vectra, Ernest Ravine, Noel Chandler, Chisato Madison | 67: 24x46, 68: 24x45, 47: 24x31, 32: 20x31, 48: 24x34, 157: 28x27 |
| **`3209`** | `Scene 002` | 16 | 318 | Celine Jules, Bowman Jean, Dias Flac, Precis F. Neumann, Ashton Anchors, Leon D.S. Gehste, Opera Vectra, Ernest Ravine, Noel Chandler, Chisato Madison | 67: 24x46, 68: 24x45, 47: 24x31, 32: 20x31, 48: 24x34, 157: 28x27 |
| **`3210`** | `Scene 003` | 16 | 318 | Celine Jules, Bowman Jean, Dias Flac, Precis F. Neumann, Ashton Anchors, Leon D.S. Gehste, Opera Vectra, Ernest Ravine, Noel Chandler, Chisato Madison | 67: 24x46, 68: 24x45, 47: 24x31, 32: 20x31, 48: 24x34, 157: 28x27 |
| **`3211`** | `Scene 004` | 5 | 96 | - | 32766: 16x36, 137: 24x45, 138: 24x45, 143: 24x45, 139: 24x46 |
| **`3212`** | `Scene 005` | 5 | 83 | Claude Kenni | 32767: 12x17, 10000: 20x20, 67: 24x46 |
| **`3213`** | `Scene 006` | 2 | 42 | - | 137: 24x45, 143: 24x45 |
| **`3214`** | `Scene 007` | 6 | 112 | - | 67: 24x46, 32767: 8x5, 137: 24x45, 138: 24x45, 143: 24x45, 139: 24x46 |
| **`3215`** | `Scene 008` | 12 | 257 | Chisato Madison, Ernest Ravine | 32767: 12x17, 32767: 8x5, 67: 24x46, 137: 24x45, 138: 24x45, 143: 24x45 |
| **`3216`** | `Scene 009` | 12 | 127 | Rena Lanford | 32767: 8x5, 32767: 8x5, 32767: 12x17, 88: 24x47, 89: 24x47, 32766: 16x36 |
| **`3217`** | `Scene 010` | 16 | 125 | Rena Lanford, Claude Kenni, Dias Flac | 32767: 16x14, 32767: 16x13, 32767: 12x17, 32767: 8x5, 32767: 8x5, 10000: 44x31 |
| **`3218`** | `Scene 011` | 9 | 96 | Dias Flac | 32767: 16x14, 32767: 8x5, 10000: 44x31, 10000: 44x34, 10000: 24x29, 128: 24x46 |
| **`3219`** | `Scene 012` | 20 | 201 | Rena Lanford, Claude Kenni, Noel Chandler | 32767: 8x5, 181: 64x67, 181: 48x66, 32767: 16x13, 32767: 16x14, 32767: 8x5 |
| **`3220`** | `Scene 013` | 4 | 47 | Rena Lanford | 32767: 12x17, 115: 24x43, 10000: 40x42 |
| **`3221`** | `Scene 014` | 19 | 151 | Claude Kenni, Rena Lanford | 32767: 12x17, 32767: 16x14, 32767: 8x5, 32767: 8x5, 145: 24x30, 32767: 16x13 |
| **`3222`** | `Scene 015` | 3 | 35 | Rena Lanford | 115: 24x43, 10000: 40x42 |
| **`3223`** | `Scene 016` | 3 | 57 | Opera Vectra, Precis F. Neumann | 32767: 12x17 |

### 3.17 Arlia Village & Shingo Forest (Scene 017..037)
*Active Scenes: 20 | Total Sprite Frames: 1,807*

| Archive | Scene ID | Sections | Frames | Heroes Present | Other Selectors (ID: dims) |
| :---: | :---: | :---: | :---: | :--- | :--- |
| **`3224`** | `Scene 017` | 24 | 291 | Rena Lanford, Claude Kenni | 32767: 8x5, 32767: 8x5, 32767: 8x5, 44: 24x42, 32767: 12x17, 32767: 16x13 |
| **`3225`** | `Scene 018` | 30 | 304 | Claude Kenni, Rena Lanford, Celine Jules, Precis F. Neumann | 115: 24x43, 32767: 16x14, 32767: 8x5, 32767: 8x5, 32767: 8x5, 32767: 12x9 |
| **`3226`** | `Scene 019` | 8 | 101 | Claude Kenni | 75: 32x44, 115: 24x43, 32767: 16x13, 102: 24x46, 32767: 12x17, 32767: 8x5 |
| **`3227`** | `Scene 020` | 3 | 29 | - | 32767: 16x14, 30: 24x44, 501: 28x29 |
| **`3228`** | `Scene 021` | 9 | 79 | Rena Lanford | 75: 32x44, 32767: 16x13, 32767: 8x5, 32767: 8x5, 68: 24x45, 504: 26x35 |
| **`3229`** | `Scene 022` | 6 | 37 | Claude Kenni, Rena Lanford | 32767: 16x14, 32767: 8x5, 32767: 12x17, 10000: 8x5 |
| **`3230`** | `Scene 023` | 6 | 96 | - | 32767: 8x5, 102: 24x46, 31: 24x42, 20: 20x30, 85: 24x44, 32767: 12x18 |
| **`3231`** | `Scene 024` | 10 | 117 | - | 32767: 12x9, 32767: 8x5, 31: 24x42, 67: 24x46, 20: 20x30, 32767: 8x5 |
| **`3232`** | `Scene 025` | 1 | 3 | - | 156: 24x21 |
| **`3233`** | `Scene 026` | 9 | 95 | Ashton Anchors | 32767: 8x5, 32767: 16x13, 32767: 8x5, 32767: 8x5, 15: 20x43, 30: 24x44 |
| **`3234`** | `Scene 027` | 20 | 197 | Claude Kenni, Rena Lanford | 115: 24x43, 32767: 12x17, 32767: 16x13, 32767: 16x14, 31: 24x42, 32767: 8x5 |
| **`3236`** | `Scene 029` | 6 | 74 | - | 115: 24x43, 32767: 16x13, 75: 32x44, 32767: 16x14, 32767: 8x5, 32767: 12x17 |
| **`3237`** | `Scene 030` | 9 | 103 | - | 32767: 8x5, 115: 24x43, 32767: 8x5, 32767: 16x14, 32767: 16x13, 115: 32x20 |
| **`3238`** | `Scene 031` | 4 | 28 | Rena Lanford | 32767: 16x14, 32767: 12x17, 10000: 8x5 |
| **`3239`** | `Scene 032` | 2 | 23 | Rena Lanford | 67: 24x46 |
| **`3240`** | `Scene 033` | 7 | 70 | - | 32767: 16x13, 21: 20x30, 23: 20x30, 153: 20x29, 218: 24x41, 32767: 16x14 |
| **`3241`** | `Scene 034` | 4 | 47 | - | 75: 32x44, 32767: 12x17, 32767: 8x5, 32767: 12x18 |
| **`3242`** | `Scene 035` | 4 | 44 | Rena Lanford | 75: 32x44, 32767: 12x17, 32767: 8x5 |
| **`3243`** | `Scene 036` | 3 | 34 | - | 16: 20x40, 32767: 12x18, 32767: 8x5 |
| **`3244`** | `Scene 037` | 2 | 35 | - | 75: 32x44, 32767: 12x17 |

### 3.18 Salva Town & Salva Drift Cave (Scene 038..062)
*Active Scenes: 25 | Total Sprite Frames: 1,748*

| Archive | Scene ID | Sections | Frames | Heroes Present | Other Selectors (ID: dims) |
| :---: | :---: | :---: | :---: | :--- | :--- |
| **`3245`** | `Scene 038` | 11 | 63 | Rena Lanford | 155: 28x27, 32767: 16x14, 32767: 12x17, 32767: 16x13, 32767: 8x5, 32767: 8x5 |
| **`3246`** | `Scene 039` | 1 | 7 | Rena Lanford | - |
| **`3247`** | `Scene 040` | 1 | 3 | - | 155: 28x27 |
| **`3248`** | `Scene 041` | 6 | 74 | - | 75: 32x44, 115: 24x43, 32767: 16x14, 32767: 16x13, 32767: 8x5, 32767: 12x17 |
| **`3249`** | `Scene 042` | 6 | 59 | Claude Kenni | 75: 32x44, 32767: 8x5, 32767: 12x17, 32767: 8x5, 32767: 8x5 |
| **`3250`** | `Scene 043` | 15 | 220 | - | 31: 24x42, 67: 24x46, 68: 24x45, 22: 20x31, 32767: 12x18, 32767: 12x9 |
| **`3251`** | `Scene 044` | 24 | 289 | Claude Kenni | 32767: 8x5, 32767: 12x18, 32767: 8x5, 32767: 16x14, 32767: 8x5, 32767: 12x17 |
| **`3252`** | `Scene 045` | 1 | 21 | - | 51: 20x37 |
| **`3253`** | `Scene 046` | 2 | 28 | - | 32767: 16x13, 44: 24x42 |
| **`3254`** | `Scene 047` | 2 | 26 | - | 32767: 12x18, 80: 24x45 |
| **`3255`** | `Scene 048` | 7 | 93 | Claude Kenni | 32767: 12x17, 32767: 8x5, 31: 24x42, 67: 24x46, 68: 24x45 |
| **`3256`** | `Scene 049` | 2 | 28 | - | 104: 24x45, 32767: 8x5 |
| **`3257`** | `Scene 050` | 2 | 24 | - | 154: 24x31, 104: 24x45 |
| **`3258`** | `Scene 051` | 3 | 33 | - | 32767: 12x18, 81: 24x47, 32767: 8x5 |
| **`3259`** | `Scene 052` | 5 | 44 | - | 10000: 12x5, 100: 8x6, 10000: 8x5, 32767: 16x14, 67: 24x46 |
| **`3260`** | `Scene 053` | 8 | 78 | Rena Lanford | 32767: 16x14, 32767: 12x17, 32767: 8x5, 104: 24x45, 218: 24x41, 88: 24x47 |
| **`3261`** | `Scene 054` | 2 | 26 | - | 32767: 12x18, 16: 20x40 |
| **`3262`** | `Scene 055` | 2 | 42 | - | 40: 20x38, 68: 24x45 |
| **`3263`** | `Scene 056` | 10 | 87 | Rena Lanford | 32767: 8x5, 32767: 12x9, 32767: 16x13, 31: 24x42, 32767: 16x14, 32767: 8x5 |
| **`3264`** | `Scene 057` | 3 | 49 | - | 30: 24x44, 21: 20x30, 32767: 16x13 |
| **`3265`** | `Scene 058` | 7 | 157 | - | 78: 24x45, 92: 24x45, 88: 24x47, 89: 24x47, 49: 24x45, 79: 24x46 |
| **`3266`** | `Scene 059` | 8 | 86 | - | 32767: 12x9, 32767: 8x5, 32767: 16x13, 156: 24x21, 31: 24x42, 15: 20x43 |
| **`3267`** | `Scene 060` | 5 | 33 | - | 32767: 8x5, 32767: 12x18, 32767: 8x5, 32767: 16x14, 32767: 8x5 |
| **`3268`** | `Scene 061` | 14 | 108 | Rena Lanford, Claude Kenni | 32767: 12x17, 10000: 12x12, 104: 24x45, 104: 52x26, 32767: 8x5, 10000: 8x5 |
| **`3269`** | `Scene 062` | 8 | 70 | Claude Kenni, Rena Lanford | 32767: 12x17, 218: 20x26, 32767: 8x5, 32767: 8x5, 32766: 16x36, 218: 24x41 |

### 3.20 Cross Kingdom, Cross Castle & Clik Approach (Scene 063..098)
*Active Scenes: 34 | Total Sprite Frames: 3,060*

| Archive | Scene ID | Sections | Frames | Heroes Present | Other Selectors (ID: dims) |
| :---: | :---: | :---: | :---: | :--- | :--- |
| **`3270`** | `Scene 063` | 7 | 81 | - | 32767: 16x14, 32767: 12x17, 32767: 8x5, 88: 24x47, 32767: 8x5, 32767: 16x13 |
| **`3271`** | `Scene 064` | 2 | 6 | - | 153: 20x29, 155: 28x27 |
| **`3272`** | `Scene 065` | 1 | 3 | - | 158: 24x31 |
| **`3273`** | `Scene 066` | 1 | 3 | - | 156: 24x21 |
| **`3274`** | `Scene 067` | 4 | 34 | - | 32767: 8x5, 160: 24x31, 156: 24x21, 67: 24x46 |
| **`3275`** | `Scene 068` | 3 | 18 | - | 155: 28x27, 156: 24x21, 32766: 16x36 |
| **`3276`** | `Scene 069` | 1 | 3 | - | 156: 24x21 |
| **`3277`** | `Scene 070` | 7 | 84 | - | 106: 24x42, 106: 24x46, 32767: 16x14, 106: 24x46, 106: 24x46, 32767: 8x5 |
| **`3278`** | `Scene 071` | 15 | 189 | Ashton Anchors | 32767: 16x14, 32767: 8x5, 32767: 8x5, 32767: 12x17, 32767: 16x13, 106: 28x47 |
| **`3279`** | `Scene 072` | 1 | 3 | - | 156: 24x21 |
| **`3280`** | `Scene 073` | 5 | 19 | Celine Jules | 32767: 12x18, 32767: 16x14, 32767: 8x5 |
| **`3281`** | `Scene 074` | 35 | 503 | Celine Jules, Claude Kenni, Rena Lanford, Bowman Jean | 32767: 16x14, 32767: 16x13, 32767: 8x5, 32767: 12x18, 32767: 8x5, 10000: 20x20 |
| **`3282`** | `Scene 075` | 33 | 311 | Ashton Anchors, Precis F. Neumann, Claude Kenni, Rena Lanford | 32767: 16x13, 522: 14x24, 523: 18x22, 524: 16x23, 67: 24x46, 17: 20x43 |
| **`3283`** | `Scene 076` | 20 | 208 | Celine Jules, Rena Lanford, Claude Kenni | 79: 24x46, 20: 20x30, 32767: 8x5, 32767: 8x5, 32767: 16x14, 32767: 12x17 |
| **`3284`** | `Scene 077` | 12 | 127 | Ernest Ravine, Claude Kenni | 32767: 16x14, 32767: 8x5, 67: 24x46, 32767: 16x13, 32767: 8x5, 32767: 8x5 |
| **`3285`** | `Scene 078` | 4 | 37 | Rena Lanford | 32767: 8x5, 32767: 8x5, 89: 24x47 |
| **`3286`** | `Scene 079` | 2 | 28 | - | 32767: 16x13, 15: 20x43 |
| **`3287`** | `Scene 080` | 5 | 91 | Celine Jules | 13: 20x40, 12: 20x42, 14: 20x42, 32767: 8x5 |
| **`3288`** | `Scene 081` | 8 | 178 | - | 78: 24x45, 79: 24x46, 79: 24x46, 92: 24x45, 55: 24x44, 67: 24x46 |
| **`3289`** | `Scene 082` | 8 | 93 | Rena Lanford | 32767: 16x13, 32767: 8x5, 81: 24x47, 30: 24x44, 101: 24x45, 32767: 12x18 |
| **`3290`** | `Scene 083` | 7 | 63 | Rena Lanford, Claude Kenni | 32767: 16x14, 32767: 16x13, 32767: 8x5, 17: 20x43, 16: 20x40 |
| **`3291`** | `Scene 084` | 3 | 33 | - | 32767: 16x14, 32767: 8x5, 16: 20x40 |
| **`3292`** | `Scene 085` | 4 | 21 | Rena Lanford | 32767: 8x5, 32767: 16x14, 32767: 8x5 |
| **`3293`** | `Scene 086` | 25 | 325 | Rena Lanford, Claude Kenni, Celine Jules | 32767: 16x14, 32767: 8x5, 32767: 8x5, 32767: 12x18, 32767: 16x13, 32767: 8x5 |
| **`3294`** | `Scene 087` | 2 | 25 | - | 32767: 16x14, 67: 24x46 |
| **`3295`** | `Scene 088` | 1 | 21 | - | 67: 24x46 |
| **`3297`** | `Scene 090` | 15 | 183 | Rena Lanford, Claude Kenni, Celine Jules | 32767: 16x14, 32767: 8x5, 32767: 8x5, 92: 24x45, 88: 24x47, 68: 24x45 |
| **`3298`** | `Scene 091` | 1 | 21 | - | 88: 24x47 |
| **`3299`** | `Scene 092` | 1 | 3 | - | 156: 24x21 |
| **`3300`** | `Scene 093` | 2 | 42 | - | 88: 24x47, 89: 24x47 |
| **`3301`** | `Scene 094` | 2 | 42 | - | 93: 24x44, 89: 24x47 |
| **`3302`** | `Scene 095` | 14 | 174 | Rena Lanford, Claude Kenni, Celine Jules | 88: 24x47, 32767: 16x14, 32767: 12x17, 32767: 8x5, 32767: 8x5, 32767: 8x5 |
| **`3304`** | `Scene 097` | 2 | 25 | - | 32767: 16x14, 91: 24x42 |
| **`3305`** | `Scene 098` | 3 | 63 | - | 88: 24x47, 81: 24x47, 80: 24x45 |

### 3.22 Port Town of Clik & Disaster Ruins (Scene 099..128)
*Active Scenes: 27 | Total Sprite Frames: 3,395*

| Archive | Scene ID | Sections | Frames | Heroes Present | Other Selectors (ID: dims) |
| :---: | :---: | :---: | :---: | :--- | :--- |
| **`3306`** | `Scene 099` | 2 | 28 | - | 90: 24x42, 32767: 16x13 |
| **`3307`** | `Scene 100` | 7 | 57 | Celine Jules | 159: 20x29, 101: 24x45, 80: 24x45, 32767: 16x14 |
| **`3308`** | `Scene 101` | 2 | 42 | - | 95: 24x44, 80: 24x45 |
| **`3309`** | `Scene 102` | 3 | 63 | - | 90: 24x42, 91: 24x42, 80: 24x45 |
| **`3312`** | `Scene 105` | 28 | 315 | Claude Kenni, Rena Lanford, Celine Jules | 32767: 16x13, 32767: 12x9, 32767: 16x14, 32767: 8x5, 32767: 12x18, 32767: 8x5 |
| **`3313`** | `Scene 106` | 18 | 221 | Claude Kenni, Rena Lanford | 32767: 8x5, 32767: 16x13, 513: 12x14, 514: 8x18, 515: 28x18, 516: 12x16 |
| **`3314`** | `Scene 107` | 7 | 87 | - | 84: 20x30, 518: 16x15, 519: 18x17, 520: 14x23, 521: 14x18, 67: 24x46 |
| **`3315`** | `Scene 108` | 22 | 371 | - | 32767: 16x14, 32767: 12x17, 32767: 8x5, 32767: 16x13, 32767: 8x5, 32767: 8x5 |
| **`3316`** | `Scene 109` | 12 | 173 | - | 32767: 8x5, 32767: 16x14, 32767: 12x17, 32767: 8x5, 79: 24x46, 32767: 12x18 |
| **`3317`** | `Scene 110` | 8 | 91 | Claude Kenni | 84: 20x30, 32767: 16x13, 32767: 8x5, 32767: 12x18, 32767: 8x5, 20: 20x30 |
| **`3318`** | `Scene 111` | 10 | 85 | Claude Kenni | 32767: 12x17, 32767: 16x13, 32767: 12x18, 32767: 8x5, 32767: 8x5, 32767: 8x5 |
| **`3320`** | `Scene 113` | 2 | 28 | - | 32767: 16x13, 15: 20x43 |
| **`3321`** | `Scene 114` | 3 | 37 | - | 32767: 12x9, 32767: 16x13, 43: 24x44 |
| **`3322`** | `Scene 115` | 5 | 101 | - | 78: 24x45, 79: 24x46, 79: 24x46, 32767: 16x13, 67: 24x46 |
| **`3323`** | `Scene 116` | 2 | 42 | - | 16: 20x40, 31: 24x42 |
| **`3324`** | `Scene 117` | 11 | 131 | - | 84: 20x30, 32767: 8x5, 32767: 16x13, 72: 24x43, 32767: 16x14, 32767: 8x5 |
| **`3325`** | `Scene 118` | 18 | 160 | Claude Kenni, Rena Lanford, Celine Jules | 84: 20x30, 32767: 12x17, 32767: 8x5, 32767: 16x13, 32767: 16x14, 32767: 8x5 |
| **`3326`** | `Scene 119` | 16 | 104 | Claude Kenni, Rena Lanford | 32767: 8x5, 84: 20x30, 32767: 16x14, 32767: 16x13, 32767: 8x5, 32767: 12x18 |
| **`3327`** | `Scene 120` | 3 | 63 | - | 67: 24x46, 68: 24x45, 55: 24x44 |
| **`3328`** | `Scene 121` | 3 | 49 | - | 32767: 16x13, 81: 24x47, 37: 20x33 |
| **`3329`** | `Scene 122` | 9 | 189 | - | 30: 24x44, 31: 24x42, 49: 24x45, 33: 24x33, 32: 20x31, 82: 24x46 |
| **`3330`** | `Scene 123` | 3 | 63 | - | 13: 20x40, 12: 20x42, 14: 20x42 |
| **`3331`** | `Scene 124` | 25 | 358 | Celine Jules, Claude Kenni, Rena Lanford | 32767: 8x5, 32767: 8x5, 32767: 8x5, 32767: 12x18, 59: 24x39, 87: 24x44 |
| **`3332`** | `Scene 125` | 8 | 131 | Celine Jules | 32767: 8x5, 32767: 8x5, 32767: 16x13, 86: 24x43, 87: 24x44, 32767: 16x14 |
| **`3333`** | `Scene 126` | 16 | 278 | Celine Jules, Ashton Anchors | 32767: 8x5, 32767: 8x5, 64: 24x37, 32767: 16x13, 56: 24x44, 32767: 12x18 |
| **`3334`** | `Scene 127` | 1 | 7 | - | 32767: 8x5 |
| **`3335`** | `Scene 128` | 11 | 121 | - | 32767: 12x17, 32767: 8x5, 32767: 16x14, 63: 20x36, 68: 24x45, 50: 24x45 |

### 3.23 Mars Village & Heraldry Forest (Scene 129..153)
*Active Scenes: 22 | Total Sprite Frames: 1,728*

| Archive | Scene ID | Sections | Frames | Heroes Present | Other Selectors (ID: dims) |
| :---: | :---: | :---: | :---: | :--- | :--- |
| **`3336`** | `Scene 129` | 5 | 89 | - | 80: 24x45, 55: 24x44, 78: 24x45, 32767: 12x18, 39: 12x19 |
| **`3337`** | `Scene 130` | 10 | 59 | Rena Lanford, Dias Flac | 32767: 8x5, 32767: 16x14, 32767: 8x5, 32767: 8x5, 32767: 16x13 |
| **`3338`** | `Scene 131` | 12 | 172 | Dias Flac, Celine Jules | 32767: 12x17, 59: 24x39, 56: 24x44, 86: 24x43, 87: 24x44, 32767: 16x14 |
| **`3339`** | `Scene 132` | 12 | 73 | Claude Kenni | 32767: 12x17, 32767: 16x14, 32767: 12x9, 32767: 8x5, 32767: 16x13, 32767: 8x5 |
| **`3342`** | `Scene 135` | 13 | 169 | Celine Jules | 32767: 16x14, 32767: 8x5, 32767: 8x5, 32767: 16x13, 59: 24x39, 32767: 12x17 |
| **`3343`** | `Scene 136` | 5 | 79 | Celine Jules | 86: 24x43, 87: 24x44, 32767: 8x5, 32767: 8x5 |
| **`3344`** | `Scene 137` | 5 | 97 | Celine Jules | 86: 24x43, 87: 24x44, 32767: 12x17, 59: 24x39 |
| **`3345`** | `Scene 138` | 3 | 37 | - | 87: 24x44, 32767: 8x5, 32767: 16x13 |
| **`3346`** | `Scene 139` | 4 | 43 | Celine Jules | 155: 28x27, 32767: 8x5, 32767: 12x17 |
| **`3347`** | `Scene 140` | 3 | 35 | - | 32767: 16x13, 80: 24x45, 32767: 8x5 |
| **`3348`** | `Scene 141` | 10 | 86 | Ashton Anchors, Celine Jules, Opera Vectra | 32767: 8x5, 32767: 8x5, 32767: 8x5, 32767: 16x13, 79: 24x46, 32767: 8x5 |
| **`3349`** | `Scene 142` | 14 | 154 | Bowman Jean | 526: 14x24, 527: 10x17, 528: 10x22, 529: 16x27, 530: 12x20, 67: 24x46 |
| **`3350`** | `Scene 143` | 3 | 25 | - | 525: 10x16, 32767: 12x17, 32767: 8x5 |
| **`3351`** | `Scene 144` | 11 | 131 | Chisato Madison | 32767: 8x5, 32767: 8x5, 32767: 12x18, 31: 24x42, 79: 24x46, 46: 24x42 |
| **`3352`** | `Scene 145` | 3 | 36 | - | 32767: 8x5, 32767: 8x5, 128: 24x46 |
| **`3353`** | `Scene 146` | 10 | 131 | - | 109: 24x45, 128: 24x46, 32767: 12x17, 32767: 16x13, 32767: 8x5, 32767: 16x14 |
| **`3354`** | `Scene 147` | 3 | 63 | - | 13: 20x40, 12: 20x42, 14: 20x42 |
| **`3355`** | `Scene 148` | 5 | 94 | - | 78: 24x45, 79: 24x46, 128: 24x46, 32767: 12x18, 114: 24x45 |
| **`3356`** | `Scene 149` | 7 | 73 | - | 32767: 8x5, 32767: 16x13, 32767: 12x18, 17: 20x43, 32767: 16x14, 32767: 8x5 |
| **`3357`** | `Scene 150` | 1 | 21 | - | 114: 24x45 |
| **`3358`** | `Scene 151` | 4 | 40 | - | 32767: 8x5, 32767: 16x13, 32767: 12x18, 17: 20x43 |
| **`3359`** | `Scene 152` | 1 | 21 | - | 16: 20x40 |

### 3.25 Linga Academic City & Sanctuary (Scene 154..178)
*Active Scenes: 17 | Total Sprite Frames: 1,672*

| Archive | Scene ID | Sections | Frames | Heroes Present | Other Selectors (ID: dims) |
| :---: | :---: | :---: | :---: | :--- | :--- |
| **`3362`** | `Scene 155` | 7 | 131 | - | 56: 24x44, 42: 24x44, 40: 20x38, 78: 24x45, 32767: 12x18, 50: 24x45 |
| **`3363`** | `Scene 156` | 8 | 88 | - | 105: 24x43, 32767: 16x14, 32767: 8x5, 32767: 8x5, 32767: 8x5, 32767: 16x13 |
| **`3364`** | `Scene 157` | 16 | 151 | Bowman Jean, Claude Kenni, Ashton Anchors | 159: 20x29, 48: 24x34, 32767: 16x14, 32767: 8x5, 32767: 8x5, 32767: 12x17 |
| **`3365`** | `Scene 158` | 2 | 26 | - | 81: 24x47, 32767: 12x18 |
| **`3367`** | `Scene 160` | 2 | 26 | - | 128: 24x46, 32767: 12x18 |
| **`3370`** | `Scene 163` | 9 | 74 | Rena Lanford | 159: 20x29, 32767: 12x17, 109: 24x45, 109: 40x29, 10000: 8x5, 32767: 8x5 |
| **`3371`** | `Scene 164` | 2 | 26 | - | 128: 24x46, 32767: 12x18 |
| **`3373`** | `Scene 166` | 5 | 27 | Rena Lanford | 159: 20x29, 153: 20x29, 32767: 8x5, 32767: 12x17 |
| **`3374`** | `Scene 167` | 23 | 302 | Celine Jules, Claude Kenni, Rena Lanford | 32767: 16x13, 32767: 16x14, 32767: 8x5, 32767: 8x5, 32767: 12x17, 32767: 8x5 |
| **`3376`** | `Scene 169` | 21 | 319 | Leon D.S. Gehste, Dias Flac, Claude Kenni | 32767: 16x13, 32767: 16x14, 32767: 8x5, 32767: 8x5, 32767: 8x5, 531: 18x26 |
| **`3379`** | `Scene 172` | 5 | 41 | Claude Kenni | 32767: 16x14, 32767: 8x5 |
| **`3380`** | `Scene 173` | 6 | 95 | - | 32767: 16x13, 32767: 16x14, 13: 20x40, 12: 20x42, 14: 20x42, 23: 20x30 |
| **`3381`** | `Scene 174` | 18 | 263 | Opera Vectra | 32767: 16x13, 32767: 16x14, 78: 24x45, 32767: 8x5, 32767: 8x5, 32767: 8x5 |
| **`3382`** | `Scene 175` | 4 | 53 | - | 32767: 16x13, 32767: 16x14, 16: 20x40, 23: 20x30 |
| **`3383`** | `Scene 176` | 3 | 14 | Claude Kenni | 32767: 16x14, 32767: 8x5 |
| **`3384`** | `Scene 177` | 3 | 32 | - | 32767: 16x13, 32767: 16x14, 23: 20x30 |
| **`3385`** | `Scene 178` | 1 | 4 | - | 32767: 16x14 |

### 3.26 Kingdom of Lacour & Armory Tournaments (Scene 179..208)
*Active Scenes: 26 | Total Sprite Frames: 3,685*

| Archive | Scene ID | Sections | Frames | Heroes Present | Other Selectors (ID: dims) |
| :---: | :---: | :---: | :---: | :--- | :--- |
| **`3386`** | `Scene 179` | 17 | 91 | Rena Lanford, Claude Kenni, Celine Jules | 32767: 16x13, 32767: 16x14, 32767: 8x5, 32767: 8x5, 23: 20x30 |
| **`3388`** | `Scene 181` | 12 | 94 | Claude Kenni, Celine Jules | 32767: 16x13, 32767: 16x14, 32767: 8x5, 32767: 8x5, 23: 20x30, 71: 24x43 |
| **`3389`** | `Scene 182` | 2 | 13 | Claude Kenni | 32767: 16x14 |
| **`3390`** | `Scene 183` | 23 | 436 | Bowman Jean, Precis F. Neumann, Ashton Anchors, Celine Jules, Opera Vectra, Rena Lanford | 94: 24x25, 32767: 16x13, 32767: 12x17, 32767: 8x5, 32767: 16x14, 120: 20x38 |
| **`3391`** | `Scene 184` | 20 | 334 | Bowman Jean, Precis F. Neumann | 68: 24x45, 42: 24x44, 60: 24x39, 49: 24x45, 32767: 12x18, 118: 20x43 |
| **`3392`** | `Scene 185` | 6 | 68 | - | 32767: 16x14, 32767: 8x5, 32767: 8x5, 32767: 16x13, 49: 24x45, 50: 24x45 |
| **`3393`** | `Scene 186` | 16 | 114 | Bowman Jean, Claude Kenni, Rena Lanford, Celine Jules, Opera Vectra, Ashton Anchors, Precis F. Neumann | 32767: 16x14, 32767: 16x13, 32767: 12x18, 32767: 12x17, 10000: 24x21, 32767: 8x5 |
| **`3394`** | `Scene 187` | 3 | 35 | - | 32767: 16x13, 32767: 8x5, 80: 24x45 |
| **`3395`** | `Scene 188` | 1 | 21 | - | 16: 20x40 |
| **`3396`** | `Scene 189` | 19 | 167 | Claude Kenni, Bowman Jean, Rena Lanford | 32767: 8x5, 43: 24x44, 49: 24x45, 50: 24x45, 42: 24x44, 32767: 8x5 |
| **`3397`** | `Scene 190` | 3 | 63 | - | 13: 20x40, 12: 20x42, 14: 20x42 |
| **`3398`** | `Scene 191` | 23 | 364 | Bowman Jean, Leon D.S. Gehste, Chisato Madison | 10000: 20x20, 32767: 16x13, 32767: 16x14, 32767: 12x17, 32767: 12x18, 32767: 8x5 |
| **`3399`** | `Scene 192` | 9 | 77 | Rena Lanford | 118: 20x43, 32767: 8x5, 32767: 8x5, 32767: 8x5, 32767: 12x18, 32767: 12x9 |
| **`3400`** | `Scene 193` | 8 | 123 | Celine Jules, Opera Vectra, Ashton Anchors, Precis F. Neumann | 32767: 16x14, 118: 20x43, 32767: 16x13, 32767: 8x5 |
| **`3402`** | `Scene 195` | 20 | 111 | Claude Kenni, Rena Lanford, Celine Jules, Opera Vectra, Ashton Anchors, Bowman Jean | 118: 20x43, 32767: 16x14, 32767: 8x5, 32767: 16x13, 32767: 8x5, 32767: 8x5 |
| **`3403`** | `Scene 196` | 20 | 287 | Precis F. Neumann, Claude Kenni, Ashton Anchors, Chisato Madison | 32767: 16x14, 32767: 8x5, 32767: 12x18, 120: 20x38, 94: 24x25, 32767: 16x13 |
| **`3404`** | `Scene 197` | 13 | 166 | Claude Kenni, Precis F. Neumann | 32767: 8x5, 120: 20x38, 32767: 16x14, 32767: 8x5, 195: 20x32, 32767: 16x13 |
| **`3405`** | `Scene 198` | 2 | 28 | Precis F. Neumann | 32767: 16x13 |
| **`3406`** | `Scene 199` | 2 | 42 | - | 43: 24x44, 50: 24x45 |
| **`3409`** | `Scene 202` | 3 | 63 | - | 80: 24x45, 50: 24x45, 68: 24x45 |
| **`3410`** | `Scene 203` | 6 | 126 | - | 49: 24x45, 42: 24x44, 67: 24x46, 43: 24x44, 50: 24x45, 31: 24x42 |
| **`3411`** | `Scene 204` | 8 | 168 | - | 49: 24x45, 42: 24x44, 30: 24x44, 50: 24x45, 43: 24x44, 67: 24x46 |
| **`3412`** | `Scene 205` | 2 | 42 | - | 59: 24x39, 49: 24x45 |
| **`3413`** | `Scene 206` | 9 | 95 | Claude Kenni | 32767: 16x13, 15: 20x43, 32767: 12x17, 32767: 8x5, 32767: 16x14, 32767: 12x18 |
| **`3414`** | `Scene 207` | 25 | 386 | Precis F. Neumann, Celine Jules, Ashton Anchors, Opera Vectra, Rena Lanford, Claude Kenni, Bowman Jean, Leon D.S. Gehste | 32767: 8x5, 32767: 16x14, 32767: 16x13, 32767: 12x17, 32767: 8x5, 32767: 8x5 |
| **`3415`** | `Scene 208` | 16 | 171 | Bowman Jean, Claude Kenni, Precis F. Neumann | 32767: 16x14, 32767: 8x5, 32767: 8x5, 32767: 16x13, 32767: 12x17, 32767: 12x9 |

### 3.28 Hoffman Ruins & Lacour Frontline (Scene 209..238)
*Active Scenes: 27 | Total Sprite Frames: 4,159*

| Archive | Scene ID | Sections | Frames | Heroes Present | Other Selectors (ID: dims) |
| :---: | :---: | :---: | :---: | :--- | :--- |
| **`3416`** | `Scene 209` | 11 | 135 | Precis F. Neumann | 32767: 16x14, 32767: 16x13, 32767: 8x5, 120: 20x38, 32767: 12x17, 32767: 12x18 |
| **`3417`** | `Scene 210` | 14 | 171 | Claude Kenni | 32767: 16x13, 32767: 16x14, 32767: 8x5, 32767: 8x5, 32767: 8x5, 534: 26x51 |
| **`3418`** | `Scene 211` | 25 | 429 | Rena Lanford, Dias Flac | 32767: 8x5, 32767: 16x14, 23: 20x30, 32767: 8x5, 92: 24x45, 119: 24x46 |
| **`3419`** | `Scene 212` | 19 | 404 | - | 67: 24x46, 68: 24x45, 41: 24x43, 53: 24x39, 112: 20x40, 92: 24x45 |
| **`3420`** | `Scene 213` | 19 | 308 | Rena Lanford, Claude Kenni | 32767: 8x5, 32767: 8x5, 32767: 16x14, 67: 24x46, 111: 24x42, 79: 24x46 |
| **`3421`** | `Scene 214` | 8 | 106 | Celine Jules, Claude Kenni | 32767: 8x5, 32767: 8x5, 89: 24x47, 32767: 8x5, 32767: 16x13 |
| **`3422`** | `Scene 215` | 17 | 249 | - | 32767: 16x13, 32767: 8x5, 535: 22x24, 17: 20x43, 51: 20x37, 22: 20x31 |
| **`3423`** | `Scene 216` | 22 | 191 | Celine Jules, Precis F. Neumann, Rena Lanford, Claude Kenni | 533: 16x24, 68: 24x45, 79: 24x46, 37: 20x33, 32767: 12x18, 89: 24x47 |
| **`3425`** | `Scene 218` | 8 | 87 | Rena Lanford | 32767: 16x14, 32767: 8x5, 32767: 12x17, 32767: 8x5, 532: 16x14, 23: 20x30 |
| **`3426`** | `Scene 219` | 3 | 63 | - | 13: 20x40, 12: 20x42, 14: 20x42 |
| **`3427`** | `Scene 220` | 8 | 116 | - | 32767: 12x9, 32767: 16x13, 32767: 8x5, 32767: 8x5, 72: 24x43, 46: 24x42 |
| **`3428`** | `Scene 221` | 2 | 25 | - | 32767: 16x14, 17: 20x43 |
| **`3429`** | `Scene 222` | 1 | 7 | - | 32767: 8x5 |
| **`3430`** | `Scene 223` | 1 | 9 | - | 32767: 8x5 |
| **`3431`** | `Scene 224` | 10 | 57 | Precis F. Neumann, Ashton Anchors, Rena Lanford | 32767: 16x14, 32767: 8x5, 32767: 8x5, 32767: 8x5, 32767: 16x13 |
| **`3432`** | `Scene 225` | 25 | 337 | Dias Flac, Rena Lanford, Bowman Jean | 32767: 16x14, 32767: 8x5, 32767: 8x5, 23: 20x30, 32767: 12x17, 32767: 16x13 |
| **`3433`** | `Scene 226` | 2 | 42 | - | 36: 24x34, 31: 24x42 |
| **`3435`** | `Scene 228` | 11 | 88 | Rena Lanford, Claude Kenni | 32767: 16x14, 23: 20x30, 32767: 16x13, 32767: 8x5, 32767: 8x5, 32767: 8x5 |
| **`3436`** | `Scene 229` | 37 | 334 | Claude Kenni, Leon D.S. Gehste, Rena Lanford, Celine Jules, Bowman Jean, Dias Flac, Precis F. Neumann, Ashton Anchors, Opera Vectra, Ernest Ravine | 32767: 12x17, 32767: 8x5, 32767: 8x5, 32767: 16x13, 10000: 24x13, 172: 92x82 |
| **`3437`** | `Scene 230` | 11 | 110 | Leon D.S. Gehste, Claude Kenni | 32767: 8x5, 32767: 12x17 |
| **`3438`** | `Scene 231` | 2 | 28 | - | 32767: 16x13, 92: 24x45 |
| **`3439`** | `Scene 232` | 35 | 380 | Celine Jules, Bowman Jean, Dias Flac, Precis F. Neumann, Ashton Anchors, Leon D.S. Gehste, Opera Vectra, Ernest Ravine, Rena Lanford, Claude Kenni | 32767: 8x5, 32767: 16x14, 32767: 12x17, 32767: 8x5, 32767: 8x5, 32767: 8x5 |
| **`3440`** | `Scene 233` | 5 | 50 | Claude Kenni | 32767: 12x17, 32767: 8x5, 32767: 16x13, 67: 24x46 |
| **`3441`** | `Scene 234` | 11 | 126 | Leon D.S. Gehste, Rena Lanford, Claude Kenni | 32767: 8x5, 32767: 16x14, 32767: 8x5, 32767: 12x18, 40: 20x38, 12: 20x42 |
| **`3442`** | `Scene 235` | 13 | 170 | Rena Lanford, Claude Kenni, Opera Vectra | 32767: 8x5, 32767: 16x13, 28: 24x44, 17: 20x43, 24: 24x39, 57: 24x39 |
| **`3444`** | `Scene 237` | 6 | 109 | Chisato Madison | 32767: 16x14, 32767: 16x13, 32767: 8x5, 39: 12x19, 199: 56x47 |
| **`3445`** | `Scene 238` | 2 | 28 | - | 28: 24x44, 32767: 8x5 |

### 3.29 Eluria Tower & Calnus Transport (Scene 239..268)
*Active Scenes: 28 | Total Sprite Frames: 2,163*

| Archive | Scene ID | Sections | Frames | Heroes Present | Other Selectors (ID: dims) |
| :---: | :---: | :---: | :---: | :--- | :--- |
| **`3446`** | `Scene 239` | 12 | 159 | - | 32767: 8x5, 32767: 16x13, 29: 24x45, 58: 24x39, 57: 24x39, 22: 20x31 |
| **`3447`** | `Scene 240` | 5 | 105 | - | 112: 20x40, 28: 24x44, 58: 24x39, 22: 20x31, 57: 24x39 |
| **`3449`** | `Scene 242` | 11 | 168 | Chisato Madison | 32767: 12x17, 32767: 8x5, 32767: 8x5, 32767: 8x5, 32767: 8x5, 40: 20x38 |
| **`3450`** | `Scene 243` | 2 | 30 | - | 32767: 12x9, 57: 24x39 |
| **`3451`** | `Scene 244` | 8 | 54 | Rena Lanford | 32767: 8x5, 32767: 8x5, 10000: 24x11, 32767: 8x5, 10000: 28x22, 32767: 8x5 |
| **`3452`** | `Scene 245` | 6 | 98 | - | 32767: 8x5, 32767: 8x5, 40: 20x38, 57: 24x39, 28: 24x44, 29: 24x45 |
| **`3453`** | `Scene 246` | 4 | 53 | - | 121: 24x44, 32767: 8x5, 32767: 16x14, 58: 24x39 |
| **`3454`** | `Scene 247` | 6 | 78 | - | 121: 24x44, 32767: 12x17, 32767: 8x5, 32767: 8x5, 32767: 16x14, 167: 24x41 |
| **`3455`** | `Scene 248` | 2 | 31 | - | 10000: 8x5, 121: 24x44 |
| **`3456`** | `Scene 249` | 2 | 25 | - | 32767: 16x14, 17: 20x43 |
| **`3457`** | `Scene 250` | 13 | 210 | Opera Vectra | 32767: 12x9, 78: 24x45, 57: 24x39, 32767: 8x5, 32767: 12x18, 32767: 16x13 |
| **`3458`** | `Scene 251` | 10 | 84 | Opera Vectra, Claude Kenni | 32767: 8x5, 32767: 16x14, 32767: 12x18, 32767: 16x13, 32767: 12x17, 78: 24x45 |
| **`3460`** | `Scene 253` | 5 | 26 | Rena Lanford, Claude Kenni | 32767: 16x13, 32767: 8x5 |
| **`3461`** | `Scene 254` | 1 | 7 | - | 32767: 8x5 |
| **`3462`** | `Scene 255` | 5 | 28 | Rena Lanford | 32767: 16x14, 32767: 8x5, 32767: 12x17 |
| **`3463`** | `Scene 256` | 3 | 24 | - | 32767: 8x5, 32767: 8x5, 32767: 8x5 |
| **`3464`** | `Scene 257` | 10 | 124 | - | 32767: 8x5, 81: 24x47, 57: 24x39, 27: 24x38, 25: 24x39, 32767: 8x5 |
| **`3465`** | `Scene 258` | 2 | 42 | - | 12: 20x42, 28: 24x44 |
| **`3466`** | `Scene 259` | 3 | 33 | - | 32767: 16x13, 32767: 12x18, 15: 20x43 |
| **`3467`** | `Scene 260` | 12 | 183 | Chisato Madison | 32767: 16x14, 32767: 16x13, 32767: 8x5, 29: 24x45, 28: 24x44, 25: 24x39 |
| **`3468`** | `Scene 261` | 14 | 82 | Precis F. Neumann, Claude Kenni, Rena Lanford | 94: 24x25, 32767: 16x13, 32767: 8x5, 32767: 8x5, 32767: 8x5, 32767: 12x18 |
| **`3469`** | `Scene 262` | 9 | 52 | Claude Kenni, Opera Vectra, Rena Lanford | 10000: 16x19, 137: 24x45, 32767: 16x13 |
| **`3470`** | `Scene 263` | 10 | 89 | Claude Kenni, Rena Lanford | 68: 24x45, 32767: 8x5, 32767: 12x17, 42: 24x44, 32767: 16x13 |
| **`3471`** | `Scene 264` | 7 | 104 | - | 32767: 16x14, 32767: 8x5, 32767: 12x9, 42: 24x44, 29: 24x45, 28: 24x44 |
| **`3472`** | `Scene 265` | 4 | 72 | - | 32767: 8x5, 16: 20x40, 15: 20x43, 39: 12x19 |
| **`3473`** | `Scene 266` | 12 | 119 | Claude Kenni, Rena Lanford | 32767: 16x13, 32767: 12x18, 32767: 8x5, 42: 24x44, 58: 24x39, 28: 24x44 |
| **`3474`** | `Scene 267` | 1 | 10 | - | 10000: 8x5 |
| **`3475`** | `Scene 268` | 9 | 73 | Claude Kenni, Chisato Madison | 32767: 12x17, 32767: 8x5, 32767: 8x5, 32767: 8x5, 32767: 16x14, 16: 20x40 |

### 3.31 Central City & Energy Nede Approach (Scene 269..333)
*Active Scenes: 59 | Total Sprite Frames: 6,423*

| Archive | Scene ID | Sections | Frames | Heroes Present | Other Selectors (ID: dims) |
| :---: | :---: | :---: | :---: | :--- | :--- |
| **`3476`** | `Scene 269` | 11 | 127 | Ashton Anchors, Claude Kenni, Rena Lanford | 170: 20x45, 68: 24x45, 169: 180x142, 32767: 16x13, 32767: 16x14, 169: 64x119 |
| **`3477`** | `Scene 270` | 5 | 65 | Ashton Anchors | 68: 24x45, 169: 64x119, 169: 32x31 |
| **`3478`** | `Scene 271` | 11 | 144 | Chisato Madison | 32767: 8x5, 32767: 16x13, 170: 20x45, 68: 24x45, 42: 24x44, 28: 24x44 |
| **`3479`** | `Scene 272` | 5 | 61 | - | 170: 20x45, 68: 24x45, 32767: 16x14, 32767: 8x5, 32767: 8x5 |
| **`3480`** | `Scene 273` | 2 | 28 | - | 57: 24x39, 32767: 16x13 |
| **`3481`** | `Scene 274` | 6 | 68 | - | 10000: 4x2, 32767: 8x5, 32767: 8x5, 32767: 12x17, 32767: 8x5, 71: 24x43 |
| **`3482`** | `Scene 275` | 3 | 51 | - | 32767: 8x5, 58: 24x39, 26: 24x39 |
| **`3483`** | `Scene 276` | 3 | 49 | - | 32767: 8x5, 17: 20x43, 29: 24x45 |
| **`3484`** | `Scene 277` | 8 | 66 | Noel Chandler | 32767: 12x17, 32767: 8x5, 32767: 8x5, 32767: 8x5, 32767: 16x14, 160: 24x31 |
| **`3485`** | `Scene 278` | 7 | 51 | Claude Kenni, Rena Lanford | 10000: 8x5, 32767: 8x5, 67: 24x46 |
| **`3486`** | `Scene 279` | 8 | 96 | Celine Jules | 32767: 16x13, 32767: 8x5, 32767: 12x17, 32767: 12x18, 29: 24x45, 112: 20x40 |
| **`3487`** | `Scene 280` | 21 | 338 | - | 32767: 12x18, 32767: 8x5, 32767: 16x13, 32767: 12x9, 32767: 8x5, 32767: 12x17 |
| **`3488`** | `Scene 281` | 30 | 487 | Celine Jules, Rena Lanford, Claude Kenni | 32767: 12x17, 29: 24x45, 90: 24x42, 28: 24x44, 23: 20x30, 27: 24x38 |
| **`3489`** | `Scene 282` | 2 | 42 | - | 24: 24x39, 26: 24x39 |
| **`3490`** | `Scene 283` | 6 | 88 | - | 32767: 8x5, 32767: 16x13, 32767: 12x9, 57: 24x39, 58: 24x39, 16: 20x40 |
| **`3492`** | `Scene 285` | 6 | 97 | - | 32767: 16x13, 28: 24x44, 167: 24x41, 167: 44x19, 29: 24x45, 57: 24x39 |
| **`3494`** | `Scene 287` | 2 | 42 | - | 58: 24x39, 112: 20x40 |
| **`3495`** | `Scene 288` | 14 | 219 | Leon D.S. Gehste | 24: 24x39, 32767: 12x9, 32767: 8x5, 32767: 8x5, 32767: 8x5, 129: 24x43 |
| **`3496`** | `Scene 289` | 10 | 65 | Rena Lanford, Claude Kenni | 32767: 16x13, 32767: 8x5, 32767: 8x5, 32767: 12x18, 32767: 8x5 |
| **`3497`** | `Scene 290` | 6 | 98 | - | 32767: 8x5, 32767: 12x18, 57: 24x39, 111: 24x42, 58: 24x39, 30: 24x44 |
| **`3498`** | `Scene 291` | 7 | 96 | - | 32767: 12x9, 32767: 8x5, 32767: 8x5, 32767: 16x13, 16: 20x40, 28: 24x44 |
| **`3499`** | `Scene 292` | 8 | 154 | - | 32767: 8x5, 28: 24x44, 29: 24x45, 57: 24x39, 58: 24x39, 21: 20x30 |
| **`3500`** | `Scene 293` | 15 | 173 | Claude Kenni, Rena Lanford | 32767: 16x14, 32767: 8x5, 32767: 16x13, 32767: 8x5, 32767: 8x5, 71: 24x43 |
| **`3501`** | `Scene 294` | 7 | 133 | - | 32767: 8x5, 32767: 16x13, 32767: 12x9, 111: 24x42, 112: 20x40, 15: 20x43 |
| **`3502`** | `Scene 295` | 11 | 97 | Claude Kenni, Rena Lanford | 199: 72x37, 32767: 8x5, 32767: 8x5, 32767: 16x13, 199: 56x47, 32767: 8x5 |
| **`3503`** | `Scene 296` | 10 | 210 | - | 28: 24x44, 57: 24x39, 29: 24x45, 67: 24x46, 30: 24x44, 21: 20x30 |
| **`3504`** | `Scene 297` | 5 | 96 | - | 32766: 16x36, 58: 24x39, 88: 24x47, 29: 24x45, 89: 24x47 |
| **`3505`** | `Scene 298` | 9 | 127 | Celine Jules, Rena Lanford | 32767: 12x17, 32767: 16x13, 32767: 8x5, 32767: 12x9, 67: 24x46, 28: 24x44 |
| **`3506`** | `Scene 299` | 7 | 109 | - | 32767: 12x9, 32767: 8x5, 111: 24x42, 28: 24x44, 20: 20x30, 22: 20x31 |
| **`3507`** | `Scene 300` | 3 | 49 | - | 20: 20x30, 22: 20x31, 32767: 16x13 |
| **`3508`** | `Scene 301` | 4 | 66 | - | 146: 24x46, 10000: 24x39, 10000: 16x14, 10000: 20x20 |
| **`3509`** | `Scene 302` | 5 | 92 | - | 28: 24x44, 198: 24x41, 29: 24x45, 32767: 16x13, 32767: 12x18 |
| **`3510`** | `Scene 303` | 14 | 225 | Claude Kenni, Rena Lanford | 32767: 16x14, 28: 24x44, 57: 24x39, 29: 24x45, 67: 24x46, 30: 24x44 |
| **`3511`** | `Scene 304` | 17 | 208 | Ashton Anchors, Precis F. Neumann | 20: 20x30, 22: 20x31, 32767: 16x13, 94: 24x25, 32767: 8x5, 32767: 8x5 |
| **`3512`** | `Scene 305` | 29 | 460 | - | 29: 24x45, 147: 32x52, 146: 24x46, 32766: 16x36, 32767: 12x17, 147: 28x55 |
| **`3513`** | `Scene 306` | 12 | 176 | - | 146: 24x46, 146: 48x24, 32767: 12x17, 147: 28x47, 121: 24x44, 57: 24x39 |
| **`3514`** | `Scene 307` | 5 | 42 | Rena Lanford | 28: 24x44, 32767: 8x5, 32767: 16x14, 32767: 16x13 |
| **`3515`** | `Scene 308` | 2 | 28 | - | 121: 24x44, 32767: 8x5 |
| **`3516`** | `Scene 309` | 21 | 138 | Claude Kenni, Ashton Anchors, Rena Lanford | 32767: 8x5, 32767: 8x5, 32767: 12x18, 28: 24x44, 57: 24x39, 129: 24x43 |
| **`3517`** | `Scene 310` | 4 | 54 | - | 27: 24x38, 196: 24x44, 32767: 8x5, 32767: 12x18 |
| **`3518`** | `Scene 311` | 4 | 84 | - | 25: 24x39, 29: 24x45, 58: 24x39, 27: 24x38 |
| **`3519`** | `Scene 312` | 10 | 109 | Noel Chandler | 32767: 16x13, 27: 24x38, 28: 24x44, 32767: 12x18, 57: 24x39, 32767: 8x5 |
| **`3520`** | `Scene 313` | 4 | 81 | - | 10000: 8x5, 10000: 20x20, 121: 24x44, 32767: 8x5 |
| **`3521`** | `Scene 314` | 7 | 93 | - | 146: 24x46, 32767: 16x14, 121: 24x44, 32767: 12x17, 32767: 8x5, 28: 24x44 |
| **`3522`** | `Scene 315` | 8 | 91 | - | 146: 24x46, 121: 24x44, 32767: 8x5, 32767: 8x5, 32767: 12x17, 32767: 16x14 |
| **`3523`** | `Scene 316` | 4 | 68 | - | 32767: 12x18, 12: 20x42, 13: 20x40, 14: 20x42 |
| **`3524`** | `Scene 317` | 6 | 97 | - | 10000: 8x7, 25: 24x39, 57: 24x39, 28: 24x44, 21: 20x30, 32767: 8x5 |
| **`3525`** | `Scene 318` | 5 | 71 | Precis F. Neumann | 32767: 12x9, 32767: 8x5, 32767: 8x5, 10000: 8x7 |
| **`3527`** | `Scene 320` | 7 | 37 | Precis F. Neumann, Rena Lanford | 32767: 16x14, 32767: 16x13, 32767: 8x5, 32767: 8x5, 32767: 8x5 |
| **`3530`** | `Scene 323` | 9 | 117 | Precis F. Neumann | 32767: 8x5, 32767: 12x9, 32767: 8x5, 58: 24x39, 32767: 16x14, 32767: 8x5 |
| **`3531`** | `Scene 324` | 5 | 50 | - | 28: 24x44, 32767: 8x5, 32767: 8x5, 32767: 8x5, 32767: 16x13 |
| **`3532`** | `Scene 325` | 1 | 21 | - | 57: 24x39 |
| **`3533`** | `Scene 326` | 7 | 119 | - | 113: 24x38, 28: 24x44, 29: 24x45, 32767: 8x5, 57: 24x39, 58: 24x39 |
| **`3534`** | `Scene 327` | 7 | 105 | - | 32767: 12x18, 113: 24x38, 28: 24x44, 29: 24x45, 58: 24x39, 32767: 8x5 |
| **`3536`** | `Scene 329` | 1 | 21 | - | 24: 24x39 |
| **`3537`** | `Scene 330` | 7 | 68 | - | 12: 20x42, 32767: 8x5, 32767: 8x5, 32767: 8x5, 32767: 16x14, 32767: 8x5 |
| **`3538`** | `Scene 331` | 4 | 58 | - | 32767: 12x9, 32767: 16x13, 26: 24x39, 28: 24x44 |
| **`3539`** | `Scene 332` | 8 | 82 | - | 32767: 8x5, 32767: 12x17, 32767: 16x13, 32767: 8x5, 32767: 16x14, 150: 24x21 |
| **`3540`** | `Scene 333` | 3 | 36 | - | 32767: 8x5, 32767: 8x5, 237: 28x47 |

### 3.34 North City, Giveaway & Library (Scene 334..413)
*Active Scenes: 41 | Total Sprite Frames: 1,552*

| Archive | Scene ID | Sections | Frames | Heroes Present | Other Selectors (ID: dims) |
| :---: | :---: | :---: | :---: | :--- | :--- |
| **`3541`** | `Scene 334` | 2 | 28 | - | 32767: 16x13, 17: 20x43 |
| **`3543`** | `Scene 336` | 4 | 43 | - | 10000: 8x7, 58: 24x39, 32767: 8x5, 32767: 8x5 |
| **`3544`** | `Scene 337` | 2 | 25 | - | 58: 24x39, 32767: 16x14 |
| **`3545`** | `Scene 338` | 8 | 75 | - | 58: 24x39, 32767: 16x14, 32767: 8x5, 32767: 8x5, 32767: 12x17, 32767: 16x13 |
| **`3546`** | `Scene 339` | 5 | 105 | - | 58: 24x39, 28: 24x44, 57: 24x39, 24: 24x39, 21: 20x30 |
| **`3549`** | `Scene 342` | 1 | 12 | - | 32766: 16x36 |
| **`3556`** | `Scene 349` | 3 | 21 | - | 32767: 12x18, 32767: 16x13, 32767: 8x5 |
| **`3558`** | `Scene 351` | 1 | 3 | - | 156: 24x21 |
| **`3562`** | `Scene 355` | 3 | 29 | - | 32767: 12x18, 156: 24x21, 89: 24x47 |
| **`3565`** | `Scene 358` | 1 | 3 | - | 156: 24x21 |
| **`3566`** | `Scene 359` | 5 | 39 | - | 10000: 8x5, 235: 140x56, 32767: 8x5, 32767: 12x17, 32767: 8x5 |
| **`3567`** | `Scene 360` | 1 | 12 | - | 32766: 16x36 |
| **`3574`** | `Scene 367` | 1 | 3 | - | 161: 28x28 |
| **`3578`** | `Scene 371` | 1 | 3 | - | 156: 24x21 |
| **`3579`** | `Scene 372` | 4 | 64 | Celine Jules | 32767: 8x5, 171: 48x56, 32767: 12x17 |
| **`3580`** | `Scene 373` | 3 | 18 | - | 32767: 8x5, 32767: 8x5, 156: 24x21 |
| **`3581`** | `Scene 374` | 14 | 154 | Opera Vectra, Claude Kenni | 32767: 12x18, 32767: 8x5, 32767: 12x17, 32767: 16x13, 32767: 16x14, 32767: 8x5 |
| **`3582`** | `Scene 375` | 1 | 3 | - | 157: 28x27 |
| **`3583`** | `Scene 376` | 2 | 6 | - | 152: 24x31, 158: 24x31 |
| **`3587`** | `Scene 380` | 8 | 37 | Claude Kenni, Rena Lanford | 32767: 16x13, 204: 40x48, 32767: 12x17, 32767: 8x5, 156: 24x21, 99: 16x16 |
| **`3588`** | `Scene 381` | 2 | 14 | Ashton Anchors | 10000: 32x30 |
| **`3591`** | `Scene 384` | 2 | 14 | Claude Kenni, Rena Lanford | - |
| **`3592`** | `Scene 385` | 9 | 86 | Ashton Anchors | 133: 104x156, 32767: 12x17, 32767: 8x5, 32767: 8x5, 10000: 8x5, 32767: 16x13 |
| **`3594`** | `Scene 387` | 1 | 3 | - | 156: 24x21 |
| **`3604`** | `Scene 397` | 1 | 12 | - | 32766: 16x36 |
| **`3605`** | `Scene 398` | 17 | 266 | Rena Lanford, Celine Jules, Bowman Jean, Precis F. Neumann, Dias Flac, Leon D.S. Gehste, Ashton Anchors, Opera Vectra, Ernest Ravine, Noel Chandler, Chisato Madison | 121: 24x44, 32767: 16x14, 32767: 8x5, 32767: 12x17 |
| **`3606`** | `Scene 399` | 8 | 102 | - | 29: 24x45, 196: 24x44, 32767: 16x13, 32767: 8x5, 32767: 12x17, 174: 24x30 |
| **`3607`** | `Scene 400` | 7 | 56 | Claude Kenni | 10000: 8x5, 121: 24x44, 32767: 8x5, 32767: 8x5, 32767: 16x14 |
| **`3608`** | `Scene 401` | 8 | 29 | Rena Lanford, Claude Kenni | 32767: 8x5 |
| **`3609`** | `Scene 402` | 4 | 16 | - | 32767: 16x14, 156: 24x21, 152: 24x31, 10000: 32x30 |
| **`3610`** | `Scene 403` | 3 | 12 | - | 156: 24x21, 155: 28x27, 10000: 32x30 |
| **`3611`** | `Scene 404` | 3 | 30 | - | 156: 24x21, 10000: 32x30, 67: 24x46 |
| **`3612`** | `Scene 405` | 1 | 6 | - | 10000: 32x30 |
| **`3613`** | `Scene 406` | 1 | 6 | - | 10000: 32x30 |
| **`3614`** | `Scene 407` | 10 | 102 | Claude Kenni, Dias Flac, Ashton Anchors | 10000: 32x30, 23: 20x30, 128: 24x46, 32767: 16x13, 32767: 8x5 |
| **`3615`** | `Scene 408` | 3 | 30 | - | 157: 28x27, 10000: 32x30, 50: 24x45 |
| **`3616`** | `Scene 409` | 3 | 21 | - | 32766: 16x36, 156: 24x21, 10000: 32x30 |
| **`3617`** | `Scene 410` | 1 | 6 | - | 10000: 32x30 |
| **`3618`** | `Scene 411` | 1 | 6 | - | 10000: 32x30 |
| **`3619`** | `Scene 412` | 5 | 49 | - | 67: 24x46, 32767: 8x5, 32767: 12x17, 219: 100x36, 156: 24x21 |
| **`3620`** | `Scene 413` | 1 | 3 | - | 156: 24x21 |

### 3.37 Armlock, Fun City & Nedian Enclaves (Scene 414..493)
*Active Scenes: 71 | Total Sprite Frames: 7,683*

| Archive | Scene ID | Sections | Frames | Heroes Present | Other Selectors (ID: dims) |
| :---: | :---: | :---: | :---: | :--- | :--- |
| **`3621`** | `Scene 414` | 1 | 3 | - | 154: 24x31 |
| **`3622`** | `Scene 415` | 9 | 96 | Chisato Madison | 32767: 16x13, 10000: 12x5, 32767: 8x5, 156: 24x21 |
| **`3623`** | `Scene 416` | 2 | 6 | - | 156: 24x21, 151: 28x28 |
| **`3624`** | `Scene 417` | 14 | 132 | Noel Chandler, Claude Kenni, Rena Lanford | 206: 56x61, 32767: 12x17, 169: 176x118, 169: 32x31, 32767: 8x5, 32767: 8x5 |
| **`3625`** | `Scene 418` | 3 | 18 | - | 150: 24x21, 156: 24x21, 32766: 16x36 |
| **`3626`** | `Scene 419` | 1 | 4 | - | 32767: 16x14 |
| **`3627`** | `Scene 420` | 14 | 294 | - | 80: 24x45, 92: 24x45, 89: 24x47, 90: 24x42, 46: 24x42, 23: 20x30 |
| **`3628`** | `Scene 421` | 8 | 123 | Rena Lanford | 32767: 16x14, 32767: 16x13, 92: 24x45, 31: 24x42, 68: 24x45, 90: 24x42 |
| **`3629`** | `Scene 422` | 25 | 472 | Leon D.S. Gehste, Dias Flac | 32767: 8x5, 32767: 12x17, 32767: 8x5, 32767: 16x14, 43: 24x44, 44: 24x42 |
| **`3630`** | `Scene 423` | 2 | 42 | - | 20: 20x30, 21: 20x30 |
| **`3632`** | `Scene 425` | 4 | 84 | - | 88: 24x47, 80: 24x45, 89: 24x47, 90: 24x42 |
| **`3633`** | `Scene 426` | 1 | 21 | - | 21: 20x30 |
| **`3634`** | `Scene 427` | 8 | 168 | - | 91: 24x42, 22: 20x31, 90: 24x42, 31: 24x42, 88: 24x47, 89: 24x47 |
| **`3636`** | `Scene 429` | 4 | 66 | - | 156: 24x21, 89: 24x47, 15: 20x43, 114: 24x45 |
| **`3637`** | `Scene 430` | 5 | 87 | - | 156: 24x21, 91: 24x42, 95: 24x44, 31: 24x42, 36: 24x34 |
| **`3638`** | `Scene 431` | 5 | 77 | - | 32767: 8x5, 92: 24x45, 89: 24x47, 32767: 12x18, 88: 24x47 |
| **`3639`** | `Scene 432` | 4 | 68 | - | 81: 24x47, 68: 24x45, 32767: 12x18, 31: 24x42 |
| **`3640`** | `Scene 433` | 1 | 21 | - | 89: 24x47 |
| **`3641`** | `Scene 434` | 5 | 66 | Dias Flac, Rena Lanford | 55: 24x44, 88: 24x47 |
| **`3642`** | `Scene 435` | 8 | 168 | - | 67: 24x46, 43: 24x44, 96: 24x38, 49: 24x45, 50: 24x45, 89: 24x47 |
| **`3644`** | `Scene 437` | 23 | 229 | Claude Kenni, Rena Lanford, Leon D.S. Gehste, Celine Jules, Chisato Madison | 32767: 16x14, 32767: 8x5, 32767: 16x13, 32767: 12x18, 32767: 12x17, 32767: 8x5 |
| **`3645`** | `Scene 438` | 6 | 87 | - | 32766: 16x36, 88: 24x47, 89: 24x47, 148: 24x47, 32767: 8x5, 32767: 12x18 |
| **`3646`** | `Scene 439` | 8 | 118 | Dias Flac | 32767: 8x5, 32767: 8x5, 32767: 16x13, 32767: 12x17, 89: 24x47, 88: 24x47 |
| **`3648`** | `Scene 441` | 3 | 47 | - | 148: 24x47, 32767: 12x18, 149: 24x47 |
| **`3649`** | `Scene 442` | 9 | 96 | - | 88: 24x47, 32767: 16x14, 32767: 16x13, 32767: 12x17, 116: 20x42, 113: 24x38 |
| **`3650`** | `Scene 443` | 10 | 131 | Dias Flac | 32767: 12x17, 32767: 16x14, 32767: 8x5, 32767: 8x5, 32767: 8x5, 32767: 16x13 |
| **`3651`** | `Scene 444` | 21 | 330 | Dias Flac, Rena Lanford, Leon D.S. Gehste | 32767: 8x5, 32767: 16x13, 32767: 8x5, 32767: 12x17, 32767: 8x5, 116: 20x42 |
| **`3652`** | `Scene 445` | 7 | 133 | Dias Flac | 32767: 16x13, 15: 20x43, 89: 24x47, 149: 24x47, 88: 24x47, 92: 24x45 |
| **`3653`** | `Scene 446` | 3 | 49 | - | 32767: 16x13, 89: 24x47, 92: 24x45 |
| **`3654`** | `Scene 447` | 19 | 282 | Celine Jules, Ashton Anchors, Opera Vectra, Precis F. Neumann, Ernest Ravine, Bowman Jean, Rena Lanford | 32767: 16x14, 32767: 8x5, 32767: 12x17, 32767: 16x13, 32767: 8x5, 32767: 8x5 |
| **`3655`** | `Scene 448` | 18 | 293 | Leon D.S. Gehste, Dias Flac | 180: 56x55, 32767: 16x13, 32767: 12x17, 32767: 8x5, 32767: 16x14, 32767: 8x5 |
| **`3656`** | `Scene 449` | 3 | 13 | - | 32767: 8x5, 156: 24x21, 155: 28x27 |
| **`3657`** | `Scene 450` | 1 | 3 | - | 156: 24x21 |
| **`3658`** | `Scene 451` | 2 | 6 | - | 156: 24x21, 155: 28x27 |
| **`3659`** | `Scene 452` | 3 | 9 | - | 156: 24x21, 157: 28x27, 152: 24x31 |
| **`3661`** | `Scene 454` | 1 | 12 | - | 32766: 16x36 |
| **`3662`** | `Scene 455` | 1 | 12 | - | 32766: 16x36 |
| **`3663`** | `Scene 456` | 6 | 36 | - | 178: 28x44, 178: 28x44, 32767: 12x17, 32767: 8x5, 123: 48x50, 97: 16x11 |
| **`3664`** | `Scene 457` | 5 | 28 | - | 178: 28x44, 178: 28x44, 32767: 12x17, 32767: 8x5, 97: 16x11 |
| **`3665`** | `Scene 458` | 4 | 22 | - | 32767: 8x5, 32767: 16x14, 122: 80x43, 97: 16x11 |
| **`3666`** | `Scene 459` | 7 | 39 | - | 178: 28x44, 178: 28x44, 32767: 12x17, 32767: 8x5, 156: 24x21, 123: 48x50 |
| **`3667`** | `Scene 460` | 8 | 119 | Dias Flac, Opera Vectra | 156: 24x21, 122: 80x43, 32767: 8x5, 32767: 16x14, 32767: 12x17, 172: 92x82 |
| **`3668`** | `Scene 461` | 3 | 14 | - | 156: 24x21, 122: 80x43, 97: 16x11 |
| **`3669`** | `Scene 462` | 13 | 128 | Celine Jules, Dias Flac | 56: 24x44, 32767: 16x14, 32767: 12x17, 32767: 8x5, 191: 92x29, 32767: 8x5 |
| **`3670`** | `Scene 463` | 16 | 215 | Leon D.S. Gehste, Noel Chandler | 32767: 8x5, 32767: 16x14, 32767: 8x5, 32767: 12x17, 177: 28x49, 73: 24x32 |
| **`3671`** | `Scene 464` | 3 | 23 | - | 32766: 16x36, 122: 80x43, 97: 16x11 |
| **`3672`** | `Scene 465` | 3 | 20 | - | 32766: 16x36, 153: 20x29, 97: 16x11 |
| **`3673`** | `Scene 466` | 2 | 13 | - | 123: 48x50, 97: 16x11 |
| **`3674`** | `Scene 467` | 19 | 380 | - | 32767: 8x5, 32767: 16x14, 67: 24x46, 55: 24x44, 88: 24x47, 23: 20x30 |
| **`3675`** | `Scene 468` | 25 | 370 | Rena Lanford, Claude Kenni, Dias Flac | 32767: 16x14, 32767: 8x5, 32767: 12x17, 32767: 12x18, 32767: 16x13, 32767: 8x5 |
| **`3676`** | `Scene 469` | 26 | 363 | Claude Kenni, Dias Flac, Rena Lanford, Celine Jules, Ashton Anchors, Precis F. Neumann | 32767: 16x14, 32767: 8x5, 32767: 8x5, 32767: 12x17, 32767: 8x5, 88: 24x47 |
| **`3677`** | `Scene 470` | 6 | 126 | - | 88: 24x47, 67: 24x46, 68: 24x45, 30: 24x44, 41: 24x43, 92: 24x45 |
| **`3678`** | `Scene 471` | 8 | 156 | - | 32767: 12x9, 51: 20x37, 59: 24x39, 112: 20x40, 31: 24x42, 71: 24x43 |
| **`3679`** | `Scene 472` | 6 | 37 | Dias Flac | 183: 28x49, 177: 28x49, 189: 36x47, 190: 64x67, 185: 60x58 |
| **`3680`** | `Scene 473` | 1 | 21 | Dias Flac | - |
| **`3681`** | `Scene 474` | 41 | 632 | Rena Lanford, Claude Kenni, Celine Jules, Ashton Anchors, Precis F. Neumann, Leon D.S. Gehste | 32767: 12x9, 32767: 8x5, 32767: 16x14, 89: 24x47, 32767: 8x5, 32767: 12x17 |
| **`3682`** | `Scene 475` | 8 | 156 | - | 32767: 8x5, 40: 20x38, 31: 24x42, 111: 24x42, 21: 20x30, 55: 24x44 |
| **`3683`** | `Scene 476` | 7 | 114 | Claude Kenni, Dias Flac | 32767: 16x13, 89: 24x47, 88: 24x47, 91: 24x42, 92: 24x45 |
| **`3684`** | `Scene 477` | 27 | 388 | Dias Flac, Claude Kenni, Celine Jules, Precis F. Neumann, Ashton Anchors | 183: 40x46, 189: 36x47, 190: 36x47, 185: 60x49, 183: 28x49, 189: 36x47 |
| **`3685`** | `Scene 478` | 3 | 62 | Opera Vectra | 32767: 12x17, 32767: 8x5 |
| **`3686`** | `Scene 479` | 17 | 268 | Ernest Ravine, Opera Vectra, Leon D.S. Gehste, Rena Lanford | 182: 24x47, 32767: 8x5, 32767: 8x5, 32767: 16x14, 32767: 16x13, 10000: 20x20 |
| **`3688`** | `Scene 481` | 1 | 7 | - | 32767: 8x5 |
| **`3689`** | `Scene 482` | 6 | 47 | - | 32767: 8x5, 32767: 8x5, 32767: 16x14, 32767: 8x5, 32767: 16x13, 32767: 12x17 |
| **`3692`** | `Scene 485` | 1 | 3 | - | 155: 28x27 |
| **`3693`** | `Scene 486` | 1 | 3 | - | 154: 24x31 |
| **`3694`** | `Scene 487` | 1 | 3 | - | 157: 28x27 |
| **`3695`** | `Scene 488` | 1 | 12 | - | 32766: 16x36 |
| **`3697`** | `Scene 490` | 1 | 3 | - | 156: 24x21 |
| **`3698`** | `Scene 491` | 1 | 3 | - | 161: 28x28 |
| **`3699`** | `Scene 492` | 1 | 3 | - | 155: 28x27 |
| **`3700`** | `Scene 493` | 1 | 3 | - | 155: 28x27 |

### 3.40 Four Fields (Might, Courage, Intellect, Love) (Scene 494..573)
*Active Scenes: 63 | Total Sprite Frames: 1,378*

| Archive | Scene ID | Sections | Frames | Heroes Present | Other Selectors (ID: dims) |
| :---: | :---: | :---: | :---: | :--- | :--- |
| **`3701`** | `Scene 494` | 2 | 33 | - | 10000: 12x13, 67: 24x46 |
| **`3702`** | `Scene 495` | 2 | 6 | - | 156: 24x21, 153: 20x29 |
| **`3703`** | `Scene 496` | 2 | 6 | - | 156: 24x21, 153: 20x29 |
| **`3704`** | `Scene 497` | 2 | 33 | - | 10000: 12x13, 67: 24x46 |
| **`3705`** | `Scene 498` | 1 | 3 | - | 156: 24x21 |
| **`3708`** | `Scene 501` | 2 | 33 | - | 10000: 12x13, 67: 24x46 |
| **`3709`** | `Scene 502` | 2 | 6 | - | 157: 28x27, 156: 24x21 |
| **`3710`** | `Scene 503` | 1 | 3 | - | 156: 24x21 |
| **`3711`** | `Scene 504` | 1 | 3 | - | 156: 24x21 |
| **`3712`** | `Scene 505` | 2 | 33 | - | 10000: 12x13, 67: 24x46 |
| **`3713`** | `Scene 506` | 2 | 6 | - | 155: 28x27, 157: 28x27 |
| **`3714`** | `Scene 507` | 3 | 9 | - | 154: 24x31, 153: 20x29, 156: 24x21 |
| **`3715`** | `Scene 508` | 1 | 3 | - | 154: 24x31 |
| **`3716`** | `Scene 509` | 2 | 33 | - | 10000: 12x13, 67: 24x46 |
| **`3717`** | `Scene 510` | 2 | 6 | - | 154: 24x31, 156: 24x21 |
| **`3720`** | `Scene 513` | 2 | 6 | - | 156: 24x21, 152: 24x31 |
| **`3721`** | `Scene 514` | 1 | 3 | - | 156: 24x21 |
| **`3722`** | `Scene 515` | 2 | 15 | - | 32766: 16x36, 157: 28x27 |
| **`3724`** | `Scene 517` | 1 | 3 | - | 155: 28x27 |
| **`3725`** | `Scene 518` | 1 | 3 | - | 155: 28x27 |
| **`3726`** | `Scene 519` | 2 | 33 | - | 10000: 12x13, 67: 24x46 |
| **`3727`** | `Scene 520` | 2 | 6 | - | 154: 24x31, 152: 24x31 |
| **`3728`** | `Scene 521` | 2 | 6 | - | 154: 24x31, 152: 24x31 |
| **`3729`** | `Scene 522` | 2 | 33 | - | 10000: 12x13, 67: 24x46 |
| **`3730`** | `Scene 523` | 8 | 54 | - | 184: 40x46, 32767: 8x5, 32767: 8x5, 32767: 16x14, 32767: 12x17, 32767: 8x5 |
| **`3731`** | `Scene 524` | 11 | 43 | Rena Lanford, Claude Kenni, Celine Jules | 32767: 16x14, 32767: 8x5, 32767: 8x5, 32767: 16x13 |
| **`3733`** | `Scene 526` | 1 | 3 | - | 156: 24x21 |
| **`3735`** | `Scene 528` | 1 | 3 | - | 150: 24x21 |
| **`3736`** | `Scene 529` | 1 | 3 | - | 158: 24x31 |
| **`3738`** | `Scene 531` | 2 | 6 | - | 152: 24x31, 159: 20x29 |
| **`3739`** | `Scene 532` | 3 | 9 | - | 150: 24x21, 154: 24x31, 156: 24x21 |
| **`3742`** | `Scene 535` | 1 | 3 | - | 156: 24x21 |
| **`3745`** | `Scene 538` | 1 | 3 | - | 150: 24x21 |
| **`3747`** | `Scene 540` | 5 | 15 | - | 151: 28x28, 160: 24x31, 159: 20x29, 156: 24x21, 153: 20x29 |
| **`3748`** | `Scene 541` | 1 | 3 | - | 150: 24x21 |
| **`3750`** | `Scene 543` | 2 | 6 | - | 155: 28x27, 151: 28x28 |
| **`3752`** | `Scene 545` | 9 | 68 | Celine Jules | 32767: 8x5, 32767: 8x5, 32767: 16x13, 32767: 8x5, 32767: 16x14, 32767: 12x17 |
| **`3753`** | `Scene 546` | 2 | 24 | - | 32767: 12x17, 32766: 16x36 |
| **`3754`** | `Scene 547` | 5 | 21 | - | 32767: 8x5, 32767: 16x14, 180: 56x55, 156: 24x21, 150: 24x21 |
| **`3755`** | `Scene 548` | 17 | 235 | Leon D.S. Gehste | 188: 96x61, 107: 20x45, 108: 24x44, 102: 24x46, 141: 24x43, 88: 24x47 |
| **`3756`** | `Scene 549` | 2 | 20 | - | 32767: 8x5, 32767: 12x17 |
| **`3757`** | `Scene 550` | 1 | 3 | - | 156: 24x21 |
| **`3758`** | `Scene 551` | 5 | 24 | - | 150: 24x21, 156: 24x21, 153: 20x29, 159: 20x29, 32767: 12x17 |
| **`3759`** | `Scene 552` | 2 | 16 | - | 10000: 8x15, 32767: 12x17 |
| **`3760`** | `Scene 553` | 1 | 4 | - | 10000: 8x15 |
| **`3761`** | `Scene 554` | 4 | 26 | - | 10000: 12x12, 32767: 12x17, 32767: 8x5, 32767: 16x14 |
| **`3762`** | `Scene 555` | 1 | 2 | - | 10000: 12x12 |
| **`3763`** | `Scene 556` | 1 | 7 | - | 32767: 8x5 |
| **`3764`** | `Scene 557` | 4 | 35 | - | 32767: 8x5, 32767: 12x17, 32767: 8x5, 32767: 16x13 |
| **`3765`** | `Scene 558` | 2 | 24 | - | 92: 24x45, 156: 24x21 |
| **`3766`** | `Scene 559` | 2 | 24 | - | 150: 24x21, 88: 24x47 |
| **`3767`** | `Scene 560` | 1 | 12 | - | 32766: 16x36 |
| **`3768`** | `Scene 561` | 1 | 3 | - | 154: 24x31 |
| **`3769`** | `Scene 562` | 2 | 24 | - | 156: 24x21, 148: 24x47 |
| **`3770`** | `Scene 563` | 1 | 21 | - | 93: 24x44 |
| **`3771`** | `Scene 564` | 2 | 24 | - | 150: 24x21, 138: 24x45 |
| **`3772`** | `Scene 565` | 2 | 24 | - | 156: 24x21, 102: 24x46 |
| **`3774`** | `Scene 567` | 17 | 237 | Rena Lanford, Celine Jules, Bowman Jean, Dias Flac, Precis F. Neumann, Ashton Anchors, Leon D.S. Gehste, Opera Vectra, Ernest Ravine, Claude Kenni | 32767: 12x17, 32767: 8x5, 32767: 8x5, 32767: 16x14, 10000: 24x13 |
| **`3775`** | `Scene 568` | 1 | 12 | - | 32766: 16x36 |
| **`3776`** | `Scene 569` | 1 | 2 | - | 188: 96x61 |
| **`3778`** | `Scene 571` | 1 | 3 | - | 156: 24x21 |
| **`3779`** | `Scene 572` | 1 | 3 | - | 156: 24x21 |
| **`3780`** | `Scene 573` | 3 | 5 | Claude Kenni, Rena Lanford | 156: 24x21 |

### 3.44 Phynal Tower, Final Bastion & Endings (Scene 574..643)
*Active Scenes: 54 | Total Sprite Frames: 2,201*

| Archive | Scene ID | Sections | Frames | Heroes Present | Other Selectors (ID: dims) |
| :---: | :---: | :---: | :---: | :--- | :--- |
| **`3782`** | `Scene 575` | 18 | 155 | Claude Kenni, Rena Lanford | 147: 32x47, 147: 28x48, 147: 28x53, 147: 32x55, 147: 44x56, 147: 28x47 |
| **`3783`** | `Scene 576` | 10 | 64 | - | 147: 32x47, 147: 28x48, 147: 28x53, 147: 32x55, 147: 44x56, 147: 28x47 |
| **`3784`** | `Scene 577` | 2 | 25 | - | 32767: 16x14, 168: 28x44 |
| **`3785`** | `Scene 578` | 1 | 21 | - | 168: 28x44 |
| **`3786`** | `Scene 579` | 1 | 21 | - | 168: 28x44 |
| **`3787`** | `Scene 580` | 1 | 21 | - | 168: 28x44 |
| **`3788`** | `Scene 581` | 13 | 108 | Rena Lanford, Ashton Anchors, Precis F. Neumann, Claude Kenni, Leon D.S. Gehste, Noel Chandler | 32767: 8x5, 32767: 16x14, 32767: 8x5, 32767: 12x17 |
| **`3789`** | `Scene 582` | 1 | 21 | - | 29: 24x45 |
| **`3790`** | `Scene 583` | 4 | 61 | - | 121: 24x44, 32767: 16x13, 32767: 8x5, 167: 24x41 |
| **`3791`** | `Scene 584` | 4 | 67 | - | 32767: 16x14, 116: 20x42, 168: 28x44, 121: 24x44 |
| **`3792`** | `Scene 585` | 4 | 62 | - | 121: 24x44, 32767: 8x5, 32767: 12x17, 168: 28x44 |
| **`3793`** | `Scene 586` | 2 | 31 | - | 10000: 8x5, 121: 24x44 |
| **`3794`** | `Scene 587` | 9 | 164 | - | 221: 116x109, 121: 24x44, 167: 24x41, 168: 28x44, 32767: 12x17, 146: 24x46 |
| **`3795`** | `Scene 588` | 5 | 44 | Claude Kenni, Rena Lanford | 169: 180x142, 32767: 12x17, 32767: 8x5 |
| **`3796`** | `Scene 589` | 1 | 3 | - | 156: 24x21 |
| **`3800`** | `Scene 593` | 1 | 3 | - | 156: 24x21 |
| **`3801`** | `Scene 594` | 1 | 3 | - | 156: 24x21 |
| **`3802`** | `Scene 595` | 1 | 12 | - | 32766: 16x36 |
| **`3803`** | `Scene 596` | 8 | 143 | Claude Kenni, Rena Lanford | 200: 20x41, 32767: 16x13, 32767: 12x17, 10000: 12x12 |
| **`3805`** | `Scene 598` | 7 | 33 | Claude Kenni, Rena Lanford | 32767: 8x5, 32767: 16x13, 156: 24x21 |
| **`3806`** | `Scene 599` | 2 | 14 | Claude Kenni, Rena Lanford | - |
| **`3808`** | `Scene 601` | 3 | 17 | Claude Kenni, Rena Lanford | 156: 24x21 |
| **`3809`** | `Scene 602` | 3 | 26 | Claude Kenni, Rena Lanford | 32766: 16x36 |
| **`3810`** | `Scene 603` | 1 | 5 | - | 213: 92x45 |
| **`3811`** | `Scene 604` | 3 | 17 | - | 10000: 12x12, 32767: 8x5, 32767: 8x5 |
| **`3813`** | `Scene 606` | 3 | 11 | Claude Kenni, Rena Lanford | 32767: 8x5 |
| **`3814`** | `Scene 607` | 4 | 11 | - | 181: 64x67, 32767: 16x14, 150: 24x21, 181: 48x66 |
| **`3815`** | `Scene 608` | 1 | 3 | - | 150: 24x21 |
| **`3816`** | `Scene 609` | 4 | 11 | - | 181: 64x67, 32767: 16x14, 156: 24x21, 181: 48x66 |
| **`3817`** | `Scene 610` | 1 | 3 | - | 156: 24x21 |
| **`3818`** | `Scene 611` | 4 | 11 | - | 181: 64x67, 32767: 16x14, 156: 24x21, 181: 48x66 |
| **`3819`** | `Scene 612` | 1 | 3 | - | 156: 24x21 |
| **`3820`** | `Scene 613` | 4 | 20 | - | 181: 64x67, 32767: 16x14, 181: 48x66, 32766: 16x36 |
| **`3821`** | `Scene 614` | 1 | 12 | - | 32766: 16x36 |
| **`3822`** | `Scene 615` | 5 | 14 | - | 181: 64x67, 32767: 16x14, 159: 20x29, 156: 24x21, 181: 48x66 |
| **`3823`** | `Scene 616` | 2 | 6 | - | 159: 20x29, 156: 24x21 |
| **`3824`** | `Scene 617` | 4 | 26 | - | 32767: 16x14, 32767: 8x5, 32767: 8x5, 32767: 8x5 |
| **`3825`** | `Scene 618` | 11 | 82 | Claude Kenni, Rena Lanford | 32767: 8x5, 32767: 16x14, 32767: 8x5, 32767: 8x5, 32767: 12x17 |
| **`3826`** | `Scene 619` | 3 | 29 | - | 10000: 8x5, 32767: 12x17, 32767: 8x5 |
| **`3829`** | `Scene 622` | 6 | 99 | - | 32767: 8x5, 32767: 8x5, 137: 24x45, 142: 24x46, 138: 24x45, 139: 24x46 |
| **`3832`** | `Scene 625` | 18 | 193 | Claude Kenni, Chisato Madison | 32767: 8x5, 32767: 8x5, 32767: 16x14, 32767: 8x5, 32767: 12x17, 137: 24x45 |
| **`3833`** | `Scene 626` | 11 | 120 | Claude Kenni | 32767: 12x17, 32767: 16x13, 32767: 8x5, 32767: 12x18, 32767: 8x5, 32767: 8x5 |
| **`3834`** | `Scene 627` | 11 | 120 | Claude Kenni | 32767: 12x17, 32767: 16x13, 32767: 8x5, 32767: 12x18, 32767: 8x5, 32767: 8x5 |
| **`3835`** | `Scene 628` | 8 | 95 | - | 27: 24x38, 137: 24x45, 144: 24x30, 32767: 8x5, 32767: 8x5, 32767: 8x5 |
| **`3836`** | `Scene 629` | 1 | 12 | - | 32767: 12x17 |
| **`3837`** | `Scene 630` | 1 | 3 | - | 156: 24x21 |
| **`3839`** | `Scene 632` | 1 | 3 | - | 155: 28x27 |
| **`3840`** | `Scene 633` | 1 | 3 | - | 153: 20x29 |
| **`3842`** | `Scene 635` | 1 | 3 | - | 156: 24x21 |
| **`3843`** | `Scene 636` | 1 | 3 | - | 156: 24x21 |
| **`3845`** | `Scene 638` | 1 | 2 | - | 10000: 20x31 |
| **`3846`** | `Scene 639` | 1 | 3 | - | 156: 24x21 |
| **`3849`** | `Scene 642` | 9 | 71 | Rena Lanford, Claude Kenni | 10000: 12x12, 32767: 8x5, 10000: 88x94, 10000: 20x31, 32767: 12x17, 187: 80x51 |
| **`3850`** | `Scene 643` | 8 | 88 | Opera Vectra | 32767: 8x5, 32767: 16x13, 32767: 16x14, 39: 12x19, 32767: 8x5, 175: 20x45 |

### 3.47 Overworld Dungeons, Sub-Levels & Secret Chambers (Scene 644..947)
*Active Scenes: 95 | Total Sprite Frames: 2,884*

| Archive | Scene ID | Sections | Frames | Heroes Present | Other Selectors (ID: dims) |
| :---: | :---: | :---: | :---: | :--- | :--- |
| **`3854`** | `Scene 647` | 1 | 3 | - | 156: 24x21 |
| **`3859`** | `Scene 652` | 1 | 10 | - | 10000: 8x5 |
| **`3860`** | `Scene 653` | 1 | 10 | - | 10000: 8x5 |
| **`3864`** | `Scene 657` | 19 | 197 | Claude Kenni | 167: 24x41, 121: 24x44, 168: 28x44, 147: 32x47, 32767: 12x17, 147: 28x48 |
| **`3868`** | `Scene 661` | 1 | 3 | - | 156: 24x21 |
| **`3869`** | `Scene 662` | 1 | 3 | - | 156: 24x21 |
| **`3876`** | `Scene 669` | 2 | 19 | - | 147: 28x53, 147: 32x55 |
| **`3877`** | `Scene 670` | 1 | 12 | - | 32766: 16x36 |
| **`3878`** | `Scene 671` | 1 | 12 | - | 32766: 16x36 |
| **`3880`** | `Scene 673` | 1 | 3 | - | 156: 24x21 |
| **`3881`** | `Scene 674` | 4 | 30 | - | 147: 28x48, 32767: 12x17, 32767: 16x14, 147: 28x48 |
| **`3885`** | `Scene 678` | 1 | 12 | - | 32766: 16x36 |
| **`3886`** | `Scene 679` | 1 | 3 | - | 159: 20x29 |
| **`3892`** | `Scene 685` | 7 | 76 | - | 10000: 96x94, 147: 32x47, 32767: 8x5, 146: 24x46, 121: 24x44, 147: 44x39 |
| **`3893`** | `Scene 686` | 4 | 71 | - | 167: 24x41, 121: 24x44, 168: 28x44, 221: 60x126 |
| **`3895`** | `Scene 688` | 46 | 408 | Claude Kenni, Rena Lanford, Celine Jules, Bowman Jean, Dias Flac, Precis F. Neumann, Ashton Anchors, Leon D.S. Gehste, Opera Vectra, Ernest Ravine, Noel Chandler, Chisato Madison | 10000: 8x6, 93: 24x44, 66: 24x27, 81: 24x47, 26: 24x39, 15: 20x43 |
| **`3896`** | `Scene 689` | 3 | 63 | - | 57: 24x39, 58: 24x39, 31: 24x42 |
| **`3902`** | `Scene 695` | 3 | 33 | - | 121: 24x44, 32767: 8x5, 32767: 16x14 |
| **`3904`** | `Scene 697` | 3 | 26 | - | 32767: 8x5, 32767: 12x17, 32767: 8x5 |
| **`3905`** | `Scene 698` | 5 | 29 | Claude Kenni, Rena Lanford | 32767: 8x5, 32767: 8x5, 10000: 12x13 |
| **`3910`** | `Scene 703` | 1 | 3 | - | 156: 24x21 |
| **`3911`** | `Scene 704` | 11 | 223 | Celine Jules, Bowman Jean, Dias Flac, Precis F. Neumann, Ashton Anchors, Leon D.S. Gehste, Opera Vectra, Ernest Ravine, Noel Chandler, Chisato Madison | 10000: 144x17 |
| **`3912`** | `Scene 705` | 2 | 16 | - | 10000: 144x17, 205: 40x48 |
| **`3913`** | `Scene 706` | 1 | 3 | - | 156: 24x21 |
| **`3914`** | `Scene 707` | 1 | 3 | - | 156: 24x21 |
| **`3916`** | `Scene 709` | 1 | 3 | - | 156: 24x21 |
| **`3917`** | `Scene 710` | 1 | 3 | - | 156: 24x21 |
| **`3918`** | `Scene 711` | 3 | 41 | - | 207: 84x86, 160: 24x31, 157: 28x27 |
| **`3919`** | `Scene 712` | 1 | 3 | - | 155: 28x27 |
| **`3920`** | `Scene 713` | 1 | 3 | - | 150: 24x21 |
| **`3923`** | `Scene 716` | 2 | 44 | - | 10000: 144x17, 210: 44x8 |
| **`3924`** | `Scene 717` | 2 | 14 | - | 230: 24x44, 231: 24x42 |
| **`3925`** | `Scene 718` | 2 | 14 | - | 228: 24x46, 234: 24x44 |
| **`3926`** | `Scene 719` | 1 | 3 | - | 156: 24x21 |
| **`3927`** | `Scene 720` | 2 | 14 | - | 229: 24x45, 233: 24x42 |
| **`3928`** | `Scene 721` | 1 | 7 | - | 232: 24x42 |
| **`3929`** | `Scene 722` | 1 | 3 | - | 150: 24x21 |
| **`3931`** | `Scene 724` | 1 | 3 | - | 153: 20x29 |
| **`3934`** | `Scene 727` | 2 | 68 | - | 10000: 144x17, 209: 36x9 |
| **`3937`** | `Scene 730` | 1 | 3 | - | 150: 24x21 |
| **`3942`** | `Scene 735` | 1 | 3 | - | 159: 20x29 |
| **`3944`** | `Scene 737` | 2 | 14 | - | 10000: 144x17, 201: 48x38 |
| **`3946`** | `Scene 739` | 3 | 16 | - | 10000: 36x95, 32767: 8x5, 32767: 12x18 |
| **`3947`** | `Scene 740` | 3 | 37 | - | 10000: 144x17, 92: 24x45, 156: 24x21 |
| **`3948`** | `Scene 741` | 1 | 3 | - | 156: 24x21 |
| **`3951`** | `Scene 744` | 3 | 24 | - | 10000: 144x17, 32767: 8x5, 156: 24x21 |
| **`3952`** | `Scene 745` | 1 | 3 | - | 156: 24x21 |
| **`3954`** | `Scene 747` | 1 | 3 | - | 156: 24x21 |
| **`3955`** | `Scene 748` | 1 | 3 | - | 156: 24x21 |
| **`3958`** | `Scene 751` | 3 | 58 | - | 10000: 144x17, 32767: 8x5, 198: 24x41 |
| **`3960`** | `Scene 753` | 8 | 133 | - | 198: 24x41, 32767: 16x13, 209: 36x9, 32767: 12x17, 32767: 16x14, 32767: 8x5 |
| **`3961`** | `Scene 754` | 8 | 120 | - | 198: 24x41, 32767: 8x5, 32767: 8x5, 32767: 8x5, 32767: 12x18, 32767: 12x17 |
| **`3963`** | `Scene 756` | 4 | 54 | - | 10000: 8x5, 10000: 144x17, 32767: 8x5, 131: 84x86 |
| **`3965`** | `Scene 758` | 2 | 43 | - | 227: 44x44, 15: 20x43 |
| **`3967`** | `Scene 760` | 1 | 13 | - | 10000: 144x17 |
| **`3969`** | `Scene 762` | 1 | 3 | - | 157: 28x27 |
| **`3970`** | `Scene 763` | 3 | 34 | - | 10000: 144x17, 211: 216x180, 156: 24x21 |
| **`3971`** | `Scene 764` | 1 | 2 | - | 10000: 12x12 |
| **`3973`** | `Scene 766` | 1 | 13 | - | 10000: 144x17 |
| **`3974`** | `Scene 767` | 1 | 3 | - | 156: 24x21 |
| **`3976`** | `Scene 769` | 1 | 3 | - | 156: 24x21 |
| **`3977`** | `Scene 770` | 1 | 3 | - | 156: 24x21 |
| **`3978`** | `Scene 771` | 1 | 3 | - | 156: 24x21 |
| **`3980`** | `Scene 773` | 3 | 9 | - | 150: 24x21, 156: 24x21, 159: 20x29 |
| **`3982`** | `Scene 775` | 3 | 40 | - | 10000: 144x17, 32767: 8x5, 217: 100x76 |
| **`3984`** | `Scene 777` | 2 | 16 | - | 10000: 144x17, 150: 24x21 |
| **`3986`** | `Scene 779` | 1 | 3 | - | 159: 20x29 |
| **`3987`** | `Scene 780` | 2 | 6 | - | 159: 20x29, 153: 20x29 |
| **`3988`** | `Scene 781` | 4 | 56 | - | 198: 24x41, 32767: 8x5, 32767: 8x5, 32767: 16x14 |
| **`3989`** | `Scene 782` | 1 | 3 | - | 153: 20x29 |
| **`3993`** | `Scene 786` | 4 | 63 | - | 10000: 144x17, 32767: 8x5, 32767: 12x17, 212: 96x74 |
| **`3995`** | `Scene 788` | 1 | 13 | - | 10000: 144x17 |
| **`3998`** | `Scene 791` | 5 | 21 | Claude Kenni, Rena Lanford | 10000: 144x17, 159: 20x29, 156: 24x21 |
| **`3999`** | `Scene 792` | 1 | 3 | - | 155: 28x27 |
| **`4000`** | `Scene 793` | 1 | 3 | - | 155: 28x27 |
| **`4001`** | `Scene 794` | 1 | 13 | - | 10000: 144x17 |
| **`4004`** | `Scene 797` | 1 | 3 | - | 157: 28x27 |
| **`4005`** | `Scene 798` | 5 | 45 | - | 10000: 144x17, 213: 92x45, 32767: 12x17, 10000: 12x13, 155: 28x27 |
| **`4006`** | `Scene 799` | 2 | 6 | - | 152: 24x31, 158: 24x31 |
| **`4007`** | `Scene 800` | 1 | 3 | - | 158: 24x31 |
| **`4010`** | `Scene 803` | 1 | 3 | - | 155: 28x27 |
| **`4012`** | `Scene 805` | 1 | 3 | - | 161: 28x28 |
| **`4013`** | `Scene 806` | 1 | 3 | - | 158: 24x31 |
| **`4014`** | `Scene 807` | 4 | 41 | - | 10000: 144x17, 10000: 8x5, 32767: 12x17, 214: 76x112 |
| **`4015`** | `Scene 808` | 1 | 13 | - | 10000: 144x17 |
| **`4016`** | `Scene 809` | 1 | 10 | - | 216: 104x156 |
| **`4018`** | `Scene 811` | 1 | 13 | - | 10000: 144x17 |
| **`4019`** | `Scene 812` | 1 | 3 | - | 153: 20x29 |
| **`4020`** | `Scene 813` | 1 | 3 | - | 159: 20x29 |
| **`4021`** | `Scene 814` | 1 | 13 | - | 10000: 144x17 |
| **`4022`** | `Scene 815` | 4 | 48 | - | 215: 92x130, 32767: 8x5, 32767: 8x5, 156: 24x21 |
| **`4025`** | `Scene 818` | 1 | 3 | - | 153: 20x29 |
| **`4027`** | `Scene 820` | 1 | 13 | - | 10000: 144x17 |
| **`4029`** | `Scene 822` | 1 | 3 | - | 159: 20x29 |
| **`4033`** | `Scene 826` | 16 | 318 | Celine Jules, Bowman Jean, Dias Flac, Precis F. Neumann, Ashton Anchors, Leon D.S. Gehste, Opera Vectra, Ernest Ravine, Noel Chandler, Chisato Madison | 67: 24x46, 68: 24x45, 47: 24x31, 32: 20x31, 48: 24x34, 157: 28x27 |

---

## 4. Extraction & Tooling Reference

To extract sprites from any scene container indexed above:
```powershell
# Extract scene sprite frames from Archive 3418
python tools/so2_scene_npc_extract.py --archive 3418 --scale 2

# Or via the unified SaveConverter CLI:
python saveconv.py so2-scene-npc --archive 3418 --scale 2

# Rebuild master scene sprite index:
python tools/so2_scene_sprite_indexer.py
```
