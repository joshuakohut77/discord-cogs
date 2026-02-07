# Pokemon Discord Bot - Project Context Summary

## Project Overview

**Repository:** https://github.com/joshuakohut77/discord-cogs.git
**Working Directory:** `/home/legend/Documents/GitHub/discord-cogs/pokemon`
**Running Bot Directory:** `/home/legend/claude/docker/data/cogs/CogManager/cogs/pokemon`
**Framework:** Red-DiscordBot v3.5.22 with Discord.py v2.6.3
**Language:** Python 3.11
**Database:** PostgreSQL (postgres_container)

## Project Structure

```
discord-cogs/pokemon/
├── configs/           # JSON configuration files
│   ├── gyms.json     # Gym leaders, trainers, requirements, badges
│   ├── quests.json   # Quest data, pre-requisites, blockers
│   ├── locations.json # Location data, connections, gym flags
│   ├── pokemon.json  # Pokemon stats, types, moves
│   ├── moves.json    # Move data, power, accuracy, effects
│   └── typeEffectiveness.json # Type matchup multipliers
├── services/         # Backend service classes
│   ├── battleclass.py      # Gym battle progression, victory tracking
│   ├── encounterclass.py   # Battle mechanics, damage calculation, exports calculate_battle_damage()
│   ├── trainerclass.py     # Trainer data management
│   ├── locationclass.py    # Location management
│   ├── questclass.py       # Quest system, blockers checking
│   ├── keyitemsclass.py    # Key items (badges, HMs, etc.)
│   ├── pokeclass.py        # Pokemon class
│   ├── ailmentsclass.py    # Status ailments (burn, poison, freeze, etc.)
│   └── dbclass.py          # Database connection handler
├── models/           # Data models (NEW PACKAGE)
│   ├── __init__.py          # Package marker
│   ├── battlestate.py       # BattleState, WildBattleState classes
│   └── sessionstate.py      # ActionState, BagState, ItemUsageState, MartState
├── helpers/          # Helper utilities (NEW PACKAGE)
│   ├── __init__.py          # Package marker, exports getTrainerGivenPokemonName
│   ├── helpers.py           # General helper functions
│   ├── pathhelpers.py       # Config/sprite path loading (NEW)
│   └── decorators.py        # Session validation decorators (NEW)
├── *.py             # Cog mixins (encounters.py, map.py, etc.)
├── constant.py      # Constants (emojis, location display names, battle constants)
└── functions.py     # UI helpers (embeds, HP bars, colors)


```

## Database Schema (PostgreSQL)

- **trainer_battles** - Tracks defeated gym trainers/leaders by enemy_uuid
- **keyitems** - Stores trainer badges, HMs, and quest flags
- **trainers** - Trainer data (location, active Pokemon)
- **pokemon** - Pokemon instances owned by trainers
- **inventory** - Items, money, pokeballs

## Recent Major Accomplishments

### 1. Database Connection Fix
**Issue:** 90-second timeout connecting to external PostgreSQL server
**Fix:** Changed host from `REDACTED_HOST` to `postgres_container` in `services/dbclass.py:37`
**Result:** Instant response times

### 2. Discord API Modernization
**Issue:** Outdated `discord_components` library causing AttributeErrors
**Changes:** Migrated 8 files from old API to modern `discord.ui`:
- Changed `self.client.add_callback()` → `View() + button.callback`
- Changed `interaction.respond()` → `interaction.response.defer()`
- Changed `edit_original_response()` → `interaction.message.edit()`
- Fixed `view=[btns]` → `view=btns` (View object not list)

**Files Updated:**
- inventory.py (2 instances)
- pokedex.py (2 instances)
- pokemart.py (2 instances)
- card.py (3 instances)
- trade.py (5 instances)
- encounters.py (11 instances)
- map.py (4 direction handlers)
- party.py, pc.py

