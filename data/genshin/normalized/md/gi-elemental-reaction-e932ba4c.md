# Elemental Reaction

<!-- https://genshin-impact.fandom.com/wiki/Elemental_Reaction | type=mechanic | effective=None -->

Overview Level Scaling

For Elemental Reactions in Genius Invokation TCG , see Genius Invokation TCG/Rules § Elemental Reactions . See also: Elemental Gauge Theory


## Infobox

Name: Elemental Reaction
Type: Combat Game Systems

Elemental Reactions are triggered by applying certain combinations of elemental effects on a target (enemies, players, or objects).

When an element is applied to a target, it will create an elemental aura that decays over time. Elemental Reactions will occur when a second element is applied onto a target with an existing elemental aura.

Triggering elemental reactions will consume the existing aura by varying amounts depending on the type of reaction triggered and the gauge units of the triggering element. This will shorten the existing aura's duration or completely remove it.

Note that many sources of elemental damage have Internal Cooldown before being able to reapply their element and therefore may not be able to trigger Elemental Reactions on every hit.

Certain more complex mechanics of elemental reactions are explained in-depth in Elemental Gauge Theory , a framework for understanding interaction of elements.


## Overview

Elemental Reactions have the following effects:

|  |  | Applied Element | Applied Element | Applied Element | Applied Element | Applied Element | Applied Element | Applied Element | Applied Element |
|---|---|---|---|---|---|---|---|---|---|
| Triggered Element |  | — | Vaporize ( 1.5× ) | Overloaded | Melt ( 2× ) | Burning | Swirl | — | — |
| Triggered Element |  | Vaporize ( 2× ) | — | Electro-Charged Lunar-Charged | Frozen Shatter | Bloom Lunar-Bloom Burgeon Hyperbloom | Swirl | — | — |
| Triggered Element |  | Overloaded | Electro-Charged Lunar-Charged | — | Superconduct Stellar-Conduct | Quicken Spread Aggravate | Swirl | — | — |
| Triggered Element |  | Melt ( 1.5× ) | Frozen Shatter | Superconduct Stellar-Conduct | — | — | Swirl | Stellar Swirl | — |
| Triggered Element |  | Burning | Bloom Lunar-Bloom Burgeon Hyperbloom | Quicken Spread Aggravate | — | — | — | — | — |
| Triggered Element |  | Swirl | Swirl | Swirl | Swirl | — | — | — | — |
| Triggered Element |  | — | — | — | Stellar Swirl | — | — | — | — |
| Triggered Element |  | Crystallize | Crystallize | Crystallize | Crystallize | — | — | — | — |
| Triggered Element |  | — | Lunar-Crystallize | — | — | — | — | — | — |

Elemental Reaction damage can be increased by the Elemental Mastery of the character causing the reaction. The in-game interface shows the damage bonus provided by the character's current elemental mastery. This bonus will be applied in different ways, depending on the type of reaction.


## Transformative Reactions

See also: Damage § Transformative Reaction Damage , and Elemental Reaction/Level Scaling

Transformative Reactions include Overloaded , Shattered , Electro-Charged , Superconduct , Swirl , Burning , Bloom , Hyperbloom , and Burgeon .

- These reactions deal their own instances of damage, which is separate from the attacks triggering them.
- These reactions have a Base Damage determined by the type of reaction and the level of the character triggering the reaction.
- The Base Damage is then multiplied by a percentage determined by the Elemental Mastery of the character. The percentage can be seen in-game in the Details section of the Attributes page.
- Transformative Reaction DMG cannot CRIT and is only based on level, meaning ATK, CRIT Rate and CRIT DMG have no impact.
- Transformative Reaction DMG ignores the target's DEF , but is affected by Resistance .


## Amplifying Reactions

See also: Damage § Amplifying Reaction Damage

Amplifying Reactions include Vaporize and Melt .

- Unlike Transformative Reactions, Melt and Vaporize do not deal damage of their own. Instead, they multiply the damage of the attacks that trigger them by either 2× or 1.5× depending on which element triggers the reaction. 2× and 1.5× amplifying reactions are sometimes described as "forward" and "reverse" respectively.
- The damage is multiplied again by a percentage determined by the Elemental Mastery of the character. The percentage can be seen in-game in the Details section of the Attributes page.
- 1.5× reactions will consume less of the initial element, often preserving the aura, while 2× reactions consume more and tend to immediately remove the initial element. This is elaborated further in Elemental Gauge Theory .

| Reaction | Element Order (2nd → 1st) | Effect |
|---|---|---|
| Melt | → | Damage considers additional multiplier of 2 along with additional multiplier from elemental mastery. |
| Melt | → | Damage considers additional multiplier of 1.5 along with additional multiplier from elemental mastery. |
| Vaporize | → | Damage considers additional multiplier of 1.5 along with additional multiplier from elemental mastery. |
| Vaporize | → | Damage considers additional multiplier of 2 along with additional multiplier from elemental mastery. |


## Additive Reactions

