# Soccer Tracker: the team platform (build spec)

> Put this in the Soccer Tracker repo as `docs/PLATFORM.md`, next to `docs/MATCH_SIMULATOR.md`, which is the match
> simulator module this platform feeds. Ask Claude: *"Read docs/PLATFORM.md and build Phase 1, fitted to this app's
> stack."* One phase at a time.

## 1. The idea in one paragraph

One app for the team manager and coaches of a junior side, covering the whole season:
- Plan and run **every training night of the season**: the exercises, timings and equipment, adapting as the season goes. This is the **development program**.
- **Assess** every child with simple, repeatable tests, and turn the results into a **skills matrix** (a snapshot in time, and the trend over the season).
- Work out **which positions suit each child**, and compare that with **where they want to play**.
- **Scout** each opposition team, then use that data in the **match simulator** to set up the best structure for the next meeting.
- Keep **schedules, attendance, match stats, reports** and **parent communication** in one place.

The coach's **home dashboard** pulls it together: what's on, who's available, who needs assessing, and what the data says to work on.

## 2. Ground rules (they shape every module)

1. **Kids' data, handled like it.** The players are minors.
   - Assessments, ratings, position-fit scores and coach notes are **coach-only** by default.
   - Parents see **their own child's progress only**, framed positively ("strengths / working on / improved since last term").
   - Parents **never** see another child's data or any ranking.
   - Get parental consent at sign-up. Store the minimum, and support export and delete per child.
   - Australia: follow the Privacy Act, plus the state association's / Football Australia's safeguarding and member-protection policies. Check the current versions with your club: [Inference] I don't have the exact policy names or versions.
2. **Development first.** Wording, colours and reports should celebrate personal improvement over comparison. A 9-year-old's "3/10 speed" is a starting point, not a label.
3. **Pitch-side reality.** It's used on a phone, outdoors, often with poor signal. It needs to work offline and sync later, with big tap targets and as little typing as possible.
4. **Roles and permissions** from day one:

| Role | Can see / do |
|---|---|
| Team manager / head coach | Everything for the team; manages coaches and parents |
| Assistant coach | Everything except settings, deleting players and parent contact details (configurable) |
| Parent / guardian | Own child's schedule, availability, RSVP, announcements, own child's development report |
| Player | Nothing by default. An optional limited view for older age groups, decided by the club |

## 3. Modules