### 3. Pokemon Sprite Server Fix
**Issue:** LAMP container failing with exec format error, sprites returning 502
**Fix:** Replaced `mattrayner/lamp` with `nginx:alpine` in `/srv/pokesprites/docker-compose.yml`
**Config:** Volume mount `./app:/usr/share/nginx/html`
**Result:** Sprites now accessible at https://pokesprites.joshkohut.com/sprites/

### 4. Stale Data Fix
**Issue:** Pokemon HP/level not updating after battles
**Problem:** Conditional loading `if pokemon.pokemonName is None:` cached old data
**Fix:** Always reload from database: `pokemon.load(pokemonId=pokemon.trainerId)`
**Files:** party.py (2x), pc.py (2x), trade.py (1x)

### 5. Location Names Dictionary
**Issue:** KeyError for segmented routes (kanto-route-23-S, etc.)
**Fix:** Added 44 missing location names to `constant.py LOCATION_DISPLAY_NAMES`:
- Segmented routes: route-10-N/S, route-12-N/S, route-23-N/S
- Mt. Moon basement floors, Cerulean Cave floors
- Seafoam Islands BF1-4, Rocket Hideout floors
- Silph Co. all floors (2F-11F)
- S.S. Anne all areas (deck, rooms, basement)
- Elite Four rooms (Lorelei, Bruno, Agatha, Lance)
- Victory Road floors, Game Corner, etc.

### 6. Map Navigation Blockers
**Issue:** No restrictions on location travel
**Implementation:** Added conditional movement based on `quests.json` blockers
- Checks trainer has required key items before allowing travel
- Uses existing `QuestsClass.locationBlocked()` for consistency
- Shows helpful error messages listing missing items
- Example: Route 2 requires `oaks_parcel_delivered`

**Flow:** User clicks direction button → Check blockers → Allow/deny with message

### 7. Quest System Integration
**Implementation:** Quest buttons now appear in encounters at locations with quests
- Blue (blurple) buttons to distinguish from encounters
- Checks pre-requisites before enabling
- Clicking executes quest via `trainer.quest(questName)`
- Rewards defined in `questclass.py` methods
- Shows quest story/message

**Example Quests:**
- Pallet Town: "Garys Sister" → Town Map
- Professor Oak's Lab: "Professor Oak" → Sets oaks_parcel_delivered

### 9. encounters.py Refactoring (COMPLETED 2026-02-04)
**Goal:** Reduce code duplication and improve organization in encounters.py (7,476 lines)
**Result:** Successfully reduced to 7,256 lines (-220 lines, -2.9%) with improved maintainability

#### Phase 1: Extract Constants & Path Helpers
**Changes:**
- Created `helpers/pathhelpers.py` with centralized config loading
  - `get_config_path(filename)` - Resolves config file paths
  - `load_json_config(filename)` - Loads and caches JSON configs
  - `get_sprite_path(sprite_path)` - Resolves sprite paths
- Enhanced `constant.py` with battle constants:
  - `BATTLE_CONSTANTS` - Damage calculation values (217, 256, STAB 1.5x)
  - `DISCORD_LIMITS` - Field/label character limits
  - `ITEM_HEALING` - Potion healing amounts
- Replaced 15+ duplicate `os.path.join()` patterns in encounters.py

**Line Reduction:** 7,476 → 7,439 (-37 lines)

#### Phase 2: Move State Classes to Models Package
**Changes:**
- Created `models/battlestate.py`:
  - Moved `BattleState` class (multi-Pokemon battle state)
  - Moved `WildBattleState` class (single wild encounter state)
- Created `models/sessionstate.py`:
  - Moved `ActionState` class (wild encounter actions)
  - Moved `BagState` class (bag navigation state)
  - Moved `ItemUsageState` class (item usage flow)
  - Moved `MartState` class (PokeMart UI state)
- Updated encounters.py to import from new locations

**Line Reduction:** 7,439 → 7,331 (-108 lines)

