# Simulator repair plan

Status: proposed implementation plan, 20 September 2026. No simulator rewrite is implemented by this document. This plan supersedes conflicting older generated plans; their rule descriptions are references to verify, not authoritative requirements.

## Agreed product and player contract

- Four automated players; simulate the entire match before independent browser replay. No human game decisions or live streaming requirement.
- Use Player terminology for user implementations; distinguish participant/display name, seat ID and implementation version.
- One persistent Player instance per seat per match, including when the same implementation occupies several seats.
- `choose_action(view, options) -> Action` is the only decision method, also used for setup, discards, robber choices, development-card resolution and decisions outside the player's own turn.
- `on_event(event) -> None` is separate and invoked for every event visible to the player. It may be implemented as a no-op. Events are not passed as an argument to choose_action.
- Optional default-no-op start/end lifecycle hooks. Start receives initial player context; end receives the structured result after final events.
- Trade is a generic available action. The player constructs recipients/give/receive; the engine does not enumerate possible trade offers.
- One deterministic response round per proposal: recipients accept/reject/counter, then proposer selects one executable agreement or cancels. No counter-to-counter recursion. Fresh proposals may follow.
- Random terrain with prescribed sequential number-token placement, skipping desert. Define traversal and starting-player policy explicitly in the versioned rules configuration.

## Boundaries and target structure

Keep a standalone Python simulation library with no FastAPI, SQLAlchemy, room or browser dependency. Consolidate the current simulation/simulator naming during migration rather than retain two apparent engine packages.

Logical modules (not a requirement for many small classes):

1. Public player SDK: Player base class, immutable observations, IDs, decision contexts, action and event schemas, protocol version, example implementation.
2. Board/domain: immutable geometry, authoritative mutable match state, bank and player holdings, seeded RNG and versioned configuration.
3. Rules: legal-option queries and validated atomic transitions. Generation and application share predicates; callers cannot bypass turn/phase restrictions.
4. Engine: explicit decision state machine, current acting seat, sequencing, lifecycle and termination. `step()` resolves one decision/transition; `run()` drives it to a terminal result.
5. Events/recording: ordered canonical events, visibility projections, public replay snapshots, decision audit records and result export.
6. Execution adapters: direct trusted local Player adapter and persistent process adapter with identical semantics. Packaging and process management stay outside game rules.
7. Platform: rooms, uploads, version selection, jobs, persistence and replay HTTP endpoints.

The engine owns all randomness affecting rules and all state mutations. Views/events are detached immutable values; no raw GameState escapes. A player's memory belongs to that player's instance.

## Event semantics

After a valid atomic transition, commit state, record its events, then dispatch filtered events in sequence order and canonical recipient order. Finish delivery before requesting the next decision. Callbacks cannot return actions or reenter the engine; their only normal side effect is private player memory. No concurrent callbacks against the same instance.

Public events cover setup, turn boundaries, dice, exact resource production, construction, trade proposals/responses/cancellation/completion, bank trades, development-card purchase occurrence and public plays, robber movement, theft occurrence, discard counts, achievements and game completion. Private variants disclose own card draws, own discards and stolen-card identity only to entitled players. Opponent hidden VP and hand contents never enter public views. Unknown visibility values fail closed.

Apply execution budgets to both event and action callbacks. Record faults without allowing a broken subscriber to interrupt committed state or starve other players. The recording observer is independent of player callbacks. Public replay and internal audit data are distinct outputs.

## Implementation sequence and completion criteria

### 1. Freeze schemas and establish a trustworthy test baseline

Define PlayerView (public board, own hand, public opponent counts/scores, separate game/turn/decision phases), typed action variants, decision IDs, event visibility, result statuses and versioning. Use concrete legal choices for board locations and constrained selections for combinatorial decisions such as discards. A Trade action contains a player-defined offer. Separate player trading from maritime exchange semantics.

Deliver a minimal stateful Player example and API tests proving events precede decisions, one API handles every decision context, and separate instances do not share memory. Preserve existing replay/browser contract tests. Replace tests that encode known broken behavior instead of optimizing for the existing test count. Verify standard-rule details against the selected official base-game rules before encoding them; older specs contain mistakes.

### 2. Replace geometry and fix setup

Build real 19-hex/54-vertex/72-unique-edge topology, six corners per tile, reciprocal adjacency, coastal edges and nine correctly typed ports (four generic and five resource-specific). Define stable IDs and display coordinates. Implement configured terrain/token setup, seeded seat order policy, snake placements and second-settlement resource transfers from bank.

Acceptance: exact topology invariants, valid ports, reproducible setup, distance rule, adjoining initial road, correct acting player and conserved resource/piece totals.

### 3. Establish authoritative rule transactions

Centralize resource transfers and piece accounting; validate all payloads and quantities before changing state. Share legality between options and execution. Fix road connectivity, opponent blocking, settlement connection and city piece return. Account for bank shortages and development deck exhaustion. Reject wrong-seat, wrong-phase, stale, unknown and post-terminal actions without mutation.