### 3.1 Squad
- Player profile: name, nickname, number, date of birth (gives the age group), preferred foot, **preferred positions** (the player's own choice, up to 3, ranked), medical notes and emergency contact (coach-only, encrypted), parent/guardian links, and consent flags.
- Status: available / injured / unavailable, with a return date.

### 3.2 Assessments: the test battery
Short, repeatable, low-equipment tests run on a training night in stations. Every test has a **protocol card** in the app: setup diagram, cones and distances, how to score, and a 20-second explanation to read to the kids. That way any parent helper can run a station.

Suggested starter battery (configurable; the club can add or remove tests):

| Area | Test | Measures | Score |
|---|---|---|---|
| Speed | 20 m sprint (flying or standing start, best of 2) | pace | seconds |
| Agility | 5-10-5 shuttle | agility / change of direction | seconds |
| Endurance | 6-minute run, or a multistage beep test (older groups) | stamina | metres / level |
| Passing **R** | Wall pass: completed passes in 30 s, right foot, from 3 m | short passing (right) | count |
| Passing **L** | Same, left foot | short passing (left) | count |
| Dribbling **R/L** | Cone slalom using only the right, then only the left | dribbling per foot | seconds |
| Shooting **R/L** | 5 shots per foot at target zones from the edge of the box | finishing per foot | points |
| First touch | Receive a thrown or served ball and control it in a box: 10 tries | first touch | successes |
| Juggling | Best of 2 attempts | ball control | count |
| 1v1 defending | Small-grid duels against rotating attackers | defending | wins / attempts |
| Goalkeeping | Catches from served balls, low dives each side, distribution to a target | GK attributes | points |

Plus **coach observation scores** (1–10, with descriptors) for things that are hard to test: decisions, positioning, work rate, communication, composure.

**Recording UX:**
- Station mode lists the kids at that station. Tap a child, then enter the time or count, with a built-in stopwatch and tap counter.
- It works offline.
- One assessment *session* (date, test set) is a snapshot.

**From raw results to 1–10:**
- Each test maps to the simulator's attributes (see MATCH_SIMULATOR.md §3) through **age-group bands**: tables saying, for example, U10 20 m sprint 3.6 s = 8/10.
- Ship sensible starter bands, **clearly marked as starting guesses**, and let the club edit them. Optionally, recalculate bands from the club's own data once there's enough of it (percentiles within the age group).
- **Weak foot** = the left/right ratio on the per-foot tests, mapped to the 1–5 weak-foot rating automatically.
- The coach can override any derived rating. Overrides are marked and kept separately from measured values.

### 3.3 The skills matrix (the snapshot)
- **Team matrix:** players are rows and attributes are columns, with colour-banded cells (development colours, e.g. blues and greens, not red for "bad").
  - Sort and filter by attribute.
  - Toggle between **measured**, **coach-adjusted** and **change since last snapshot** (↑↓).
  - The column averages give team strengths and gaps, which feed training planning.
- **Player view:**
  - A radar chart of the current snapshot against the previous one.
  - A trend line per test over the season.
  - "Strengths" (top 3) and "Working on" (coach-chosen, linked to drills).
- **Snapshots** are immutable once closed, so the history stays honest.

### 3.4 Position fit vs preferred position
- **Position profiles:** each position (GK, CB, FB/WB, DM, CM, AM, Winger, Striker; scaled per format) is a weighted mix of attributes. For example, Winger = pace 30%, dribbling 25%, crossing 15%, stamina 15%, weak foot 5%, decisions 10%. The club can edit the profiles.
- **Fit score:** the weighted sum of a player's attributes, plus a footedness bonus for side positions (e.g. left-footed on the left for a full back; inverted wingers optional).
- **Per player:**
  - Their **top 3 suggested positions** with the fit %.
  - Their **preferred positions**, side by side.
  - A small "**gap to preferred**" panel: which attributes hold back their preferred position, and the drills that build them.
  - This is a development conversation starter, not a verdict.
- **Team view:** a grid of positions × players showing fit. It highlights cover gaps ("only one natural left-sided defender") and a suggested best XI per formation, which feeds the line-up board.
- **Fair play:** a toggle to weight the suggestions toward rotating kids through positions they want and through equal minutes, as the club's junior policy may require.

### 3.5 Season training planner: what's done every night, all season

The coach plans the **whole season once**, at a high level. The app fills in every training night with actual exercises,
timings and equipment, and then **keeps adapting the plan** as assessments, attendance and match results come in.
On the night, the coach opens one screen and runs the session from it.

#### 3.5.1 Building blocks
- **Season** → **blocks** (usually a school term or 4–6 weeks) → **weeks** → **sessions** (each training night) → **segments** → **drills**.
- **Season setup:**
  - start and end dates
  - training nights (e.g. Tue and Thu, 5:00–6:15 pm)
  - venue and field
  - match day
  - school holidays and public holidays to skip
  - number of coaches and parent helpers usually available
  - equipment the club has (cones, bibs, balls, mini goals, poles, ladders)
- **Blocks** have a **theme** and **targets**, e.g.
  - Block 1: "Ball mastery and first touch"
  - Block 2: "Weak foot and passing"
  - Block 3: "1v1 attacking and defending"
  - Block 4: "Playing out from the back and team shape"

  Each block ends with a **re-assessment session** (§3.2), so progress is measured.
- **Session template** (segments with default minutes, for a 75-minute night, all editable):
  1. Arrival activity / free play: 5–10 min. Kids start the moment they arrive.
  2. Warm-up with the ball (movement, agility, injury prevention): 10 min
  3. **Technical** focus (the block theme): 15–20 min
  4. **Small-sided game** built around the theme: 15–20 min
  5. **Match game** (free play, the theme encouraged): 15–20 min
  6. Cool-down and a 2-minute team talk: 5 min

  Age-group defaults differ. Younger groups get more play and shorter technical blocks.
  - [Inference] Football Australia's national curriculum describes age phases: a Discovery phase for the youngest, Skill Acquisition, then Game Training.
  - Check the current curriculum and align the templates and drill tags to it.

#### 3.5.2 The drill library
Each drill has:
- name and a diagram (a simple pitch drawing: cones, players, arrows)
- setup and equipment
- players needed (min / ideal / max)
- area size and duration
- age suitability
- **target attributes** (e.g. weak-foot passing, first touch)
- intensity (low / medium / high)
- coaching points (3 short bullets)
- progressions (make it harder) and regressions (make it easier)
- "what good looks like"
- optional video link

Coaches can create, copy and edit drills, and share them with other teams in the club.

**Content:** ship a starter library of about 40 drills written for this app, or use the club's own resources. Don't copy drills, diagrams or text from copyrighted coaching books or paid sites.

#### 3.5.3 Auto-generating the season
From the season setup, the block themes and the **team skills matrix** (§3.3), the planner fills every session:
- **Balance across the block:**
  - The block theme dominates the technical and small-sided segments.
  - Each week also touches the team's **biggest gaps** from the matrix (e.g. low weak-foot passing).
  - Nothing repeats so often that kids get bored: a variety rule such as "no drill more than twice in 3 weeks unless it's a favourite".
- **Progression:** drills step up through their progressions as the block goes on (week 1 regression → week 4 progression).
- **Load:** intensity is spread across the week, with a lighter session the night before a match, and stays age-appropriate.
- **Fit to resources:**
  - Each drill is checked against expected numbers, coaches and equipment.
  - Station rotations are generated when there are enough helpers.
- **Fixed dates:** skip holidays, add the assessment nights at the end of each block, and leave a pre-season "fun" session and an end-of-season "parents vs kids" night (optional).
- **Output:** every training night has a full session plan the coach can review and edit. Locked sessions are never auto-changed.

#### 3.5.4 Adapting during the season
After each week, the planner proposes changes for the **upcoming** sessions. The coach approves them; it never silently rewrites:
- **New assessment results:** shift emphasis toward new gaps, and recognise improved areas.
- **Match notes and stats:** e.g. "conceded 3 goals from crosses" adds a crossing/heading-defence drill next week. "Next opponent presses high" (from scouting, §3.7) adds a playing-out-under-pressure game.
- **Attendance:**
  - If expected numbers drop, swap in drills that work with fewer players.
  - A child who missed key sessions gets a short **catch-up note**: home practice suggestions for their family.
- **Cancellations** (rain, field closed):
  - One tap moves or cancels the session and notifies parents (§3.9).
  - The block's key content reflows into the following sessions.
- **Coach feedback:** after a session, rate it (👍/👎 per drill, "too hard / just right / too easy"). That steers future picks.

#### 3.5.5 On the night: run-sheet mode
- A phone screen showing the **current segment and drill** with its diagram and coaching points, a **countdown timer**, and **what's next**.
  - It vibrates or chimes at changeovers.
  - It works offline.
- **Equipment checklist** before leaving home, and a **setup map** if several drills share the field.
- **Station rotation board:** which group is at which station, who runs it, and rotate on the timer. Parent helpers can open a read-only link to their station's card.
- **Roll call** at the start (§3.5.6). Tap players into groups or bibs (auto-balanced by the skills matrix if wanted).
- Quick **per-player notes** with a few taps ("great weak-foot passing tonight"), which feed the development record.
- An **after-session reflection** of 30 seconds: what worked, ratings for each drill.

#### 3.5.6 Attendance, home practice and sharing
- Roll call and attendance history per player. Attendance % appears on the dashboard and in reports.
- **Home practice:** each week, an optional 10-minute "homework" card per child, based on their "working on" focus (e.g. 50 left-foot wall passes). Parents see it in their view. Kids or parents can tick it off.
- **Print / share:**
  - Season overview (one page per block).
  - Weekly plan PDF for assistant coaches.
  - Session cards for parent helpers.

### 3.6 Match day
- Availability from the RSVPs, then the line-up from the board (existing), using the suggested XI from §3.4.
- **Live logging:** goals, assists, shots, saves, subs (minutes played are tracked automatically), injuries and cards. Big buttons, offline.
- An **equal-minutes tracker** that warns when a child is under their fair share.
- Post-match: result, coach's notes, player of the match (optional, and handled kindly), and lessons learned that feed the next session plan.

### 3.7 Opposition scouting
After each game against a team, the coach records:
- Their **formation(s)** and style (pressing / possession / long ball / counter / deep block).
- **Key players by shirt number:** quick tags like ⚡ fast, 🦶 left-footed, 📏 tall, 🎯 dangerous shooter, 🧱 strong defender, 🧤 good keeper, 🔁 tires late. An optional 1–10 per area.
- **Team strengths and weaknesses** (tags plus a free note), set-piece habits, and the result and score.

Notes **build up across meetings**, with a "last updated" date. When you play them again, the app builds the **opponent profile** for the simulator: the quick sliders (attack / midfield / defence / keeper, plus style) and **named key players** with their tags turned into attributes. The coach can then run **Compare A vs B** (MATCH_SIMULATOR.md §7) to pick the best structure for that opponent.

Keep it respectful: these are other people's kids. Shirt numbers and football traits only, no names or photos.

### 3.8 Statistics and reports
- **Team:** results, goals for and against, where goals come from and are conceded, clean sheets, attendance %, and minutes distribution.
- **Player:** minutes, goals, assists, saves, attendance, assessment trend, and positions played.
- **Reports** (PDF or share):
  - A **parent development report** per child: own progress only, strengths, working on, a positive coach comment, and the next term's focus.
  - A **season report** for the club.
  - **Coach handover** notes for next season's coach (with consent).

### 3.9 Communication
See the recommendation in §5 before building any of this.
- **Announcements:** coach to all parents. Schedule changes, cancellations ("training off: wet field"), reminders.
- **RSVP and availability** for training and matches.
- **Group chat:** only if the club wants it, and only with safeguards built in:
  - no private adult-to-child messages
  - parents and coaches only
  - every thread visible to at least two adults from the club
  - moderation and reporting
  - a retention policy

### 3.10 Coach dashboard (home screen)
- **Next up:** tonight's training or Saturday's match, RSVP count, weather.
- **Squad status:** available, injured, missing RSVPs.
- **To do:** assessments due, minutes imbalance, unscouted next opponent, overdue development reports.
- **Insights:** the top 3 data-driven tips, e.g. "Team weak-foot passing is the biggest gap (avg 4.2): this week's session plan is built around it."
- **Season at a glance:** results, the attendance trend, and the team matrix change since the last snapshot.

## 4. Data model (outline)

```jsonc
Team { id, name, ageGroup, format, season, coaches[], settings{ bands, positionProfiles, policies } }
Player { id, teamId, name, nickname, number, dob, foot, preferredPositions[], status, consent{}, guardians[] }
Guardian { id, name, contact, playerIds[] }                      // contact details: coach-only
AssessmentSession { id, teamId, date, tests[], closed }           // a snapshot
TestResult { sessionId, playerId, testId, raw, foot?: 'L'|'R', recordedBy }
Rating { playerId, sessionId, attr, value1to10, source: 'measured'|'coach' }
PositionFit { playerId, sessionId, position, score }              // derived, cached
Event { id, teamId, type: 'training'|'match'|'other', start, end, venue, recurrence? }
Attendance { eventId, playerId, status }   RSVP { eventId, playerId, status, by }
Season { id, teamId, start, end, trainingNights[{ weekday, start, end, venue }], matchDay, blackouts[], resources{ coaches, helpers, equipment[] } }
Block { id, seasonId, name, theme, targetAttrs[], start, end, assessmentSessionId? }
SessionTemplate { id, ageGroup, minutes, segments[{ kind: 'arrival'|'warmup'|'technical'|'ssg'|'game'|'cooldown', minutes }] }
SessionPlan { eventId, blockId, locked, segments[{ kind, minutes, drillId, groups?, stationLead? }], equipment[], notes, generatedBy: 'auto'|'coach' }
Drill { id, name, diagram, setup, equipment[], players{ min, ideal, max }, area, minutes, ageMin, ageMax, targetAttrs[], intensity,
        points[], progressions[], regressions[], videoUrl?, ownerTeamId, sharedWithClub }
DrillFeedback { eventId, drillId, rating: 'up'|'down', difficulty: 'hard'|'right'|'easy', note? }
PlanChange { id, weekStart, reason: 'assessment'|'match'|'scouting'|'attendance'|'cancellation'|'feedback', proposed[], status: 'pending'|'approved'|'rejected' }
HomePractice { playerId, weekStart, drillId, done }
Match { eventId, opponentId, formationId, lineup[], subs[], events[], result, notes }
Opponent { id, name, club, meetings[]: { matchId, formation, style, keyPlayers[{ number, tags[], ratings? }], strengths[], weaknesses[], notes } }
Announcement { id, teamId, text, sentAt, audience }
```

## 5. Recommendations (build order and what *not* to build)

**Build in this order.** Each phase is useful on its own, so you get value from week one.
1. **Squad and assessments:**
   - Players, test battery, station recording (offline), snapshot, team matrix, player radar.
   - *Done when:* a training night can assess 15 kids across 6 stations with parent helpers, and the matrix appears that night.
2. **Position fit vs preferred:** profiles, fit scores, gap-to-preferred, team cover grid.
3. **Season training planner:** a starter drill library, season setup and blocks, session templates, auto-generated session plans for every night, and **run-sheet mode** with a timer (§3.5.1–3.5.3, 3.5.5).
   *Done when:* the coach can set up a season in about 15 minutes and every training night has a usable plan. Then add the weekly adaptation, feedback and home practice (§3.5.4, 3.5.6).
4. **Match day:** availability, line-up, live logging, minutes tracker, post-match notes.
5. **Opposition scouting, then the simulator** (MATCH_SIMULATOR.md phases 1–5, using the measured attributes from step 1).
6. **Stats, reports and the dashboard.**
7. **Communication:** announcements and RSVP first. Chat last, if at all.

**Don't build parent chat yourself, at least not early.**
- [Inference] Chat is the most expensive and riskiest part. Real-time infrastructure, notifications, moderation and safeguarding duties around minors all come with it, and parents already use WhatsApp, Spond, TeamApp or similar.
- Build announcements and RSVP (high value, low risk), and link out to the group chat the team already uses. Revisit only if the club insists, and then with the safeguards in §3.9.

**Backend:**
- [Inference] As soon as there's more than one coach, or parents log in, you need a real backend: authentication, roles, row-level security so a parent can only read their own child, encrypted medical fields and backups. A hosted service with built-in auth and row-level security, such as Supabase or Firebase, is the usual shortcut.
- Use whatever Soccer Tracker already runs on, if that covers these.

**Validate with real use early.** Run the Phase 1 assessment night with your team before building further. The band tables and test choices will change once you see real kids doing them.
