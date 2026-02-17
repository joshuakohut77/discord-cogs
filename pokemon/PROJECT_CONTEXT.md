# Pokemon Discord Bot - Project Context Summary

**Last Updated:** 2026-02-17

## Project Overview

**Repository:** https://github.com/joshuakohut77/discord-cogs.git
**Working Directory:** `/home/legend/Documents/GitHub/discord-cogs/pokemon`
**Running Bot Directory:** `/home/legend/claude/docker/data/cogs/CogManager/cogs/pokemon`
**Framework:** Red-DiscordBot v3.5.22 with Discord.py v2.6.3
**Language:** Python 3.11
**Database:** PostgreSQL (postgres_container)
**Sprite Server:** nginx:alpine at https://pokesprites.joshkohut.com/sprites/

---

## Project Structure

```
discord-cogs/pokemon/
├── configs/                    # JSON configuration files
│   ├── gyms.json              # Gym leaders, trainers, requirements, badges
│   ├── quests.json            # Quest data, pre-requisites, blockers
│   ├── locations.json         # Location data, connections, gym flags
│   ├── pokemon.json           # Pokemon stats, types, moves, evolution data
│   ├── moves.json             # Move data: power, accuracy, type, stat_change, stat_change_secondary, special functions
│   ├── typeEffectiveness.json # Type matchup multipliers
│   └── enemyTrainers.json     # Wild route trainers keyed by location ID
│
├── services/                   # Backend service classes
│   ├── battleclass.py         # Gym battle progression, victory/defeat tracking, finale_unlocked flag
│   ├── encounterclass.py      # Core battle mechanics, damage calc, battle_fight() with stat stages & special moves
│   ├── trainerclass.py        # Trainer data management, useItem(), evolveItem(), quest(), gift()
│   ├── locationclass.py       # Location management, encounter methods, area details
│   ├── questclass.py          # Quest system, locationBlocked(), quest rewards, easter eggs, create_key_item_embed()
│   ├── keyitemsclass.py       # Key items (badges, HMs, fossils, easter egg items)
│   ├── pokeclass.py           # Pokemon class: stats, moves, evolution, shiny support, sprites
│   ├── ailmentsclass.py       # Status ailments (burn, poison, freeze, sleep, confusion, paralysis)
│   ├── shinyclass.py          # Shiny Pokemon roll logic and sprite URL generation
│   ├── pokedexclass.py        # Pokedex registration and tracking
│   ├── leaderboardclass.py    # Stats tracking: victories, defeats, catches, evolutions, easter eggs, trades, completions
│   ├── storeclass.py          # PokeMart buy/sell logic for all items, stones, TMs
│   ├── inventoryclass.py      # Inventory management with TM01-TM50 support, link cable, game shark
│   ├── uniqueencounterclass.py# Unique/gift Pokemon tracking (Mew, Porygon, etc.)
│   ├── dbclass.py             # Database connection handler (host: postgres_container)
│   └── loggerclass.py         # Logging utility
│
├── models/                     # Data models
│   ├── __init__.py
│   ├── battlestate.py         # BattleState (gym/trainer), WildBattleState (wild encounters)
│   ├── sessionstate.py        # ActionState, BagState, ItemUsageState, MartState
│   └── state.py               # DisplayCard enum for trainer card views
│
├── helpers/                    # Helper utilities
│   ├── __init__.py            # Re-exports getTrainerGivenPokemonName, specialmoves, statstages
│   ├── helpers.py             # getTrainerGivenPokemonName (nickname or species name)
│   ├── pathhelpers.py         # get_config_path(), load_json_config() (cached), get_sprite_path()
│   ├── decorators.py          # Session validation decorators (@require_*_state)
│   ├── statstages.py          # StatStages class, apply_stat_change(), apply_secondary_stat_change(), get_modified_stat()
│   └── specialmoves.py        # handle_rest, handle_recover, calculate_drain_heal, night_shade, leech_seed, haze, dream_eater, check_accuracy
│
├── finale/                     # Cinematic post-game finale system
│   ├── __init__.py            # Exports FinaleEngine, FinaleRenderer, FinaleAudioManager, scene types
│   ├── engine.py              # FinaleEngine state machine, FinaleBattleState, scene progression
│   ├── renderer.py            # PIL-based image rendering for dialog, battles, transitions, finale screens
│   ├── audio.py               # FinaleAudioManager for voice channel audio playback (FFmpeg)
│   ├── scenes.py              # Dataclasses: DialogScene, BattleStartScene, BattleCutsceneScene, TransitionScene, FinaleScene, CutsceneTrigger
│   ├── views.py               # FinaleDialogView, FinaleBattleView, FinaleDefeatView, FinaleSwitchView
│   ├── script.py              # Full storyboard: Skippy's Challenge & Chodethulu (Acts 1-3)
│   ├── custom_pokemon.py      # FinalePokemon class (mimics PokemonClass interface from config)
│   └── pokemon_config.json    # Custom finale Pokemon with custom moves, stats, sprites
│
├── sprites/                    # Local sprite assets
│   ├── pokemon/               # Pokemon sprites (front/back)
│   ├── trainers/              # Trainer/NPC sprites
│   ├── items/                 # Item sprites
│   ├── finale/                # Finale-specific assets
│   │   ├── backgrounds/       # Scene backgrounds
│   │   ├── characters/        # Character sprites (Skippy, Chodethulu, etc.)
│   │   ├── fonts/             # Custom fonts for rendering
│   │   └── audio/             # Music tracks (intro.mp3, battle themes, etc.)
│   └── map/                   # Map images
│
├── encounters.py              # Main encounter/battle mixin (~8000+ lines) - wild encounters, gym battles, manual/auto battles, items, catching
├── finalemixin.py             # Finale mixin - manages finale engine, all battle modes, audio, scene rendering
├── achievements.py            # Achievement system mixin - badge, capture milestone, elite_four, first_evolution, easter_egg announcements
├── leaderboard.py             # Leaderboard display mixin - global rankings, personal stats
├── map.py                     # Map navigation mixin - direction buttons, movement, blocker checks
├── pokemart.py                # PokeMart mixin - shop UI with categories, TMs, evolution stones, battle items
├── trade.py                   # Trading mixin - Pokemon trades with evolution checks, link cable support
├── party.py                   # Party management mixin - view, switch active, release
├── pc.py                      # PC storage mixin - deposit, withdraw, browse
├── inventory.py               # Inventory/bag display mixin
├── pokedex.py                 # Pokedex display mixin
├── card.py                    # Trainer card mixin - stats, about, Pokemon display
├── pokemon.py                 # Main cog class combining all mixins
├── constant.py                # All constants: Pokemon emojis, item emojis, badge emojis, location names, battle constants, TM mappings
├── functions.py               # UI helpers: create_hp_bar(), type colors, embed builders
└── sheehan.py                 # Dev test script (not part of bot)
```