See also: Damage § Catalyze Damage Bonus

Additive Reactions (unofficial name) , or simply denoted as "Catalyze Reactions" in Miliastra Wonderland , include Spread and Aggravate .

- Additive Reactions also increase the DMG of the hit that triggers it without dealing DMG of its own. However, they provide a Additive Base DMG Bonus that adds onto base DMG in the DMG formula, instead of multiplying DMG like Amplifying Reactions.
- The Additive Base DMG Bonus provided by Spread is slightly higher than that of Aggravate.


## Lunar Reactions

See also: Damage § Lunar Reaction Damage

Lunar Reactions include Lunar-Charged , Lunar-Bloom , and Lunar-Crystallize .

- These reactions can be dealt either directly by a character's talent (all Lunar Reactions), or through a separate instance of damage that takes into account the stats of all contributing characters and is dealt independently of the triggering attacks (all but Lunar-Bloom ).
- In the latter case, these reactions have their Base Damage determined by the type of reaction and the level of the character triggering the reaction.
- The Base Damage is multiplied by a Base DMG Bonus provided by certain Moonsign Benediction Passives , and then again by a percentage determined by the Elemental Mastery of the character. The percentage can be seen in-game in the Details section of the Attributes page.
- Lunar Reaction DMG ignores DMG Bonus and the target's DEF , but is affected by Resistance .


## Stellar Glimmer Reactions

See also: Damage § Stellar Glimmer Reaction Damage

Stellar Glimmer Reactions include Stellar-Conduct and Stellar Swirl .

- These reactions can be dealt either directly by a character's talent (all Stellar Glimmer Reactions), or through a separate instance of damage that takes into account the stats of all contributing characters and is dealt independently of the triggering attacks (all but Stellar-Conduct ).
- In the latter case, these reactions have their Base Damage determined by the type of reaction and the level of the character triggering the reaction.
- The Base Damage is multiplied by a Base DMG Bonus provided by Stellar Jubilee Passives , and then again by a percentage determined by the Elemental Mastery of the character. The percentage can be seen in-game in the Details section of the Attributes page.
- Stellar Glimmer Reaction DMG ignores DMG Bonus and the target's DEF , but is affected by Resistance .


## Order of Application

The effects of Elemental Reactions scale off of the stats of the character who triggers the reaction. The stats of the character that produced the initial aura is not considered.


## Talents

There are 16 Talents that have special effects when an Elemental Reaction is triggered:

| Talent | Description | Type |
|---|---|---|
| All Schemes to Know Nahida | Sends forth karmic bonds of wood and tree from her side, dealing AoE Dendro DMG and marking up to 8 opponents hit with the Seed of Skandha. When held, this skill will trigger differently. Hold Enters Aiming Mode, which will allow you to select a limited number of opponents within a limited area. During this time, Nahida's resistance to interruption will be increased. When released, this skill deals Dendro DMG to these opponents and marks them with the Seed of Skandha. Aiming Mode will last up to 5s and can select a maximum of 8 opponents. Seed of Skandha Opponents who have been marked by the Seed of Skandha will be linked to one another up till a certain distance. After you trigger Elemental Reactions on opponents who are affected by the Seeds of Skandha or when they take DMG from Dendro Cores (including Burgeon and Hyperbloom DMG), Nahida will unleash Tri-Karma Purification on the opponents and all connected opponents, dealing Dendro DMG based on her ATK and Elemental Mastery. You can trigger at most 1 Tri-Karma Purification within a short period of time. | Elemental Skill |
| An Architect's Undertaking Kaveh | When DMG dealt by a Dendro Core (including DMG from Burgeon and Hyperbloom) hits Kaveh, Kaveh will regain HP equal to 300% of his Elemental Mastery . This effect can be triggered once every 0.5s. | 1st Ascension Passive |
| An Eye for Gold Dori | After a character connected to the Jinni triggers an Electro-Charged , Lunar-Charged , Superconduct , Overloaded , Quicken , Aggravate , Hyperbloom , or an Electro Swirl or Crystallize reaction, the CD of Spirit-Warding Lamp: Troubleshooter Cannon is decreased by 1s. This effect can be triggered once every 3s. | 1st Ascension Passive |
| Ancient Rite: The Thundering Sands Sethos | Gathers the might of thunder, dealing AoE Electro DMG and quickly retreating. If this attack triggers Electro-Charged , Lunar-Charged , Superconduct , Overloaded , Quicken , Aggravate , or Electro Swirl reactions, Sethos recovers a certain amount of Elemental Energy . | Elemental Skill |
| Catalyst Conversion Sucrose | When Sucrose triggers a Swirl or Stellar Swirl reaction, all characters in the party with the matching element (excluding Sucrose) have their Elemental Mastery increased by 50 for 8s. | 1st Ascension Passive |
| Choice Treasures Diona | Within 20s after using the Elemental Skill Icy Paws , Diona will also fire off three Icy Paws when party members trigger Superconduct , Stellar-Conduct , Cryo Swirl , or Stellar Swirl reactions. Icy Paws fired this way cannot generate Elemental Particles, nor will they generate a shield upon hitting opponents. This effect can occur once every 3.5s. Additionally, Diona will also enter the Radiance: Stellar-Conduct state when she is inside a Polestar Field , or the Radiance: Stellar Swirl state for 8s after a nearby party member triggers a Stellar Swirl reaction. | Witch's Revelation Passive |
| Dark-Shattering Flame Clorinde | After a nearby party member triggers an Electro-related reaction against an opponent, Electro DMG dealt by Clorinde's Normal Attacks and Last Lightfall will be increased by 20% of Clorinde's ATK for 15s. Max 3 stacks. Each stack is counted independently. The Maximum DMG increase achievable this way for the above attacks is 1,800. | 1st Ascension Passive |
| Floral Sidewinder Collei | If one of your party members has triggered Burning , Quicken , Aggravate , Spread , Bloom , Hyperbloom , Burgeon , or Lunar-Bloom reactions before the Floral Ring returns, it will grant the character the Sprout effect upon return, which will continuously deal Dendro DMG equivalent to 40% of Collei's ATK to nearby opponents for 3s. If another Sprout effect is triggered during its initial duration, the initial effect will be removed. DMG dealt by Sprout is considered Elemental Skill DMG. | 1st Ascension Passive |
| Heir to the Ancient Sea's Authority Neuvillette | When a party member triggers a Vaporize , Frozen , Electro-Charged , Lunar-Charged , Bloom , Lunar-Bloom , Hydro Swirl , Hydro Crystallize or a Lunar-Crystallize reaction on opponents, 1 stack of Past Draconic Glories will be granted to Neuvillette for 30s. Max 3 stacks. Past Draconic Glories causes Charged Attack: Equitable Judgment to deal 110%/125%/160% of its original DMG. The stacks of Past Draconic Glories created by each kind of Elemental Reaction exist independently. | 1st Ascension Passive |
| Life-Prolonging Methods Qiqi | When a character under the effects of Adeptus Art: Herald of Frost triggers an Elemental Reaction , their Incoming Healing Bonus is increased by 20% for 8s. | 1st Ascension Passive |
| Nightshade Synesthesia Ororon | After a nearby party member triggers Nightsoul Burst , Ororon will gain 40 Nightsoul points . Within 15s after using his Elemental Skill , when other party members' Hydro or Electro attacks hit opponents, Ororon will gain 5 Nightsoul points, an effect that can occur every 0.3s for a maximum of 10 times during this 15s duration. Ororon can have a maximum of 80 Nightsoul points. Also, when nearby opponents take Electro-Charged or Lunar-Charged reaction DMG or Nightsoul-aligned DMG dealt by other nearby characters, Ororon will consume 10 Nightsoul points (provided he has at least that amount), entering the Nightsoul's Blessing state and triggering the Hypersense effect: Deal Nightsoul-aligned Electro DMG based on 160% of Ororon's ATK to at most 4 nearby opponents. The aforementioned effect can trigger once every 1.8s. Nightsoul's Blessing: Ororon Ororon's Nightsoul's Blessing state lasts 6s. | 1st Ascension Passive |
| Paradoxical Practice Shikanoin Heizou | When Shikanoin Heizou activates a Swirl reaction while on the field, he will gain 1 Declension stack for Heartstopper Strike . This effect can be triggered every 0.1s. | 1st Ascension Passive |
| Poetics of Fuubutsu Kaedehara Kazuha | Upon triggering a Swirl or Stellar Swirl reaction, Kaedehara Kazuha will grant all party members a 0.04% Elemental DMG Bonus to the element absorbed by Swirl for every point of Elemental Mastery he has for 8s. Bonuses for different elements obtained through this method can co-exist. | 4th Ascension Passive |
| Someone More Capable Sayu | When Sayu triggers a Swirl reaction while active, she heals all your characters and nearby allies for 300 HP. She will also heal an additional 1.2 HP for every point of Elemental Mastery she has. This effect can be triggered once every 2s. | 1st Ascension Passive |
| The Languid Wood Collei | When a character within the Cuilein-Anbar Zone triggers Burning , Quicken , Aggravate , Spread , Bloom , Hyperbloom , Burgeon , or Lunar-Bloom reactions, the Zone's duration will be increased by 1s. A single Trump-Card Kitty can be extended by up to 3s. | 4th Ascension Passive |
| Undone Be Thy Sinful Hex Fischl | If your active character triggers an Electro -related Elemental Reaction when Oz is on the field, the opponent shall be stricken with Thundering Retribution that deals Electro DMG equal to 80% of Fischl's ATK. | 4th Ascension Passive |

There are 13 Talents that have special effects that enhance certain Elemental Reactions:

| Talent | Description | Type |
|---|---|---|
| All Things Are of the Earth Baizhu | Characters who are healed by Seamless Shields will gain the Year of Verdant Favor effect: Each 1,000 Max HP that Baizhu possesses that does not exceed 50,000 will increase the Burning, Bloom, Hyperbloom, and Burgeon reaction DMG dealt by these characters by 2%, their Lunar-Bloom DMG by 0.7%, and the DMG Bonus provided by Aggravate and Spread by 0.8%. This effect lasts 6s. | 4th Ascension Passive |
| Artistic Ingenuity Kaveh | Uses Mehrak 's mapping ability for offensive purposes, initiating a radial scan that deals AoE Dendro DMG . It will also scan all Dendro Cores in its AoE and cause them to immediately burst. | Elemental Skill |
| Assemblage Hub Ineffa | When a party member triggers the Electro-Charged reaction, it will be converted into the Lunar-Charged reaction, with every 100 ATK that Ineffa has increasing Lunar-Charged's Base DMG by 0.7%, up to a maximum of 14%. Additionally, when Ineffa is in the party, the party's Moonsign will increase by 1 level. | Moonsign Benediction Passive |
| Court of Dancing Petals Nilou | When all characters in the party are all Dendro or Hydro , and there are at least one Dendro character and one Hydro character: The completion of the third dance step of Nilou's Dance of Haftkarsvar will grant all nearby characters the Golden Chalice's Bounty for 30s. Characters under the effect of Golden Chalice's Bounty will increase the Elemental Mastery of all nearby characters by 100 for 10s whenever they are hit by Dendro attacks . Also, triggering the Bloom or Lunar-Bloom reaction will create Bountiful Cores instead of Dendro Cores. Such Cores will burst very quickly after being created, and they have larger AoEs. Bountiful Cores cannot trigger Hyperbloom or Burgeon , and they share an upper numerical limit with Dendro Cores. Bountiful Core DMG is considered DMG dealt by Dendro Cores produced by Bloom. Should the party not meet the conditions for this Ascension Talent, any existing Golden Chalice's Bounty effects will be canceled. | 1st Ascension Passive |
| Dance of Aurore Odette | Odette will enter the Radiance: Stellar-Conduct state when she is inside a Polestar Field , or the Radiance: Stellar Swirl state for 8s after a nearby party member triggers a Stellar Swirl reaction. When a party member triggers a Superconduct or Cryo Swirl reaction, it becomes a Stellar-Conduct or Stellar Swirl reaction instead, and the Base DMG of said reaction is also increased by 0.7% for every 100 points of Odette's ATK. A maximum increase of 14% can be obtained in this way. | Stellar Jubilee Passive |
| Dreamy Dance of Aeons Nilou | Every 1,000 points of Nilou's Max HP above 30,000 will cause the DMG dealt by Bountiful Cores created by characters affected by Golden Chalice's Bounty to increase by 9%. The maximum increase in Bountiful Core DMG that can be achieved this way is 400%. | 4th Ascension Passive |
| Habitat Survey Linnea | When a party member triggers a Hydro Crystallize reaction, it will be converted into the Lunar-Crystallize reaction, with every 100 DEF that Linnea has increasing Lunar-Crystallize's Base DMG by 0.7%, up to a maximum of 14%. Additionally, when Linnea is in the party, the party's Moonsign will increase by 1 level. | Moonsign Benediction Passive |
| Illusory Frostmirror Traveler (Cryo) | The Traveler will enter the Radiance: Stellar-Conduct state when inside a Polestar Field, or the Radiance: Stellar Swirl state for 8s after a nearby party member triggers a Stellar Swirl reaction. When a party member triggers a Superconduct or Cryo Swirl reaction, it becomes a Stellar-Conduct or Stellar Swirl reaction instead, and the Base DMG of said reaction is also increased by 0.35% for every 100 points of the Traveler's ATK. A maximum 7% increase can be obtained in this way. | Stellar Jubilee Passive |
| Light of Rationalisme Sandrone | Sandrone will enter the Radiance: Stellar Conduct state when she is inside a Polestar Field , or the Radiance: Stellar Swirl state for 8s after a nearby party member triggers a Stellar Swirl reaction. When a party member triggers a Superconduct or Cryo Swirl reaction, it becomes a Stellar-Conduct or Stellar Swirl reaction instead, and the Base DMG of the aforementioned reaction is also increased by 0.7% for every 100 points of Sandrone's ATK. A maximum increase of 14% can be obtained in this way. | Stellar Jubilee Passive |
| Moonlight, Lent Unto You Columbina | When a party member triggers an Electro-Charged , Bloom , or Hydro- Crystallize reaction, it will be converted into a Lunar-Charged , Lunar-Bloom , or Lunar-Crystallize reaction respectively. Lunar Reaction DMG inflicted by party members gain a Base DMG increase based on Columbina's Max HP . For every 1,000 points of Max HP, the Base DMG of Lunar reactions is increased by 0.2%, up to a maximum of 7%. Additionally, when Columbina is in the party, the party's Moonsign will increase by 1 level. | Moonsign Benediction Passive |
| Old World Secrets Flins | When a party member triggers an Electro-Charged reaction, it will be converted into the Lunar-Charged reaction, with every 100 ATK that Flins has increasing Lunar-Charged's Base DMG by 0.7%, up to a maximum of 14%. Additionally, when Flins is in the party, the party's Moonsign will increase by 1 level. | Moonsign Benediction Passive |
| Painted Dome Kaveh | Completely unleashes Mehrak 's energy and creates a cubic scanned space, dealing AoE Dendro DMG to all opponents within it, causing all Dendro Cores in its AoE to immediately burst, and granting Kaveh the following enhanced combat abilities for a specific duration: Increases Kaveh's Normal, Charged, and Plunging Attack AoE, and converts his attack DMG to Dendro DMG that cannot be overridden. All Dendro Cores created by all your own party members through Bloom and Lunar-Bloom reactions will deal additional DMG when they burst. Increases Kaveh's resistance to interruption. These effects will be canceled once Kaveh leaves the field. | Elemental Burst |
| The Coursing Sun and Moon Zibai | When a party member triggers a Hydro Crystallize reaction, it will be converted into the Lunar-Crystallize reaction, with every 100 DEF that Zibai has increasing Lunar-Crystallize's Base DMG by 0.7%, up to a maximum of 14%. Additionally, when Zibai is in the party, the party's Moonsign will increase by 1 level. | Moonsign Benediction Passive |


