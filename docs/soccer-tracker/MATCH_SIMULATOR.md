# Match Simulator & Player Skills: build spec for Soccer Tracker

> Drop this file into the Soccer Tracker repo (suggested path: `docs/MATCH_SIMULATOR.md`) and ask Claude:
> *"Read docs/MATCH_SIMULATOR.md and build Phase 1. Fit it to this app's existing stack, data and line-up board."*
> Build one phase at a time and play with each before starting the next.

> **Part of the wider platform:** see `docs/PLATFORM.md`. There, player skills come from **measured assessments**
> (PLATFORM §3.2–3.3, the test battery turned into 1–10 through age-group bands, with coach overrides). Opponents come
> from **scouting notes** built up over meetings (PLATFORM §3.7). Build the platform's Phase 1 (assessments) before this
> simulator, so the engine runs on real data from day one.

## 1. What we're building, and for whom

A coaching tool inside Soccer Tracker. The team manager or coach:

1. rates each **real player's** skills (strong foot, weak foot, defending, striking, goalkeeping and so on);
2. puts them on the pitch in a **formation**, using the line-up board the app already has;
3. sets **tactics** (pressing, defensive line, width, passing style);
4. describes the **opposition**, in detail or in four quick sliders;
5. **runs simulated matches**: watches one play out, or runs 200 in a second for the odds;
6. gets **plain-English coaching advice**, for example: *"Most goals you concede come down your left. Your left back is slower than their right winger. Try your quicker defender there, or keep your left midfielder back."*

The main users are **parent coaches and inexperienced coaches of junior teams**. Every screen should teach as well as calculate. Explain terms in plain words, give advice rather than raw numbers, and keep the default view simple.

### Honest framing (show this in the app)
- A simulation is a **thinking tool, not a prediction**. Its value is comparing *your own* options against the same opponent ("4-3-3 vs 3-4-3"), not forecasting a score.
- The output is only as good as the ratings, so keep them rough and update them as players develop.
- Kids change fast. Build in a quick "re-rate" habit, for example a prompt each half-season.

## 2. Child-safety and privacy rules (non-negotiable)

The players are minors, so:
- **Ratings are coach-only.** Never show them to players or parents by default, never on a public screen, and never in a shareable link without an explicit coach action.
- Call them "development profile" and "strengths / working on", not "rating" or "rank". Never show a team-wide ranked list of kids.
- Store the minimum: first name or nickname, ratings, preferred foot and positions. Photos only with parental consent, if the app already has a consent flow.
- Let the coach export and delete a player's data in one tap.
- Keep it on the device, or behind the app's existing authenticated backend. No third-party analytics on this data.

## 3. Player skills

Two levels over the same data. **Simple mode** is the default and shows the 7 headline sliders. **Advanced mode** reveals the detail. When the coach moves a headline slider, it sets all its detail values together. Editing a detail value marks that headline as "custom".

All values run 1 to 10, where 5 is average for this age group. Use 1–10, not 1–100: coaches can't tell a 63 from a 67.

| Headline (simple) | Detail attributes (advanced) |
|---|---|
| ⚡ **Pace** | pace (top speed), acceleration, agility |
| 🎯 **Passing** | short passing, long passing, crossing, vision |
| ⚽ **Striking** | finishing, shot power, long shots, heading |
| 🌀 **Dribbling** | dribbling, first touch, ball control under pressure |
| 🛡 **Defending** | tackling, marking, interceptions, defensive positioning |
| 💪 **Engine** | stamina, strength, work rate |
| 🧤 **Goalkeeping** | handling, reflexes, GK positioning, distribution, 1v1 / rushing out |

Plus:
- **Preferred foot:** Left / Right / Both.
- **Weak-foot ability:** 1–5. It scales passing, shooting and dribbling when the ball is on the weak side.
- **Composure / decisions:** 1–10. This controls how often the player picks the *best* option rather than a random reasonable one (see §6.3). It's important, and coaches understand it: "makes good choices".
- **Positions:** each position gets a comfort level of natural, OK or unfamiliar. Playing out of position applies a small penalty to positioning and decisions.
- **Notes** and **"working on"** tags (free text). These are never used by the engine, only for development tracking.

### Player card UI
- A card per player: name, number, foot icon, and a mini radar (spider chart) of the 7 headlines.
- Tap the card to see the sliders. Each slider has a one-line explanation, e.g. *Defending: wins the ball back and stays goal-side of their player.*
- "Copy from…" lets you start from another player or from an archetype (Speedy winger, Rock at the back, Playmaker, Goal poacher, Sweeper keeper).

### Where the numbers come from
Ratings come from the latest assessment snapshot (measured), with any coach override layered on top (marked as coach).
The sliders on the player card edit the **override**, never the measured value. The UI always shows which is which, and the date of the snapshot.

