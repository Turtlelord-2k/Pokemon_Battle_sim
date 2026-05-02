# Pokemon Battle Simulator + AI Agents

A turn-based Pokemon battle simulator written in Python, plus a collection of AI trainers (Greedy, Smart-Greedy, Minimax, Alpha-Beta pruning) that play 6v6 matches against a human opponent. Mechanics roughly follow the main-series games (Gen 1–4 Pokemon, Gen 6-style damage formula) at a fixed Level 50 with default stats.

The simulator covers the core combat loop in detail: 18 types, STAB, critical hits, accuracy/evasion, status conditions (burn / poison / bad poison / paralysis / sleep / freeze / confusion / curse / flinch), stat-stage changes, recoil, healing, weight-based moves, multi-hit attacks, recharge moves, OHKO moves, fixed-damage moves, and many other per-move special effects.

---

## Project Structure

```text
.
├── pokemonsim.py          # Main simulator: Pokemon, Trainer (with AI), battle loops
├── pokemon.json           # Stats / types / weights for every Pokemon (used by name/ID)
├── moves.json             # Move data: power, accuracy, type, damage class, effect ID, priority
├── types.json             # Full type effectiveness chart (offense + defense)
├── supported_moves.csv    # List of moves whose effects are explicitly handled
├── __init__.py            # Gym registration scaffold (RL env placeholder)
└── envs/                  # Gym environment scaffold (not yet wired to the simulator)
    ├── __init__.py
    ├── custom_env.py
    └── pokgame.py
```

> Note: `envs/` is an early scaffold for an OpenAI Gym RL environment. The current `pokgame.py` is a placeholder template and is not yet connected to `pokemonsim.py`.

---

## Requirements

- Python 3.8+
- `numpy`

Install with:

```bash
pip install numpy
```

(`gym` is only needed if you intend to extend the `envs/` RL scaffold; it is not required to run battles.)

---

## How to Run

From the project root:

```bash
python pokemonsim.py
```

You will be prompted at each turn to either fight (then pick a move 1–4) or switch Pokemon. Battles run in the terminal with delayed text for readability.

### Choosing a battle mode

The bottom of `pokemonsim.py` has a set of boolean flags that select which mode runs. Set exactly one to `True`:

```python
greedy      = False   # Bot always picks highest base-power move
smartgreedy = False   # Bot picks move with highest expected damage (uses calculate_damage)
baseCode    = False   # Plain 6v6 where both sides choose moves manually
minimax     = False   # Bot uses depth-limited minimax search
alphabeta   = True    # Bot uses minimax with alpha-beta pruning (default)
```

You can also run a quick 1v1 test by uncommenting the line near the bottom:

```python
p1.fight(p2)
```

…and editing `p1` / `p2` to any two `Pokemon` objects.

### Building teams

Pre-built sample Pokemon are defined near the bottom of `pokemonsim.py`. Each is constructed as:

```python
Charizard = Pokemon('6', ['89', '394', '337', '411'])
#                    ^id   ^four moves (IDs from moves.json)
```

Teams are just Python lists of up to 6 Pokemon:

```python
team1 = [Marshtomp, Mewtwo, Golem, Blastoise, Beedrill, Pidgeot]
team2 = [Deoxys, Lugia, Lucario, Rayquaza, Dragonite, Charizard]
```

To build your own Pokemon, look up its dex number in `pokemon.json` and the IDs of the 4 moves you want in `moves.json`. Only moves listed in `supported_moves.csv` have their special effects implemented; other moves will still deal damage but skip their secondary effects.

---

## AI Agents

All agents live on the `Trainer` class. Each one exposes a `*fight(Trainer2)` entry point that mirrors the manual `fight` loop but replaces the opponent's decision with the agent's policy.

| Agent           | Method              | Strategy                                                                                                                              |
|-----------------|---------------------|---------------------------------------------------------------------------------------------------------------------------------------|
| Manual          | `fight`             | Both sides input moves manually (baseline reference).                                                                                 |
| Greedy          | `greedyfight`       | Always picks the move with the highest **base power**. Ignores types and effects.                                                     |
| Smart Greedy    | `smartgreedyfight`  | Picks the move with the highest **expected damage** via `calculate_damage` (factors in STAB, type effectiveness, attacker/defender stats). |
| Minimax         | `minimaxfight`      | Depth-limited minimax over move choices, scored by `evaluate(...)` which weights HP diff, dealt damage, status, stat totals, faints, and type effectiveness. |
| Alpha-Beta      | `alphabetafight`    | Same evaluation as Minimax, but with alpha-beta pruning for deeper search at the same cost.                                           |

Search depth defaults to `5` and is configurable per-Trainer:

```python
ashketchum = Trainer(team2, 'Ash', depth=5)
```

The bots currently always send out the next available Pokemon on faint (no smart switching yet) and never voluntarily switch; only the human player has full switch control.

---

## Implemented Battle Mechanics

- **Stats** auto-converted from base stats to Level 50 (0 EV / 0 IV) values.
- **Damage formula** with STAB (1.5×), critical hits (~3.5% base, 12.5% on high-crit moves, 100% on guaranteed-crit moves), 0.85–1.0 random factor, burn halving physical attack, type effectiveness, and `damage_class` (physical / special / non-damaging) routing.
- **Status conditions:** burn, poison, bad poison (escalating), paralysis (with speed cut), sleep (1–3 turn counter), freeze (defrost on fire moves or 20% chance), confusion (2–5 turns + self-hit), flinch, curse.
- **Stat stages** from −6 to +6 with the standard multiplier table; accuracy uses its own multiplier table.
- **Special move effects:** recoil (1/4, 1/3, 1/2), recoil-on-miss (jump kicks), healing moves (50% / 75% / damage-based), self-destruct, OHKO, fixed-damage (Dragon Rage, Sonic Boom, Seismic Toss), Endeavor, Flail / Reversal scaling, Acrobatics, Brine, Facade, Foul Play, Hex, Venoshock, Stored Power, Wake-Up Slap, Eruption / Water Spout, weight-based moves (Low Kick, Heat Crash family), tri-attack random status, recharge moves (Hyper Beam etc.), Belly Drum, Curse, Swagger / Flatter, multi-hit moves (2-hit and 2–5-hit), Struggle, immunity-respecting status moves.
- **Turn order** based on move priority, then modified speed, with a 50/50 coin flip on speed ties.

See `supported_moves.csv` for the complete list of moves with handled effects.

---

## Type ID Reference

All types use IDs 1–18 throughout the JSON files:

| ID | Type     | ID | Type     | ID | Type     |
|----|----------|----|----------|----|----------|
| 1  | Normal   | 7  | Bug      | 13 | Electric |
| 2  | Fighting | 8  | Ghost    | 14 | Psychic  |
| 3  | Flying   | 9  | Steel    | 15 | Ice      |
| 4  | Poison   | 10 | Fire     | 16 | Dragon   |
| 5  | Ground   | 11 | Water    | 17 | Dark     |
| 6  | Rock     | 12 | Grass    | 18 | Fairy    |

---

## Status Update Log

```text
December 21: Added Minimax (and alpha-beta pruning) agent to Trainer class
July 9:      Added effects for recharging moves / tri-attack / curse / dragon rage / sonic boom; added bad-poison mechanics
July 8:      Implemented various moves and move effects for semi-common moves
July 7:      Finished 6v6 implementation (battle testing). Updated input/output interface
July 6:      Implemented Trainer class and switch-in functions / checks
June 30:     Lots of testing on stat and status moves; fixed healing / crit and accuracy bugs; added self-destructing move mechanics; expanded sample Pokemon for 6v6 prep; added supported_moves.csv
June 29:     Added non-damaging stat moves and non-damaging status moves; fixed bugs for STAB, healing, and stat condition lists
June 24:     1v1 battling works (some move effects still missing). Added more Pokemon. Level 50 stats now auto-calculated
June 23 II:  Status moves and stat-boosting moves fully implemented; basic 1v1 should be complete
June 23:     Added confusion, Acrobatics / Struggle mechanics, recoil-on-miss
June 22:     Added critical hits, status condition mechanics, updated turn structuring
June 19:     Updated special / physical distinguishment and damage calculation
```

---

## TODO

- Hook up `envs/` to expose a real Gym environment around `pokemonsim.py` for RL training.
- Smarter switching for AI agents (currently always defaults to slot 1 on faint and never voluntarily switches).
- Charging moves (Sky Attack, Solar Beam), locked-in moves (Outrage), and switching moves (U-turn, Baton Pass, Roar, Dragon Tail) — not yet implemented.
- Optional ability to start a battle from an arbitrary game state (useful for AI rollouts).
- Optional logging of game progress to file / variables for offline analysis.
- General code / structure / documentation cleanup.

## To Test

- Random 6v6 game mechanics that may have been missed.
- Newly added move effects.

---

## Credits

- Data files (`pokemon.json`, `moves.json`, `types.json`) are based on data from [fonse/pokemon-battle](https://github.com/fonse/pokemon-battle).
- The original turn-based battling skeleton and class layout was inspired by [cesaralvrz/Pokemon-Battle-Simulator](https://github.com/cesaralvrz/Pokemon-Battle-Simulator).
- Stat and damage calculations use Level 50 / 0 EV / 0 IV defaults, rounded down.