## Constellations

There are 9 Constellations that have special effects when an Elemental Reaction is triggered:

| Constellation | Description | Level |
|---|---|---|
| Attunement Keqing | For 10s after Keqing triggers an Electro-related Elemental Reaction , her ATK is increased by 25%. | 4 |
| Through Hill and Copse Collei | The Ascension Talent Floral Sidewinder is changed to this: The Floral Ring will grant the character the Sprout effect from Floral Sidewinder upon return, dealing 40% of Collei's ATK as Dendro DMG to nearby opponents for 3s. From the moment of using Floral Brush to the moment when this instance of Sprout effect ends, if any of your party members triggers Burning , Quicken , Aggravate , Spread , Bloom , Hyperbloom , Lunar-Bloom , or Burgeon reactions, the Sprout effect will be extended by 3s. The Sprout effect can only be extended this way once. If another Sprout effect is triggered during its initial duration, the initial effect will be removed. You must first unlock the Ascension Talent "Floral Sidewinder." | 2 |
| Withering Glimpsed in the Leaves Tighnari | When Fashioner's Tanglevine Shaft is unleashed, all nearby party members gain 60 Elemental Mastery for 8s. If the Fashioner's Tanglevine Shaft triggers a Burning , Bloom , Lunar-Bloom , Quicken , or Spread reaction, their Elemental Mastery will be further increased by 60. This latter case will also refresh the buff state's duration. | 4 |
| Austerity: Forbidding Guard Cyno | Before Enhancement After Enhancement (Revelation) When Cyno is in the Pactsworn Pathclearer state triggered by Sacred Rite: Wolf's Swiftness , after he triggers an Electro-Charged , Lunar-Charged , Superconduct , Stellar-Conduct , Overloaded , Quicken , Aggravate , Hyperbloom , or an Electro Swirl reaction, he will restore 3 Elemental Energy for all nearby party members (except himself.) This effect can occur 5 times within one use of Sacred Rite: Wolf's Swiftness. When Cyno is in the Pactsworn Pathclearer state triggered by Sacred Rite: Wolf's Swiftness , after he triggers an Electro-Charged , Lunar-Charged , Superconduct , Stellar-Conduct , Overloaded , Quicken , Aggravate , Hyperbloom , or an Electro Swirl reaction, he will restore 3 Elemental Energy to all nearby party members (except himself). This effect can occur 5 times within one use of Sacred Rite: Wolf's Swiftness. When other characters affected by Together We Rise trigger the aforementioned reaction, they will also regenerate 20 Elemental Energy for Cyno. This effect can trigger once every 18s. | 4 |
| Skiving: New and Improved Sayu | Sayu recovers 1.2 Energy when she triggers a Swirl reaction. This effect occurs once every 2s. | 4 |
| Flower and a Fighter Yun Jin | When Yun Jin triggers Crystallize or Lunar-Crystallize reactions, her DEF is increased by 20% for 12s. | 4 |
| The Root of All Fullness Nahida | Opponents that are marked by Seeds of Skandha applied by Nahida herself will be affected by the following effects: Burning , Bloom , Hyperbloom , and Burgeon Reaction DMG they receive can score CRIT Hits . CRIT Rate and CRIT DMG are fixed at 20% and 100% respectively. CRIT Rate from this effect stacks with CRIT Rate from similar effects that allow these Elemental Reactions to CRIT. Within 8s of being affected by Quicken , Aggravate , or Spread , DEF is decreased by 30%. The CRIT Rate and CRIT DMG of Lunar-Bloom DMG received are increased by 10% and 20% respectively. | 2 |
| Dance of the Snowy Moon and Flute Freminet | After Freminet triggers Frozen , Shatter , or Superconduct against opponents, his ATK will be increased by 9% for 6s. Max 2 stacks. This can be triggered once every 0.3s. | 4 |
| Vigilant Sentinel Illuga | After Illuga triggers a Geo-related Reaction on the field, he will regain 12 Elemental Energy. This effect can be triggered at most once every 15s. | 1 |