---

## Architecture

### Mixin Pattern
The main Pokemon cog uses mixins to separate functionality into manageable files:

| Mixin | File | Responsibility |
|-------|------|---------------|
| `EncountersMixin` | encounters.py | Wild encounters, gym battles, manual/auto battles, catching, items |
| `FinaleMixin` | finalemixin.py | Post-game finale cinematic system |
| `AchievementsMixin` | achievements.py | Achievement announcements to configured channel |
| `LeaderboardMixin` | leaderboard.py | Global leaderboard display |
| `MapMixin` | map.py | Location navigation with directional buttons |
| `PokeMartMixin` | pokemart.py | Shop system with categories |
| `TradeMixin` | trade.py | Pokemon trading between players |
| `PartyMixin` | party.py | Party management |
| `PcMixin` | pc.py | PC storage system |
| `InventoryMixin` | inventory.py | Bag/inventory display |
| `PokedexMixin` | pokedex.py | Pokedex display |
| `CardMixin` | card.py | Trainer card stats |

All mixins inherit from `MixinMeta` and are combined in `pokemon.py`.

### State Management

**Three distinct state systems:**

1. **`__useractions`** (dict of `ActionState`) — General exploration/encounter state
   - Tracks: user ID, channel, message ID, location, active Pokemon, wild Pokemon, description log
   - Used for: map navigation, encounter choices, catching, running

2. **`__battle_states`** (dict of `BattleState`) — Gym/trainer manual battles
   - Tracks: full party, enemy team list, current indices, battle log, ailments, stat stages, leech seed, rest turns
   - Used for: manual gym battles, wild trainer battles