## 4. Opposition

Offer two ways to describe the other team:
- **Quick:** four team sliders (Attack, Midfield, Defence, Keeper, each 1–10), plus a **style**: Pressing / Possession / Long ball / Counter-attack / Park the bus. The engine fills a squad from these with some spread, so they aren't all identical.
- **Detailed:** a full opposition squad with the same player cards, saved per opponent and reused next season.

Opponent profiles are generated from the scouting notes (PLATFORM §3.7): team sliders plus **named key players by shirt number**, with their tags (fast, left-footed, tall, dangerous shooter…) turned into attributes. The coach can tweak these before simulating. Each fixture remembers its opponent. After a real match, the coach can note what actually happened ("they had two very fast wingers") and adjust.

## 5. Formats, formations and tactics

### Formats
| Format | Players | Typical pitch (m) | Match length |
|---|---|---|---|
| 5v5 / futsal style | 4 + GK | 30 × 20 | 2 × 15 min |
| 7v7 | 6 + GK | 50 × 35 | 2 × 20 min |
| 9v9 | 8 + GK | 70 × 45 | 2 × 25 min |
| 11v11 | 10 + GK | 100 × 65 | 2 × 30–45 min |

Make these configurable to the club's age-group rules. Also make **offside on/off** configurable: many junior formats have none or a retreat line.

### Formations
Store each formation as **slots with normalised coordinates**: x across the pitch from 0 to 1, y up the pitch from 0 (own goal) to 1. Each slot has a role. Ship sensible presets per format, for example:
- 7v7: 2-3-1, 3-2-1, 2-1-2-1, 3-1-2
- 9v9: 3-2-3, 3-3-2, 2-4-2
- 11v11: 4-4-2, 4-3-3, 4-2-3-1, 3-5-2

The existing line-up board drags real players into slots. Coaches can also drag slots to make custom formations.

Each slot has **two positions**:
- **In possession:** how the shape looks when we have the ball. It's wider and higher, with full-backs pushing on.
- **Out of possession:** how it looks when they have the ball. It's compact and goal-side.

The board shows both, with a toggle and a ghost of the other.

### Roles (per slot)
Give each slot a role, each with a short description:
- Goalkeeper / Sweeper keeper
- Centre back / Ball-playing CB
- Full back / Wing back (attacking)
- Holding mid / Box-to-box / Playmaker
- Winger (stay wide) / Inside forward (cut in)
- Target striker / Runner in behind / False 9

Roles change the engine's behaviour weights in §6.

### Team tactics (sliders with plain-language ends)
| Slider | Low end ↔ High end |
|---|---|
| Defensive line | Deep, protect the goal ↔ High, squeeze the space |
| Pressing | Sit back and stay in shape ↔ Chase the ball everywhere |
| Width | Narrow and compact ↔ Stretch the pitch |
| Tempo | Patient, keep the ball ↔ Quick, get forward fast |
| Passing | Short passes ↔ Long balls over the top |
| After losing the ball | Fall back into shape ↔ Win it back immediately (counter-press) |
| After winning the ball | Build up calmly ↔ Counter-attack fast |

Also include set-piece choices (corners: near post / far post / short) and a **substitutions plan**, so it can simulate rotating kids for equal game time, which is a big deal in junior football.

## 6. The simulation engine

A deterministic, seedable 2D agent simulation, independent of the UI so it can run in a Web Worker. Pure functions, no DOM.

### 6.1 Units and loop
- The pitch is in metres, sized to the format. Time steps at 10 ticks a second (dt = 0.1 s), which is enough for decisions. Render-side interpolation smooths playback.
- A **seeded RNG** (e.g. mulberry32) means the same seed and inputs give the same match. That's essential for "A vs B" comparisons and for tests.
- One full 11v11 match should take **under about 150 ms** headless on a phone, so 200 sims finish in about 30 s in a worker. Smaller formats are much faster. Measure this and optimise only if needed.

### 6.2 State
```ts
type Vec = { x: number; y: number };
interface SimPlayer {
  id: string; team: 0 | 1; slot: number; role: Role;
  pos: Vec; vel: Vec; stamina: number;            // stamina 0..1, drains with sprinting
  attrs: Attributes;                               // §3, already adjusted for position comfort
}
interface Ball { pos: Vec; vel: Vec; height: number; owner: string | null; lastTouch: string | null }
interface MatchState {
  t: number; half: 1 | 2; score: [number, number];
  phase: 'kickoff' | 'open' | 'goalKick' | 'corner' | 'throwIn' | 'freeKick';
  possession: 0 | 1 | null; players: SimPlayer[]; ball: Ball; events: MatchEvent[]; rng: () => number;
}
```