#### Phase 3: Extract Damage Calculation
**Changes:**
- Added `calculate_battle_damage()` function to `services/encounterclass.py`
  - Centralized Gen 1 damage formula: `((2*level/5+2) * power * (atk/def) / 50 + 2) * random * STAB * effectiveness`
  - Handles hit/miss calculation based on move accuracy
  - Returns tuple: `(damage, hit_success)`
- Replaced 4 duplicate damage calculations (300+ lines duplicated code)
- Added `__all__ = ['encounter', 'calculate_battle_damage']` export

**Line Reduction:** 7,331 → 7,254 (-77 lines)

#### Phase 4: Create Session Validation Decorators
**Changes:**
- Created `helpers/decorators.py` with validation decorators:
  - `@require_action_state()` - Validates ActionState session
  - `@require_battle_state()` - Validates BattleState session
  - `@require_wild_battle_state()` - Validates WildBattleState session
  - `@require_bag_state()` - Validates BagState session
- Applied to key handler methods as proof of concept
- Eliminates repeated session validation checks

**Line Reduction:** 7,254 → 7,232 (-22 lines)

#### Phase 5: UI Component Factories
**Status:** Reserved for future implementation
**Potential:** Would eliminate 900+ lines of duplicate Pokemon selectors and party buttons

#### Phase 6: Add Battle UI Functions
**Changes:**
- Added `create_hp_bar()` function to `functions.py`
  - Visual HP bar display: `█████░░░░░`
  - Replaced 2 duplicate implementations
- Updated all 4 `make_hp_bar` calls to use `create_hp_bar`

**Line Reduction:** 7,232 → 7,222 (-10 lines)

#### Phase 7: Consolidate TrainerClass Instantiation
**Changes:**
- Added `_get_trainer()` helper method with caching to encounters.py
- Replaced 46 instances of `TrainerClass(str(user.id))`
- Reduces object creation overhead
- Added `_clear_trainer_cache()` for cache invalidation

**Line Change:** 7,222 → 7,256 (+34 net, but improves performance)

#### Bug Fixes Applied During Refactoring
1. **ImportError for calculate_battle_damage**: Added `__all__` export to encounterclass.py
2. **ModuleNotFoundError for helpers**: Created `helpers/__init__.py` package marker
3. **ModuleNotFoundError for models**: Created `models/__init__.py` package marker
4. **ImportError for getTrainerGivenPokemonName**: Moved helpers.py to helpers/helpers.py, exported from __init__.py
5. **NameError for make_hp_bar**: Replaced all calls with `create_hp_bar`
6. **NotNullViolation in ailments table**: Fixed pre-existing bug - added pokemonId to INSERT column list in ailmentsclass.py:89
7. **AttributeError for MartState.quantity**: Added missing quantity attribute to MartState.__init__
8. **ModuleNotFoundError for pathhelpers**: Fixed import path after package restructure

#### Summary
- **Original:** 7,476 lines
- **Final:** 7,256 lines
- **Reduction:** -220 lines (-2.9%)
- **New Files:** 8 (pathhelpers.py, decorators.py, battlestate.py, sessionstate.py, 4 __init__.py files)
- **Git Commits:** 14 (6 refactoring phases + 8 bug fixes)
- **Architecture:** Clear separation of concerns (UI/Logic/Data), reusable components, follows existing patterns

### 8. Gym Challenge System (FULLY FUNCTIONAL)
**Implementation:** Complete gym battle system with UI and mechanics

#### Gym Button
- Red "Gym Challenge" button appears at locations with `gym: true`
- Checks leader requirements from gyms.json
- Disabled if trainer lacks requirements

#### Battle Flow
1. Click "Gym Challenge" → Shows trainer/leader info
2. "Battle Trainer" or "Challenge Gym Leader" button appears
3. Click battle button → Creates enemy Pokemon from gym data
4. Runs `encounter.fight(battleType='auto')` for turn-based combat
5. Victory → Money reward, tracks completion in trainer_battles table
6. Shows next trainer or gym leader readiness