3. **`__wild_battle_states`** (dict of `WildBattleState`) — Wild Pokemon manual battles
   - Tracks: player Pokemon, wild Pokemon, party, ailments, stat stages
   - Used for: manual wild encounters

4. **`__finale_engines`** (dict of `FinaleEngine`) — Finale state machines
   - Tracks: scene progression, battle state, audio, renderer
   - One per guild at a time

**Critical Rule:** Always update `messageId` in state after sending/editing messages to prevent "This is not for you" errors.

### Battle Systems

**Auto Battle** (`encounter.fight(battleType='auto')`):
- AI vs AI, runs full battle loop in `encounterclass.py`
- Uses `battle_fight()` with stat stages, special moves, ailments
- Returns battle result, logs, experience

**Manual Battle** (turn-by-turn UI):
- Player selects moves via Discord buttons
- Each turn processes: player move → enemy move → status effects
- Supports: stat stages, special moves (rest, recover, drain, leech seed, haze, night shade, dream eater), ailments
- Switch Pokemon on faint, item usage during battle
- Works for both wild encounters and gym/trainer battles

**Finale Battle** (scripted modes):
- `unwinnable` — Player attacks do nothing, enemy one-shots, uses all party except last
- `rigged_win` — Player does 10% per hit, enemy can't hurt you, ends at 50% HP
- `final_skippy` — Normal battle mechanics, player uses highest-level Pokemon only
- `melkor` — Normal battle mechanics with cutscene triggers at HP thresholds
- `normal` — Standard battle using `calculate_battle_damage()`

### Database Schema (PostgreSQL)

| Table | Purpose |
|-------|---------|
| `trainer` | Trainer data: discord_id, location, activePokemon, starter |
| `pokemon` | Pokemon instances: stats, IVs, EVs, moves, types, shiny, is_deleted, party flag |
| `inventory` | Items, money, pokeballs, stones, TMs (TM01-TM50), special items |
| `keyitems` | Badges, HMs, quest flags, fossil choices, easter egg items (eevee_tail, game_shark) |
| `trainer_battles` | Defeated gym trainers/leaders by enemy_uuid |
| `leaderboard` | Stats: battles, victories, defeats, catches, balls_thrown, run_aways, releases, evolved, easter_eggs, completions, trades, actions |
| `ailments` | Active status ailments on Pokemon |
| `pokedex` | Pokemon species seen/caught per trainer |
| `unique_encounters` | Special Pokemon flags (mew, porygon, etc.) |

### Database Patterns
```python
db = dbconn()
result = db.querySingle(query, params)   # Single row
results = db.queryAll(query, params)      # Multiple rows
db.execute(query, params)                 # INSERT/UPDATE
del db                                    # Close connection (always in finally block)
```

---

## Key Features (All Functional)

### Core Gameplay
- ✅ **Complete Kanto Region** — All locations, routes, caves, buildings with interconnected map
- ✅ **Wild Pokemon Encounters** — Walk, surf, fish (old/good/super rod), gift Pokemon, Poke Flute
- ✅ **Manual & Auto Battles** — Choose moves or let AI fight
- ✅ **Pokemon Catching** — Pokeball/Great/Ultra/Master with catch rate mechanics
- ✅ **Gym System** — All 8 gyms with trainers → leader progression, badge rewards
- ✅ **Elite Four** — Full progression through Lorelei → Bruno → Agatha → Lance → Champion Blue
- ✅ **Quest System** — Story quests with prerequisites, blockers, rewards
- ✅ **Map Navigation** — Directional buttons with blocker checks (requires items/badges)
- ✅ **Party/PC Management** — View, switch active, deposit, withdraw, release
- ✅ **Trading** — Player-to-player with trade evolution support (link cable items)
- ✅ **PokeMart** — Full shop with categories: Pokeballs, Potions, Status Heals, Battle Items, Evolution Stones, TMs
- ✅ **Pokedex** — Species tracking with seen/caught status
- ✅ **Trainer Card** — Stats display with leaderboard data