### 6.3 Each tick
1. **Team state:** in possession, out of possession, or transition (the first ~3 s after the ball changes hands, when the "after losing / winning" tactics apply).
2. **Off-ball movement.** Every player without the ball heads for a **target point**:
   - The slot's in- or out-of-possession anchor, scaled to the pitch.
   - Shifted toward the ball side (block shift).
   - Pushed up or down by the defensive-line slider, and widened or narrowed by width.
   - Plus role behaviours: a runner in behind makes runs past the last defender; wing backs overlap when the ball is wide on their side; a holding mid stays between the ball and goal.
   - Defenders out of possession pick a mark (nearest attacker in their zone) and stay goal-side of them. The nearest one or two (more with high pressing) close down the ball carrier.
   - Speed toward the target comes from pace and acceleration, scaled down by low stamina.
3. **On-ball decision.** Only the ball carrier decides, every 0.3–0.6 s or when pressured. Score each option and pick one:
   - **Pass** to each teammate: open space around them, progress up the pitch, the risk that a defender intercepts the pass line, distance against passing range, and the tempo and passing-style sliders.
   - **Dribble** forward or into space: the carrier's dribbling against how close defenders are.
   - **Shoot:** expected-goal value from distance, angle and pressure, against the role's "shot appetite".
   - **Clear / long ball:** when under heavy pressure in their own third.

   Selection uses a softmax over the option scores. **Composure / decisions** sets the temperature: high composure nearly always takes the best option, low composure is noisier. This one parameter makes skill differences *visible* and believable.
4. **Execution** (where skills matter most):
   - **Pass accuracy:**
     - base = passing skill
     - minus distance and pressure penalties
     - × the weak-foot factor if the ball is on the weak side (ball relative to body and pass direction)
     - The pass's actual direction gets an angular error drawn from a normal distribution whose spread shrinks with accuracy.
   - **Interception:** any defender whose path can reach the ball's line in time tries it, with probability from interceptions and anticipation.
   - **Duel (tackle):** compare the attacker's (dribbling, pace, strength, composure) against the defender's (tackling, positioning, strength), plus a random term. The outcome is ball won, ball lost, or a foul. The foul chance rises with low tackling and high pressing.
   - **Shot:**
     - On-target probability comes from finishing, weak foot and pressure.
     - Power comes from shot power.
     - Saved or goal is decided by placement (corner vs central) against the keeper's reflexes, positioning, and 1v1 skill if the keeper rushed out.
     - A save can parry the ball loose, which creates a second-ball chance.
   - **First touch:** receiving under pressure can miscontrol, more often with low first touch.
5. **Ball physics:** rolling friction, out of play (throw-in, corner, goal kick), posts, and simple aerial balls with height for crosses and headers.
6. **Events:** log every pass (from, to, success), shot (xG, outcome), tackle, interception, foul, set piece and goal. Every stat and insight is computed from this log.

### 6.4 Restarts and rules
Kick-offs, throw-ins, corners, goal kicks, free kicks (direct shot or pass), and half-time with a side switch. Offside follows the configured rules.

### 6.5 Calibration (do this before trusting any advice)
Add tests that run many seeded sims and assert that the engine behaves like football:
- Two identical teams: wins about equal (within ±5% over 500 sims) and draws common.
- One team +2 on every headline: wins clearly more (e.g. above 60%).
- Goals per match fall in a realistic range for the format, for example 2–6 total in 7v7 juniors.
- Possession in the 35–65% range in most matches, unless the styles are extreme.
- Weak-foot test: a winger with weak foot 1, forced onto the weak side, scores and assists noticeably less.
- Pressing high against a team with low composure produces more turnovers in their half.

Expose a hidden **developer calibration panel** with the global constants (pass error scale, xG curve, tackle odds) so the model can be tuned without code changes. Lock it behind an admin passcode, the same idea as the Tower Defence tuning screen in Little-Jimmy.

## 7. Modes the coach can use

1. **Watch a match:**
   - A top-down animated pitch using the app's existing pitch look.
   - Speed controls: 1×, 4×, 16× and skip to end.
   - Pause and **drag a player** to see what changes ("what if our left back stood here?").
   - Event ticker: "12' ⚽ Mia scores, assist Jack."
2. **Quick odds:** run N matches (default 200) and show win/draw/loss %, average score, shots and possession.
3. **Compare A vs B:** two line-ups or tactic sets against the same opponent with the same seeds, which makes the comparison fair. Example result: *"3-2-1 wins 46% vs 2-3-1 38%: it concedes 0.8 fewer goals but scores 0.3 fewer."*
4. **Scenarios / drills:** short starts from a set situation, for coaching moments:
   - Defending a 3v2 counter
   - Playing out from the goal kick against a high press
   - Defending corners
   - Breaking down a team that sits deep
5. **Game-time planner:** simulate the substitution plan to check every player gets fair minutes and the team stays balanced on the pitch at all times.