#### Battle Mechanics (encounterclass.py)
- Full turn-based combat (MAX_BATTLE_TURNS = 50)
- Damage calculation: `((2*level/5+2) * power * (atk/def) / 50 + 2) * random * STAB * type_effectiveness`
- Type effectiveness from typeEffectiveness.json
- Ailment system: burn, poison, freeze, confusion, sleep, trap
- Experience gain and level up system
- Victory: `enc.__victory()` → exp, money, level ups
- Defeat: `enc.__defeat()` → Pokemon faints (HP = 0)

#### Gym Progression (battleclass.py)
- `getRemainingTrainerCount()` → Tracks undefeated trainers
- `getNextTrainer()` → Gets next trainer to battle
- `getGymLeader()` → Available only after all trainers defeated
- `battleVictory(trainer)` → Money reward, database tracking
- `gymLeaderVictory(leader)` → Badge + money, updates keyitems table
- Database: trainer_battles table tracks enemy_uuid completions

#### Rewards
- Trainers: Money (varies by trainer)
- Gym Leaders: Badge + Money
  - Boulder Badge (Brock)
  - Cascade Badge (Misty)
  - Thunder Badge (Lt. Surge)
  - Rainbow Badge (Erika)
  - Soul Badge (Koga)
  - Marsh Badge (Sabrina)
  - Volcano Badge (Blaine)
  - Earth Badge (Giovanni - requires badge_volcano)

## Critical Fixes Applied

### File Path Resolution
**Issue:** FileNotFoundError when loading gyms.json
**Fix in battleclass.py:**
```python
# Changed from:
configPath = './configs/gyms.json'
loadedConfig = json.load(open(configPath, 'r'))

# To:
configPath = '../configs/gyms.json'
p = os.path.join(os.path.dirname(os.path.realpath(__file__)), configPath)
loadedConfig = json.load(open(p, 'r'))
```

### Pokemon Name Typos in gyms.json
**Issue:** KeyError when creating gym trainer Pokemon
**Fix:** Corrected spellings:
- "bellsproud" → "bellsprout"
- "victreebell" → "victreebel"

### ActionState Message ID Tracking
**Issue:** "This is not for you" error on gym battle buttons
**Fix:** Update ActionState messageId when sending new messages:
```python
message = await interaction.followup.send(...)
self.__useractions[str(user.id)].messageId = message.id
```

## Development Workflow

### 1. Making Changes
```bash
# Work in the cloned repo
cd /home/legend/claude/discord-cogs/pokemon

# Edit files
# ... make changes ...

# Copy to running bot
cp file.py /home/legend/claude/docker/data/cogs/CogManager/cogs/pokemon/

# Clear Python cache
find /home/legend/claude/docker/data/cogs/CogManager/cogs/pokemon -type d -name "__pycache__" -exec rm -rf {} +

# Reload cog in Discord
,reload pokemon
```

### 2. Committing Changes
```bash
cd /home/legend/claude/discord-cogs

git add pokemon/file.py
git commit -m "Description

Details about what changed

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
git push

# If push rejected (remote has changes):
git pull --rebase && git push
```

### 3. Checking Logs
```bash
# View recent logs
docker logs pokebot --tail 50

# Search for errors
docker logs pokebot --tail 100 | grep -A 20 "Traceback\|Error\|Exception"

# Follow logs live
docker logs pokebot -f
```

### 4. Database Connection
```bash
# Already configured in dbclass.py
Host: postgres_container
Database: pokemon_db
User: redbot
Password: REDACTED
Port: 5432
```

## Key Code Patterns

### 1. Discord Button Pattern
```python
# Modern discord.ui pattern
from discord.ui import Button, View
from discord import ButtonStyle, Interaction

view = View()
button = Button(style=ButtonStyle.gray, label="Label", custom_id='unique_id')
button.callback = self.on_button_click
view.add_item(button)

# Handler
async def on_button_click(self, interaction: discord.Interaction):
    await interaction.response.defer()  # Always defer first
    # Do work...
    await interaction.followup.send("Result")  # Use followup after defer
```