There are 5 Constellations that have special effects which enhance certain Elemental Reactions:

| Constellation | Description | Level |
|---|---|---|
| Prophecy of Submersion Mona | Before Enhancement After Enhancement (Hexerei) When any of your own party members hits an opponent affected by an Omen, the effects of Hydro-related Elemental Reactions are enhanced for 8s: Electro-Charged DMG increases by 15%. Lunar-Charged DMG increases by 15%. Vaporize DMG increases by 15%. Hydro Swirl DMG increases by 15%. Lunar-Crystallize DMG increases by 15%. Frozen duration is extended by 15%. When any of your own party members hits an opponent affected by an Omen, the effects of Hydro-related Elemental Reactions are enhanced for 8s: Electro-Charged DMG increases by 15%. Lunar-Charged DMG increases by 15%. Vaporize DMG increases by 15%. Hydro Swirl DMG increases by 15%. Lunar-Crystallize DMG increases by 15%. Frozen duration is extended by 15%. Additionally, when your off-field party members trigger the above effect, the DMG Bonus to the above Hydro-related Elemental Reactions is enhanced to 160% of its original effect. | 1 |
| The Root of All Fullness Nahida | Opponents that are marked by Seeds of Skandha applied by Nahida herself will be affected by the following effects: Burning , Bloom , Hyperbloom , and Burgeon Reaction DMG they receive can score CRIT Hits . CRIT Rate and CRIT DMG are fixed at 20% and 100% respectively. CRIT Rate from this effect stacks with CRIT Rate from similar effects that allow these Elemental Reactions to CRIT. Within 8s of being affected by Quicken , Aggravate , or Spread , DEF is decreased by 30%. The CRIT Rate and CRIT DMG of Lunar-Bloom DMG received are increased by 10% and 20% respectively. | 2 |
| Pairidaeza's Dreams Kaveh | When Kaveh's Normal, Charged, or Plunging Attacks hit opponents during Painted Dome , they will unleash Pairidaeza's Light upon the opponent's position, dealing 61.8% of Kaveh's ATK as AoE Dendro DMG and causing all Dendro Cores within that AoE to burst. This effect can be triggered once every 3s. | 6 |
| The Heart Lingers Long Yumemizuki Mizuki | Before Enhancement After Enhancement (Revelation) While Yumemizuki Mizuki is in the Dreamdrifter state, Swirl DMG dealt by nearby party members can Crit, with CRIT Rate fixed at 30%, and CRIT DMG fixed at 100%. While Yumemizuki Mizuki is in the Dreamdrifter state, Swirl DMG dealt by nearby party members can score CRIT Hits, with CRIT Rate fixed at 30%, and CRIT DMG fixed at 100%. Every point of Elemental Mastery Yumemizuki Mizuki has in excess of 500 increases her CRIT Rate by 0.04% and her CRIT DMG by 0.16%. Yumemizuki Mizuki's CRIT Rate and CRIT DMG can be increased by up to 20% and 80% in this way, respectively. | 6 |
| Feast of Apadana Kaveh | Dendro Cores created from Bloom and Lunar-Bloom reactions Kaveh triggers will deal 60% more DMG when they burst. | 4 |


## Weapons

9 Weapons have special effects when an Elemental Reaction is triggered:

| Icon | Name | Quality | Base ATK (Lv. 1) | 2nd Stat (Lv. 1) | Passive Ability |
|---|---|---|---|---|---|
|  | Freedom-Sworn | 5 Stars | 608 (46) | Elemental Mastery 198 (43) | Revolutionary Chorale A part of the "Millennial Movement" that wanders amidst the winds. Increases DMG by 10 ~ 20 %. When the character wielding this weapon triggers Elemental Reactions, they gain a Sigil of Rebellion. This effect can be triggered once every 0.5s and can be triggered even if said character is not on the field. When you possess 2 Sigils of Rebellion, all of them will be consumed and all nearby party members will obtain "Millennial Movement: Song of Resistance" for 12s. "Millennial Movement: Song of Resistance" increases Normal, Charged, and Plunging Attack DMG by 16 ~ 32 % and increases ATK by 20 ~ 40 %. Once this effect is triggered, you will not gain Sigils of Rebellion for 20s. Of the many effects of the "Millennial Movement," buffs of the same type will not stack. |
|  | Forest Regalia | 4 Stars | 565 (44) | Energy Recharge 30.6% (6.7%) | Forest Sanctuary After triggering Burning , Quicken , Aggravate , Spread , Bloom , Lunar-Bloom , Hyperbloom , or Burgeon , a Leaf of Consciousness will be created around the character for a maximum of 10s. When picked up, the Leaf will grant the character 60 ~ 120 Elemental Mastery for 12s. Only 1 Leaf can be generated this way every 20s. This effect can still be triggered if the character is not on the field. The Leaf of Consciousness' effect cannot stack. |
|  | Fruit of Fulfillment | 4 Stars | 510 (42) | Energy Recharge 45.9% (10.0%) | Full Circle Obtain the "Wax and Wane" effect after an Elemental Reaction is triggered, gaining 24 ~ 36 Elemental Mastery while losing 5% ATK . For every 0.3s, 1 stack of Wax and Wane can be gained. Max 5 stacks. For every 6s that go by without an Elemental Reaction being triggered, 1 stack will be lost. This effect can be triggered even when the character is off-field. |
|  | Hakushin Ring | 4 Stars | 565 (44) | Energy Recharge 30.6% (6.7%) | Sakura Saiguu After the character equipped with this weapon triggers an Electro elemental reaction, nearby party members of an Elemental Type involved in the elemental reaction receive a 10 ~ 20 % Elemental DMG Bonus for their element, lasting 6s. Elemental Bonuses gained in this way cannot be stacked. |
|  | Mappa Mare | 4 Stars | 565 (44) | Elemental Mastery 110 (24) | Infusion Scroll Triggering an Elemental reaction grants a 8 ~ 16 % Elemental DMG Bonus for 10s. Max 2 stacks. |
|  | Moonpiercer | 4 Stars | 565 (44) | Elemental Mastery 110 (24) | Stillwood Moonshadow After triggering Burning , Quicken , Aggravate , Spread , Bloom , Lunar-Bloom , Hyperbloom , or Burgeon , a Leaf of Revival will be created around the character for a maximum of 10s. When picked up, the Leaf will grant the character 16 ~ 32 % ATK for 12s. Only 1 Leaf can be generated this way every 20s. This effect can still be triggered if the character is not on the field. |
|  | Sapwood Blade | 4 Stars | 565 (44) | Energy Recharge 30.6% (6.7%) | Forest Sanctuary After triggering Burning , Quicken , Aggravate , Spread , Bloom , Lunar-Bloom , Hyperbloom , or Burgeon , a Leaf of Consciousness will be created around the character for a maximum of 10s. When picked up, the Leaf will grant the character 60 ~ 120 Elemental Mastery for 12s. Only 1 Leaf can be generated this way every 20s. This effect can still be triggered if the character is not on the field. The Leaf of Consciousness' effect cannot stack. |
|  | Dark Iron Sword | 3 Stars | 401 (39) | Elemental Mastery 141 (31) | Overloaded Upon causing an Overloaded , Superconduct , Stellar-Conduct , Electro-Charged , Quicken , Aggravate , Hyperbloom , Lunar-Charged , or Electro-infused Swirl reaction, ATK is increased by 20 ~ ? % for 12s. |
|  | Emerald Orb | 3 Stars | 448 (40) | Elemental Mastery 94 (20) | Rapids Upon causing a Vaporize , Electro-Charged , Frozen , Bloom , Lunar-Charged , Lunar-Bloom , or a Hydro-infused Swirl reaction, ATK is increased by 20 ~ 40 % for 12s. |


## Artifacts

7 Artifact Sets have special effects when an Elemental Reaction is triggered:

| Set | Rarity | Pieces | Bonuses |
|---|---|---|---|
| Instructor | 3-4★ |  | 2-Piece: Increases Elemental Mastery by 80. 4-Piece: Upon triggering an Elemental Reaction , increases all party members' Elemental Mastery by 120 for 8s. |
| Viridescent Venerer | 4-5★ |  | 2-Piece: Anemo DMG Bonus +15% 4-Piece: Increases Swirl Reaction DMG dealt by 60%, and Stellar Swirl reaction DMG dealt by 20%. Decreases opponent's Elemental RES to the element infused in the Swirl by 40% for 10s. Upon triggering a Stellar Swirl in the opponent, will also decrease their Cryo RES by 40%. RES debuffs of the same elemental type do not stack. |
| Archaic Petra | 4-5★ |  | 2-Piece: Geo DMG Bonus +15%. 4-Piece: Upon obtaining an Elemental Shard created through Crystallize or triggering a Lunar-Crystallize reaction, all party members gain 35% DMG Bonus for that particular element for 10s. Only one form of Elemental DMG Bonus can be gained in this manner at any one time. |
| Thundering Fury | 4-5★ |  | 2-Piece: Electro DMG Bonus +15% 4-Piece: Increases the DMG caused by Overloaded , Electro-Charged , Superconduct , and Hyperbloom by 40%, the DMG Bonus conferred by Aggravate by 20%, and the DMG caused by Lunar-Charged and Stellar-Conduct by 20%. When Quicken or the aforementioned Elemental Reactions are triggered, Elemental Skill CD is decreased by 1s. Can only occur once every 0.8s. |
| Gilded Dreams | 4-5★ |  | 2-Piece: Increases Elemental Mastery by 80. 4-Piece: Within 8s of triggering an Elemental Reaction , the character equipping this will obtain buffs based on the Elemental Type of the other party members. ATK is increased by 14% for each party member whose Elemental Type is the same as the equipping character, and Elemental Mastery is increased by 50 for every party member with a different Elemental Type. Each of the aforementioned buffs will count up to 3 characters. This effect can be triggered once every 8s. The character who equips this can still trigger its effects when not on the field. |
| Flower of Paradise Lost | 4-5★ |  | 2-Piece: Increases Elemental Mastery by 80. 4-Piece: The equipping character's Bloom , Hyperbloom , and Burgeon reaction DMG are increased by 40%, and their Lunar-Bloom reaction DMG is increased by 10%. Additionally, after the equipping character triggers Bloom, Hyperbloom, Lunar-Bloom, or Burgeon, they will gain another 25% bonus to the effect mentioned prior. Each stack of this lasts 10s. Max 4 stacks simultaneously. This effect can only be triggered once per second. The character who equips this can still trigger its effects when not on the field. |
| Nighttime Whispers in the Echoing Woods | 4-5★ |  | 2-Piece: ATK +18%. 4-Piece: After using an Elemental Skill , gain a 20% Geo DMG Bonus for 10s. When under a shield granted by the Crystallize reaction, or when Moondrifts formed by Lunar-Crystallize reactions are nearby, the above effect will be increased by 150%. When these conditions are no longer met, this additional increase disappears after 1s. |