### Battle Mechanics
- ✅ **Type Effectiveness** — Full type chart from typeEffectiveness.json
- ✅ **STAB** — Same-type attack bonus (1.5x)
- ✅ **Status Ailments** — Burn, poison, freeze, sleep, confusion, paralysis with per-turn effects
- ✅ **Stat Stages** — Attack, Defense, Speed, Sp.Atk, Sp.Def, Accuracy, Evasion (+6 to -6)
- ✅ **Special Moves** — Rest (sleep+heal), Recover, Drain moves, Leech Seed, Night Shade, Haze, Dream Eater
- ✅ **Secondary Stat Effects** — Chance-based stat changes on damaging moves
- ✅ **Pokemon Switching** — Switch on faint with alive party members
- ✅ **In-Battle Items** — Potions, revives, evolution stones, TMs during battle

### Evolution
- ✅ **Level-Up Evolution** — Automatic during battle with move learning
- ✅ **Stone Evolution** — Fire/Water/Thunder/Leaf/Moon stones via item usage
- ✅ **Trade Evolution** — Link Cable item triggers trade evolutions
- ✅ **Shiny Preservation** — Shiny status carries through evolution
- ✅ **Move Preservation** — Moves transfer from pre-evolution form

### Advanced Features
- ✅ **Shiny Pokemon** — Random shiny rolls on encounter/creation, custom sprite URLs
- ✅ **Achievement System** — Configurable announcement channel for badges, capture milestones (50/100/150), Elite Four, first evolutions, easter eggs
- ✅ **Leaderboard** — Global rankings and personal stats (battles, catches, evolutions, trades, etc.)
- ✅ **Easter Eggs** — Hidden quests (Search Room → Eevee's Tail, Play SNES → Game Shark, Check Truck → Mew, Old Man glitch reference)
- ✅ **Wild Route Trainers** — NPC trainers on routes from enemyTrainers.json with auto/manual battle
- ✅ **Rival Battles** — Blue encounters at scripted locations with dynamic starter-based team
- ✅ **TM System** — TM01-TM50 purchasable and usable, teaches moves to compatible Pokemon
- ✅ **Fossil System** — Choose Helix/Dome fossil, revive at Cinnabar Lab for Omanyte/Kabuto/Aerodactyl
- ✅ **Custom Pokemon Emojis** — Full set of 151 Pokemon emojis from custom Discord emoji servers
- ✅ **Item Emojis** — Custom emojis for pokeballs, potions, badges, HMs, key items, evolution stones

### Finale System (Post-Game)
- ✅ **Cinematic Experience** — PIL-rendered scenes with dialog, transitions, custom backgrounds
- ✅ **Voice Channel Audio** — Joins voice and plays music tracks during finale (FFmpeg)
- ✅ **3-Act Story** — Skippy encounter → Unwinnable battle → Power of friendship → Final battle → Chodethulu
- ✅ **Custom Pokemon** — FinalePokemon class with custom moves, stats, sprites from pokemon_config.json
- ✅ **Multiple Battle Modes** — Unwinnable, rigged_win, final_skippy, melkor (with cutscene triggers)
- ✅ **Battle Cutscenes** — Mid-battle interruptions triggered by HP thresholds or turn counts
- ✅ **Retry/Quit on Defeat** — Players can retry battles or quit finale
- ✅ **Auto-Advance Scenes** — Timed transitions with configurable duration
- ✅ **Admin Commands** — `,finaleact <act>` to skip to specific acts for testing

---

## Important Patterns & Conventions

### Code Changes (for AI assistants)
- **Provide full methods** to copy/replace, OR use `# old code → # new code` format
- **Never reference line numbers** — they're often wrong
- Search for old code strings to find replacement locations

### Config Loading
```python
from helpers.pathhelpers import load_json_config
moves_config = load_json_config('moves.json')      # Cached after first load
pokemon_config = load_json_config('pokemon.json')
```

### Sprite Loading
```python
# URL-based (preferred for embeds)
sprite_url = f"https://pokesprites.joshkohut.com/sprites/pokemon/{pokedex_id}.png"
# Shiny
shiny_url = f"https://pokesprites.joshkohut.com/sprites/pokemon/shiny/{pokedex_id}.png"
# Local file fallback
from helpers.pathhelpers import get_sprite_path
local_path = get_sprite_path('pokemon/front/1.png')
```

### Pokemon Emoji Usage
```python
import constant
emoji = constant.POKEMON_EMOJIS.get(pokemon_name.upper(), '')
# e.g., constant.POKEMON_EMOJIS['PIKACHU'] → "<:pikachu:981370...>"
```

### Trainer Instance Caching
```python
trainer = self._get_trainer(str(user.id))  # Cached TrainerClass instance
```

### HP Bar Display
```python
from functions import create_hp_bar
hp_bar = create_hp_bar(current_hp, max_hp)
```

### Battle Damage Calculation
```python
from services.encounterclass import calculate_battle_damage
damage, hit = calculate_battle_damage(attacker, defender, move_name, moves_config, type_effectiveness)
```

### Session Validation
```python
# Check if interaction belongs to the correct user
if not self.__checkUserActionState(user, interaction.message):
    await interaction.response.send_message('This is not for you.', ephemeral=True)
    return
```

### Interaction Patterns
```python
# Pattern 1: Defer then edit
await interaction.response.defer()
message = await interaction.message.edit(embed=embed, view=view)

# Pattern 2: Defer then followup (new message)
await interaction.response.defer()
new_message = await interaction.followup.send(embed=embed, view=view)

# Pattern 3: Direct response (no defer)
await interaction.response.send_message('Error', ephemeral=True)
```

### Module Exports
```python
# services/encounterclass.py
__all__ = ['encounter', 'calculate_battle_damage']

# helpers/__init__.py
from .helpers import getTrainerGivenPokemonName
from .specialmoves import *
from .statstages import *
```

---

## Debugging Tips

### "This is not for you" Error
- ActionState/BattleState `messageId` doesn't match current message
- Fix: Update state after every `send`/`edit` that changes the message
- Check: `state.message_id = message.id`

### Pokemon Not Loading
- Ensure `pokemonName` is not None before operations
- Always reload from DB: `pokemon.load(pokemonId=pokemon.trainerId)`
- Never trust cached data — the conditional `if pokemon.pokemonName is None` pattern was a known bug source

### Interaction Failures
- `response.send_message()` after `defer()` → use `followup.send()` instead
- `response.send_message()` without `defer()` works fine
- Edit existing message: `interaction.message.edit()` (doesn't need defer)

### Config Key Mismatches
- Pokemon names: lowercase with hyphens (e.g., `mr-mime`, `nidoran-f`)
- Location names: lowercase with hyphens (e.g., `kanto-route-23-S`)
- Moves: lowercase with hyphens (e.g., `thunder-wave`)

### Database Issues
- Verify container: `docker ps | grep postgres_container`
- Host must be `postgres_container` (not external hostname)
- Column names use hyphens in DB but underscores in Python (e.g., `"poke-ball"` in SQL, `pokeball` in class)

### Finale Issues
- Only one finale per guild at a time
- Auto-advance uses `_advance_id` to prevent stale task execution
- Voice channel disconnect requires explicit cleanup
- Image cache busting: `next_frame_name()` generates unique filenames

---

## Development Workflow

```bash
# 1. Edit files
cd /home/legend/Documents/GitHub/discord-cogs/pokemon
# make changes...

# 2. Copy to running bot
cp -r . /home/legend/claude/docker/data/cogs/CogManager/cogs/pokemon/

# 3. Clear cache
find /home/legend/claude/docker/data/cogs/CogManager/cogs/pokemon/ -type d -name __pycache__ -exec rm -rf {} +

# 4. Reload in Discord
# Type: ,reload pokemon

# 5. Check logs
docker logs pokebot --tail 50

# 6. Commit
git add .
git commit -m "Description"
git push
```

---

## File Size Reference

| File | Approximate Size | Notes |
|------|-----------------|-------|
| encounters.py | ~8000+ lines | Main battle/encounter logic, largest file |
| finalemixin.py | ~1500+ lines | Finale orchestration |
| constant.py | ~600+ lines | All emojis, names, constants |
| pokeclass.py | ~800+ lines | Pokemon data model |
| encounterclass.py | ~700+ lines | Core battle mechanics |
| trainerclass.py | ~500+ lines | Trainer management |
| questclass.py | ~500+ lines | Quest system with rewards |
| pokemart.py | ~400+ lines | Shop UI and item catalog |
| gyms.json | ~826 lines | All gym data |
| enemyTrainers.json | ~3000+ lines | Route trainer data |