### 2. Checking Quest Blockers
```python
from services.questclass import quests as QuestsClass

quest_obj = QuestsClass(user_id)
blockers = ['badge_volcano', 'HM03']

if quest_obj.locationBlocked(blockers):
    # User doesn't have required items
    return "You need: Badge Volcano, HM03"
```

### 3. Creating Pokemon for Battle
```python
from services.pokeclass import Pokemon as PokemonClass

# Create enemy Pokemon
enemy_pokemon = PokemonClass("pikachu")
enemy_pokemon.create(level=25)

# Get trainer's active Pokemon
trainer = TrainerClass(str(user.id))
active_pokemon = trainer.getActivePokemon()

# Start battle
from services.encounterclass import encounter as EncounterClass
enc = EncounterClass(active_pokemon, enemy_pokemon)
result = enc.fight(battleType='auto')

if result.get('result') == 'victory':
    # Handle victory
    print(enc.message)  # Contains exp gained, level ups, etc.
```

### 4. Gym Battle Tracking
```python
from services.battleclass import battle as BattleClass

# Create battle handler
battle = BattleClass(user_id, location_id, enemyType="gym")

# Check progress
remaining = battle.getRemainingTrainerCount()
next_trainer = battle.getNextTrainer()  # Returns TrainerBattleModel
gym_leader = battle.getGymLeader()      # Returns GymLeaderModel

# After victory
battle.battleVictory(trainer_model)     # Money + database tracking
battle.gymLeaderVictory(leader_model)   # Badge + money + database
```

### 5. Loading Config Files (NEW PATTERN)
```python
# Modern pattern using pathhelpers (Phase 1 refactoring)
from helpers.pathhelpers import load_json_config, get_sprite_path

# Load JSON config with caching
moves_config = load_json_config('moves.json')
gyms_data = load_json_config('gyms.json')

# Get sprite path
sprite_path = get_sprite_path('/sprites/pokemon/pikachu.png')

# Old pattern (still works, but prefer pathhelpers)
import json
import os
config_path = os.path.join(os.path.dirname(__file__), '../configs/gyms.json')
data = json.load(open(config_path, 'r'))
```

### 6. Using Session Validation Decorators (NEW PATTERN)
```python
# Modern pattern using decorators (Phase 4 refactoring)
from helpers.decorators import require_wild_battle_state, require_bag_state

# Decorator automatically validates session
@require_wild_battle_state()
async def on_battle_move_click(self, interaction: discord.Interaction):
    # No need for manual validation, decorator handles it
    user_id = str(interaction.user.id)
    battle_state = self.__wild_battle_states[user_id]
    # ... proceed with battle logic

@require_bag_state()
async def on_bag_item_click(self, interaction: discord.Interaction):
    user_id = str(interaction.user.id)
    bag_state = self.__bag_states[user_id]
    # ... proceed with item logic

# Old pattern (still used in many places, migrate gradually)
async def on_button_click(self, interaction: discord.Interaction):
    user_id = str(interaction.user.id)
    if user_id not in self.__wild_battle_states:
        await interaction.response.send_message('No active battle.', ephemeral=True)
        return
    battle_state = self.__wild_battle_states[user_id]
    if battle_state.message_id != interaction.message.id:
        await interaction.response.send_message('This is not the current battle.', ephemeral=True)
        return
    # ... proceed with logic
```

### 7. Creating Visual HP Bars (NEW PATTERN)
```python
# Modern pattern using functions.py (Phase 6 refactoring)
from functions import create_hp_bar

# Calculate HP percentage
hp_percent = (pokemon.currentHP / max_hp) * 100

# Create visual HP bar
hp_bar = create_hp_bar(hp_percent, bar_length=10)
# Output: "█████░░░░░" (50% HP example)

# Use in embed
description = f"HP: {pokemon.currentHP}/{max_hp}\n{hp_bar}"
```