1 Artifact Set have special effects that enhance certain Elemental Reactions:

| Set | Rarity | Pieces | Bonuses |
|---|---|---|---|
| Flower of Paradise Lost | 4-5★ |  | 2-Piece: Increases Elemental Mastery by 80. 4-Piece: The equipping character's Bloom , Hyperbloom , and Burgeon reaction DMG are increased by 40%, and their Lunar-Bloom reaction DMG is increased by 10%. Additionally, after the equipping character triggers Bloom, Hyperbloom, Lunar-Bloom, or Burgeon, they will gain another 25% bonus to the effect mentioned prior. Each stack of this lasts 10s. Max 4 stacks simultaneously. This effect can only be triggered once per second. The character who equips this can still trigger its effects when not on the field. |


## Elemental Resonance

Main article: Elemental Resonance

Some resonances have special effects when an Elemental Reaction is triggered.

- High Voltage : Superconduct, Overloaded, Electro-Charged, Quicken, Aggravate, or Hyperbloom have a 100% chance to generate an Electro Elemental Particle
- Sprawling Greenery : After triggering Burning, Quicken, or Bloom reactions, all nearby party members gain 30 Elemental Mastery for 6s. After triggering Aggravate, Spread, Hyperbloom, or Burgeon reactions, all nearby party members gain 20 Elemental Mastery for 6s.


## Achievements

There are 2 Achievement Categories that contain Achievements related to elemental reactions:

- Elemental Specialist: Series I
- Elemental Specialist: Series II


## Trivia

- The design of the Elemental Reaction system was established long before combat strategy and numerical planning. It was designed to support gameplay interaction, forming a set of modular, intuitive, and easy-to-understand rules for players to engage with.


## Change History

Released in Version 1.0

[ Edit History ]

Version 7.0

- Added Stellar Swirl .

Version "Luna VIII"

- Added Stellar-Conduct .

Version "Luna IV"

- Added Lunar-Crystallize .

Version "Luna I"

- Added Lunar-Bloom .

Version 5.8

- Added Lunar-Charged .

Version 5.2

- Increased DMG multipliers of the following Elemental Reactions: Superconduct: 0.5 to 1.5 Electro-Charged: 1.2 to 2 Overloaded: 2 to 2.75 Shatter: 1.5 to 3
- Superconduct: 0.5 to 1.5
- Electro-Charged: 1.2 to 2
- Overloaded: 2 to 2.75
- Shatter: 1.5 to 3

Version 3.0

- Added: Bloom Hyperbloom Burgeon Quicken Aggravate Spread
- Bloom
- Hyperbloom
- Burgeon
- Quicken
- Aggravate
- Spread

Version 1.6

- Increases the damage caused by Electro-Charged, Superconduct, Overloaded, Swirl, and Shatter above Level 60; increases damage from Elemental Mastery; and increases Base Shield strength from Crystallize-based shields.

Version 1.0

- Elemental Reactions were released with: Burning Crystallize Electro-Charged Frozen Melt Overloaded Superconduct Swirl Vaporize Shatter
- Burning
- Crystallize
- Electro-Charged
- Frozen
- Melt
- Overloaded
- Superconduct
- Swirl
- Vaporize
- Shatter


## Glossary

Polestar Field: When Stellar-Conduct is triggered, the surrounding area will transform into a Polestar Field for a short period of time, and when inside a Polestar Field, certain characters will enter the Radiance: Stellar-Conduct state, which grants various skill buffs