Acceptance: legal actions succeed; illegal actions leave state and event history unchanged; resource/deck/piece invariants hold after every transition. No negative quantities or caller-chosen bank ratios.

### 4. Implement the complete decision state machine

Setup -> pre-roll -> roll -> production or discard/robber resolution -> repeated post-roll decisions -> turn end. Development plays and trades create explicit pending decision contexts and return to the correct phase. Include legal pre-roll card behavior, mandatory rolling, per-turn flags and exact acting-seat selection.

Replace eight-turn execution with termination on legal victory, configured limit, player failure or engine failure. Return structured results; enforce bounded turns, decisions and negotiation activity to stop pathological games. Limits are operational safeguards, not a two-build/two-trade game rule.

Acceptance: integration scenarios traverse all phases, cannot skip required decisions and stop without additional actions after completion.

### 5. Complete robber, cards, trading and scoring

- Seven: correct discard threshold/count and return to bank; robber relocation and adjacent eligible victim selection; sample individual cards uniformly for theft.
- Development cards: purchase-turn tracking, standard per-turn active-card limit, pre-roll continuation, validated Knight resolution, sequential free-road legality/piece limits, correct Year of Plenty quantities including duplicate resources and shortages, Monopoly and hidden VP.
- Maritime trades: derive legal ratios from occupied ports and validate exchange quantities.
- Player trades: generic Trade capability, positive integer resource offers, valid distinct recipients, one public response round, proposer selection, atomic final revalidation and no unilateral transfers. Acceptance of the original offer is allowed only when executable; counters must offer resources the responding player can provide.
- Scores: correct longest edge-trail with branches/loops/opponent blocking, achievement incumbent/tie rules, largest army and victory timing, final score disclosure policy.

Acceptance: focused rule scenarios plus multi-turn games where players build, trade, play cards and actually win. Freeze exact bank-shortage and final-disclosure behavior in tests after rule verification.

### 6. Make player execution consistent and bounded

Ship an SDK and loader so authors implement a Player class; a platform-owned adapter handles wire serialization. Keep one process and one player instance alive per seat per match, with version handshake and ordered request/event messages. Do not require authors to hand-write a JSON script protocol. Route every decision and lifecycle/event callback through the same adapter semantics.

Validate packages with import/instantiate/protocol smoke tests, not compilation alone. Bound message sizes, logs, callback time and total match usage; terminate process trees on failure. Record the exact fault and apply a documented deterministic policy. Proposed default: abort a competitive match with a player-failure result rather than silently replace an entrant's strategy; allow explicit demo fallback mode. A failed process's memory is not assumed recoverable.

Process separation alone is not a security sandbox. Before external untrusted submissions, enforce filesystem/network/CPU/memory/process restrictions in an appropriate OS/container worker. Local trusted play can use the direct adapter. Choose deployment-specific isolation separately from the core SDK.

Acceptance: stateful player behaves consistently through local/process adapters; invalid JSON, exceptions, infinite callbacks and child processes cannot hang the match service; failure statuses are visible.

### 7. Integrate native recording and the existing platform

Replace RecordingSimulator method interception with a supported engine observer/export contract. Record public snapshots at committed transitions plus ordered public events, result, geometry, seed, player version hashes, rules/engine/protocol versions and accepted decisions in an appropriately restricted audit record. Keep the web replay schema compatible or explicitly version it and retain old-reader support.

The backend freezes entrant versions, launches an isolated match job and persists its final artifact. Migrate new jobs away from CPU work in API threads; start with a simple subprocess worker, without requiring a distributed queue. Keep the existing room -> simulate -> watch flow and independent browser playback.

Current persistence is split: rooms and implementations in SQLite; match metadata and recordings in JSON files. During integration, choose one authoritative match catalog (recommended: SQLite metadata referencing replay files), import existing JSON metadata without deleting recordings, and reconcile interrupted jobs. Do not persist each in-game resource mutation through SQL.

Acceptance: room match produces a real completed game, survives restart as a replay, renders pieces on actual geometry, supports seeking without rerunning players, and never serves internal/private logs through public replay endpoints.

### 8. Final acceptance and cleanup

Run invariant/property scenarios, cross-process seeded reproducibility with deterministic players, recorded-decision reproduction, multi-seed end-to-end matches, failure isolation tests and browser replay checks. State that arbitrary author code and wall-clock timeouts can be nondeterministic; seed alone is not a universal reproducibility guarantee.

Remove superseded engine/transport paths only after replacements are in use. Update terminology, SDK documentation and examples. Preserve existing saved replays and uploaded versions; label old implementations incompatible where an honest automatic adapter is impossible. Authentication/public hosting is a separate platform task, not implied by simulator completion.

## End-state acceptance

A friend writes a Player implementation with choose_action and optional-no-op on_event, tests it locally, submits an immutable version, joins a room and runs a full legal match. It receives all permitted events before decisions, can keep private memory and negotiate trades, cannot inspect other hands or mutate state, and has clear fault handling. The completed recording can be watched independently after the server restarts. The engine can also run headlessly with no web server or database.