### 8. Using Battle Constants (NEW PATTERN)
```python
# Modern pattern using constant.py (Phase 1 refactoring)
from constant import BATTLE_CONSTANTS, ITEM_HEALING

# Access battle constants
random_damage = random.randrange(
    BATTLE_CONSTANTS['RANDOM_DAMAGE_MIN'],
    BATTLE_CONSTANTS['RANDOM_DAMAGE_MAX']
)
stab_multiplier = BATTLE_CONSTANTS['STAB_MULTIPLIER']  # 1.5

# Access item healing amounts
heal_amount = ITEM_HEALING.get('potion', 20)  # 20 HP
```

## Common Discord Bot Commands

```bash
# Prefix: ,

# Encounter commands
,trainer encounter      # Show encounter options (walk, surf, etc.)
,trainer enc           # Alias for encounter

# Map navigation
,trainer map           # Show current location map
# Click direction buttons to travel

# Party/PC
,trainer party         # View party Pokemon
,trainer pc            # View PC Pokemon
,trainer bag           # View inventory

# Trading
,pokecenter trade @user pokemonId   # Trade Pokemon

# Gym battles
,trainer encounter     # At gym location → Click "Gym Challenge"

# Reloading cog
,reload pokemon        # Reload after making changes
```

## Current State: What Works

✅ **Database Connections** - Fast, no timeouts
✅ **Map Navigation** - All locations accessible with blocker checks
✅ **Quest System** - Quest buttons appear, rewards given
✅ **Gym Battles** - Full battle system functional
✅ **Trainer Battles** - Auto-battle with damage calculation
✅ **Badge Earning** - Gym leaders give badges correctly
✅ **Experience System** - Pokemon gain exp and level up
✅ **Type Effectiveness** - Fire vs Grass, etc. working
✅ **Ailments** - Burn, poison, freeze, confusion, etc.
✅ **Pokemon Sprites** - Display correctly in embeds
✅ **Inventory System** - Items, money tracking
✅ **Party/PC Management** - View and manage Pokemon
✅ **Trading** - Pokemon trades work with evolution checks

## Known Limitations

⚠️ **Manual Move Selection** - Currently only auto-battle (AI vs AI)
⚠️ **Multi-Pokemon Battles** - Gym leaders with multiple Pokemon fight one at a time
⚠️ **Wild Encounters** - Encounter system exists but not fully integrated with new UI
⚠️ **Battle Animations** - Text-based, no animations
⚠️ **Status Effects UI** - Ailments work but limited feedback

## Architecture Notes

### Mixin Pattern
The Pokemon cog uses mixins to separate functionality:
- `EncountersMixin` - Encounter system, gym battles, quests
- `MapMixin` - Location navigation, movement
- `TradeMixin` - Pokemon trading
- `PartyMixin` - Party management
- `PcMixin` - PC storage
- `InventoryMixin` - Items and bag

All mixins inherit from `MixinMeta` and are combined in the main cog.

### State Management
Uses `__useractions` dict to track interaction state:
```python
self.__useractions[str(user.id)] = ActionState(
    discordId, channelId, messageId, location, activePokemon, wildPokemon, descLog
)
```

**Critical:** Update `messageId` when sending new messages to prevent "This is not for you" errors.

### Database Patterns
Services use connection pooling:
```python
db = dbconn()
result = db.querySingle(query, params)
results = db.queryAll(query, params)
db.execute(query, params)
del db  # Close connection in finally block
```

## Debugging Tips

### 1. "This is not for you" Error
- Means ActionState messageId doesn't match current message
- Fix: Update state after sending new message
- Check: `self.__useractions[str(user.id)].messageId = message.id`

### 2. KeyError in Config Loading
- Pokemon/location name typo or mismatch
- Check spelling matches pokemon.json exactly
- Use lowercase with hyphens (e.g., "mr-mime")

### 3. FileNotFoundError for Configs
- Using relative paths incorrectly
- Always use: `os.path.join(os.path.dirname(__file__), '../configs/file.json')`

