# Pokemon TCG Collector — Setup Guide

## Directory Structure

You need **two** directory trees: the **cog** (lives in your Red bot cogs) and the **card data** (lives wherever you want on disk).

### Card Data (from bulk downloader)
```
/srv/pokemontcg/data/               ← configurable via !tcgset datadir
├── cards.json                       ← master metadata (all sets, all cards)
├── pack_config.json                 ← booster pack compositions (copy from cog)
├── base1/
│   ├── set_info.json
│   ├── base1_cards.json
│   └── 1.png ... 102.png
├── base2/
│   └── ...
├── base3/ ... base6/
├── gym1/
└── gym2/
```

### Red Bot Cog
```
<your_cogs_path>/pokemontcg/
├── __init__.py
├── info.json
├── main.py                          ← commands, embeds, DB ops
├── packopener.py                    ← pack opening engine
└── dbclass.py                       ← your existing DB wrapper
```

## Setup Steps

### 1. Run the bulk downloader
```bash
python3 pokemon_tcg_bulk.py
```
This creates the `pokemon_cards/` directory with all card images + metadata.

### 2. Place card data on server
```bash
sudo mkdir -p /srv/pokemontcg/data
sudo cp -r ./pokemon_cards/* /srv/pokemontcg/data/
# Copy pack_config.json from the cog into the data dir
sudo cp /path/to/cog/pokemontcg/pack_config.json /srv/pokemontcg/data/
```

### 3. Create the database tables
```bash
psql -h postgres_container -U redbot -d discord -f schema.sql
```

### 4. Install the cog
Copy the `pokemontcg/` cog folder into your Red bot's cog directory, then:
```
[p]load pokemontcg
```

### 5. Configure the data path
```
[p]tcgset datadir /srv/pokemontcg/data
```

## Commands

| Command | Description |
|---------|-------------|
| `!tcg packs` | Show all available booster packs |
| `!tcg open <set_id>` | Open a booster pack (e.g., `!tcg open base1`) |
| `!tcg stats` | View your collection stats |
| `!tcg stats @user` | View another user's stats |
| `!tcgset datadir <path>` | (Admin) Set card data directory |
| `!tcgset reload` | (Admin) Reload card data from disk |

## Pack Compositions (authentic WOTC era)

All packs contain **11 cards**.

| Set | Commons | Uncommons | Rare | Energy | Holo Chance |
|-----|---------|-----------|------|--------|-------------|
| Base Set | 5 | 3 | 1 | 2 | ~1/3 |
| Jungle | 7 | 3 | 1 | 0 | ~1/3 |
| Fossil | 7 | 3 | 1 | 0 | ~1/3 |
| Base Set 2 | 5 | 3 | 1 | 2 | ~1/3 |
| Team Rocket | 5 | 3 | 1 | 2 | ~1/3 |
| Legendary Coll. | 5 | 3 | 1 | 2 | ~1/3 |
| Gym Heroes | 5 | 3 | 1 | 2 | ~1/3 |
| Gym Challenge | 5 | 3 | 1 | 2 | ~1/3 |

Jungle and Fossil don't have Energy cards in the set, so those 2 slots are replaced with extra Commons (7 total).

## Database Schema

Two tables + two views:

- **tcg_pack_opens** — Log of every pack opened (who, when, which set)
- **tcg_user_cards** — Every card pulled (one row per card per pull, dupes = multiple rows)
- **tcg_collection_summary** (view) — Aggregated stats per user per set
- **tcg_pack_stats** (view) — Pack opening counts per user per set