## 8. Reports and coaching insights

Compute everything from the event log:
- **Heatmaps** per player and per team.
- **Pass network:** who passes to whom; arrow thickness shows count.
- **Where goals and shots come from:** zones, and which flank.
- **Player involvement:** touches, passes completed, duels won.
- **Danger map:** where we lose the ball, and how often that leads to a shot against.

**Insight rules** turn the numbers into plain advice. Each rule fires only when the evidence is strong (enough sims, a big enough effect) and says *why*:
- Flank mismatch: concede down a side and that full back's pace is ≥3 below the winger's → suggest a swap, a covering midfielder, or a deeper line.
- Possession lost in our own third under a press, with low passing at the back → suggest more long balls when pressed, or a ball-playing CB in that slot.
- Lots of shots but few goals, with low striking in the forwards → suggest a different striker or more cutbacks (shots from closer in).
- Wide players never receive the ball → width is set too narrow, or no one is passing out wide.
- Late goals conceded with low stamina → suggest a substitution plan.
- A player out of position → "Sam is playing as a winger but is natural at centre back."

Use plain words, positive framing and one action per tip. Link each tip to a "try it" button that applies the change and re-runs the comparison.

## 9. Data model (JSON)

```jsonc
// player profile (coach-only)
{ "id": "p_mia", "name": "Mia", "number": 7, "foot": "L", "weakFoot": 3,
  "headline": { "pace": 8, "passing": 6, "striking": 7, "dribbling": 7, "defending": 3, "engine": 6, "goalkeeping": 2 },
  "detail": { "acceleration": 8, "finishing": 7, "shotPower": 6, "tackling": 3, "...": 0 },   // optional; falls back to headline
  "composure": 6, "positions": { "LW": "natural", "ST": "ok", "LB": "unfamiliar" },
  "workingOn": ["weak foot", "tracking back"], "updatedAt": "2026-10-18" }

// formation
{ "id": "7v7_3-2-1", "format": "7v7", "name": "3-2-1",
  "slots": [ { "role": "GK", "in": [0.5, 0.04], "out": [0.5, 0.03] },
             { "role": "CB", "in": [0.5, 0.25], "out": [0.5, 0.18] } /* … */ ] }

// tactics
{ "line": 0.5, "press": 0.6, "width": 0.7, "tempo": 0.5, "direct": 0.3, "counterPress": 0.5, "counterAttack": 0.7,
  "corners": "far", "subs": [ { "minute": 15, "off": "p_jack", "on": "p_sam" } ] }

// opponent (quick form)
{ "id": "o_rovers", "name": "Rovers U11", "attack": 7, "midfield": 5, "defence": 6, "keeper": 5, "style": "counter" }

// sim request / result (Web Worker message)
{ "home": { "players": [], "formation": "", "tactics": {} }, "away": {}, "format": "7v7", "runs": 200, "seed": 12345 }
{ "wins": 0.46, "draws": 0.2, "losses": 0.34, "avgFor": 2.1, "avgAgainst": 1.6, "shots": [], "zones": {}, "insights": [] }
```

## 10. Build phases

**Phase 1: skills and data (no simulation yet).**
- Player skill cards: simple mode, radar, archetypes, foot, positions.
- Coach-only storage, export and delete.
- Opposition (quick form).
- *Done when* a coach can rate the squad in under 10 minutes.

**Phase 2: engine core plus quick odds.**
- Engine §6.1–6.4 in a Web Worker, with seeded RNG and the calibration tests in §6.5 passing.
- Quick odds mode.
- *Done when* the calibration tests pass and 200 7v7 sims finish in under 30 s on a mid-range phone.

**Phase 3: watch mode.**
- Animated pitch, speed controls, event ticker, and pause-and-drag "what if".
- Reuse the line-up board for the starting positions.

**Phase 4: tactics and formations.**
- In/out-of-possession shapes, roles, tactic sliders, and A vs B compare.

**Phase 5: coaching insights and reports.**
- Heatmaps, pass network, danger map, insight rules with "try it".

**Phase 6: scenarios, game-time planner, detailed opposition, advanced attributes, admin calibration panel.**

Keep each phase shippable, and get real coach feedback before moving on.

## 11. Ideas that carry over from the Little-Jimmy games
- **Pocket Soccer** (`soccer.html`) shows drag-to-move players on a phone with an offset so the finger doesn't cover the player, a 2D/3D pitch renderer, and host-authoritative multiplayer. The drag handling and rendering approach are worth borrowing.
- **Don't reuse its physics.** Pocket Soccer players are square "paddles" built for arcade fun; this needs the agent model above.
- **Tower Defence's tuning screen** (`tower-defence.html`, 🎛) is the pattern for the calibration panel: sliders as multipliers, saved per device, with an admin passcode.