### 4. Pokemon Not Loading
- Check `pokemonName` is not None
- Verify name exists in pokemon.json
- Add error handling around `pokemon.create()`

### 5. Interaction Failed
- Using `response.send_message()` after `defer()`
- Fix: Use `followup.send()` after defer
- Or use `response.send_message()` without defer

### 6. Database Errors
- Check postgres_container is running: `docker ps`
- Verify connection in dbclass.py uses `postgres_container` as host
- Check credentials match container environment

## Next Steps / TODO

**Potential Enhancements:**
1. Manual move selection during battles (turn-based UI)
2. Multi-Pokemon battles for gym leaders
3. Wild Pokemon encounter buttons integration
4. Battle animations/better feedback
5. Status effect indicators in battle UI
6. Switching Pokemon during battle
7. Item usage during battle (potions, revives)
8. Enemy trainer battles in routes (not just gyms)
9. Elite Four progression system
10. Pokemon evolution UI (trade evolutions work, level-up needs UI)

**Areas to Explore:**
- How Pokemon evolution works (level-up, stone, trade)
- How wild encounters are triggered vs trainer battles
- PvP trainer battles system
- Leaderboard system
- Fishing rod mechanics
- HM usage (Cut, Surf, Fly, etc.)

## Important Files Reference

**Core Cog Files:**
- `encounters.py` - Encounter UI, gym battles, quest buttons (7,256 lines after refactoring, was 7,476)
- `map.py` - Location navigation, direction buttons (400+ lines)
- `constant.py` - Location display names, emoji constants, battle constants
- `functions.py` - UI helpers (embeds, HP bars, type colors)

**Service Layer:**
- `battleclass.py` - Gym progression, victory tracking (224 lines)
- `encounterclass.py` - Battle mechanics, exports `calculate_battle_damage()` (689 lines)
- `trainerclass.py` - Trainer management, has `quest()` method (375+ lines)
- `questclass.py` - Quest system, `locationBlocked()` checker
- `keyitemsclass.py` - Badge/HM tracking (137 lines)
- `pokeclass.py` - Pokemon class, moves, stats
- `ailmentsclass.py` - Status ailments (sleep, poison, burn, freeze, etc.)
- `dbclass.py` - Database connection handler

**Models Package (NEW):**
- `models/battlestate.py` - BattleState, WildBattleState classes
- `models/sessionstate.py` - ActionState, BagState, ItemUsageState, MartState classes

**Helpers Package (NEW):**
- `helpers/pathhelpers.py` - Config/sprite path loading, JSON caching
- `helpers/decorators.py` - Session validation decorators (@require_*_state)
- `helpers/helpers.py` - General helper functions (getTrainerGivenPokemonName)

**Config Files:**
- `gyms.json` - All gym data (826 lines) - FIXED typos
- `quests.json` - Quest pre-requisites and blockers
- `locations.json` - Map data, connections, gym flags
- `pokemon.json` - All Pokemon data
- `moves.json` - Move data
- `typeEffectiveness.json` - Type matchup chart

## Git Commit History (Recent)

```
# Refactoring (2026-02-04)
97f2d81 Update encounters.py
df96e70 Update encounters.py
faccb40 Update enemyTrainers.json
e5f1adb Update encounters.py
8b9a8df Update encounters.py
[Commit] Fix MartState missing quantity attribute
[Commit] Fix ailments null constraint violation - add pokemonId to INSERT
[Commit] Fix make_hp_bar references to create_hp_bar
[Commit] Fix helpers package structure and imports
[Commit] Phase 7: Consolidate TrainerClass instantiation with caching
[Commit] Phase 6: Add create_hp_bar to functions.py
[Commit] Phase 4: Create session validation decorators
[Commit] Phase 3: Extract damage calculation to encounterclass
[Commit] Phase 2: Move state classes to models package
[Commit] Phase 1: Extract constants and path helpers
[Commit] Stable v1.0 - Pre-refactoring checkpoint

# Gym System (2026-02-02)
0a3ca86 Fix Pokemon name typos in gyms.json and add error handling
f5d6210 Fix 'This is not for you' error in gym battles
a0ad236 Add full gym battle system with UI and battle mechanics
9cf8563 Integrate battleclass.py gym progression system
69222c6 Fix config file path in battleclass and improve error messages
dbd1063 Fix gym leader loading logic flow
b096816 Integrate battleclass.py gym progression system into gym button
93300a7 Add gym challenge button to encounters
e1b9719 Fix quest buttons showing even when no encounter methods exist
33121f1 Add quest buttons to encounters based on location
50fad01 Refactor to use existing quests.locationBlocked() for consistency
4d9d341 Add 44 missing location names to LOCATION_DISPLAY_NAMES

# Earlier Work
7efe01d Always reload pokemon data (fix stale stats)
bccb9dd Fix interaction handling in fight
66693ce Remove old interaction.respond
7721723 Complete Discord API modernization (23 self.client + 13 edit_original)
899ab16 Channel None checks in encounters/trade
6967538 Map navigation button fixes
3d36471 Database connection and logging channel fixes
```

## Contact & Resources

**Repository:** https://github.com/joshuakohut77/discord-cogs.git
**Pokemon Sprites:** https://pokesprites.joshkohut.com/sprites/
**Discord Bot Framework:** https://docs.discord.red/en/stable/
**Discord.py Docs:** https://discordpy.readthedocs.io/

## Development Best Practices (Post-Refactoring)

### Code Organization Rules
Following the refactoring, new code should follow these patterns:

1. **Constants** → Always add to `constant.py`, never hardcode magic numbers
2. **State Classes** → Place in `models/` package (battlestate.py, sessionstate.py)
3. **UI Helpers** → Add to `functions.py` (embeds, formatters, visual elements)
4. **Business Logic** → Keep in `services/` (battle mechanics, trainer management)
5. **Utilities** → Add to `helpers/` (path helpers, decorators, general functions)
6. **Cog Mixins** → Keep focused on Discord interactions, delegate to services

### Prevent Future Duplication
- **Session Validation**: Use `@require_*_state()` decorators instead of inline checks
- **Config Loading**: Use `load_json_config()` from pathhelpers instead of manual file loading
- **HP Bars**: Use `create_hp_bar()` from functions.py
- **TrainerClass**: Use `self._get_trainer(user_id)` for cached instances
- **Damage Calculation**: Use `calculate_battle_damage()` from encounterclass

### Package Structure
All directories that contain Python modules must have `__init__.py`:
```python
# helpers/__init__.py
"""Helper utilities for Pokemon cog."""
from .helpers import getTrainerGivenPokemonName
__all__ = ['getTrainerGivenPokemonName']
```

### Module Exports
Use `__all__` to explicitly declare what functions are exported:
```python
# services/encounterclass.py
__all__ = ['encounter', 'calculate_battle_damage']
```

## Quick Start for New Session

1. **Verify Environment:**
   ```bash
   cd /home/legend/claude/discord-cogs/pokemon
   git status
   docker ps | grep pokebot
   ```

2. **Make Changes:**
   - Edit files in `/home/legend/claude/discord-cogs/pokemon`
   - Copy to `/home/legend/claude/docker/data/cogs/CogManager/cogs/pokemon`
   - Clear `__pycache__` directories
   - Run `,reload pokemon` in Discord

3. **Test:**
   - Use `,trainer encounter` to test encounters/gyms
   - Use `,trainer map` to test navigation
   - Check `docker logs pokebot` for errors

4. **Commit:**
   ```bash
   git add .
   git commit -m "Description"
   git push
   ```

---

**Last Updated:** 2026-02-05
**Claude Code Session ID:** 0ee0846d-4e1b-4e85-8f36-0e3121357aec
**Status:** Major refactoring complete - encounters.py reduced from 7,476 to 7,256 lines with improved architecture. Gym battle system fully functional, ready for enhancements.
