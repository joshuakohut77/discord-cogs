# Dank Hall - Discord Hall of Fame Cog

A comprehensive Hall of Fame system for Red Discord Bot that automatically tracks and celebrates the best messages in your server based on community reactions.

## Features

✨ **Automatic Certification** - Messages are automatically certified when they reach a configured reaction threshold

🎯 **Flexible Configuration** - Set global defaults and per-channel overrides for thresholds and hall channels

🚫 **Blacklisting** - Exclude specific channels from the certification system

📊 **Comprehensive Statistics** - Track user rankings, channel activity, popular emojis, and more

🏆 **Leaderboards** - See who has the most certified posts with detailed breakdowns

✋ **Manual Certification** - Manually certify messages that might have been missed

💾 **Database Tracking** - Uses PostgreSQL to prevent duplicates and maintain historical records

## Installation

```bash
# Add your cog repository
[p]repo add mycogs <repo-url>

# Install the cog
[p]cog install mycogs DankHall

# Load the cog
[p]load DankHall
```

## Database Setup

This cog requires a PostgreSQL database connection configured in your `dbclass.py` file. The cog will automatically create the necessary tables on first load.

### Required Table
The cog creates this table automatically:

```sql
CREATE TABLE dank_certified_messages (
    message_id BIGINT PRIMARY KEY,
    guild_id BIGINT NOT NULL,
    channel_id BIGINT NOT NULL,
    user_id BIGINT NOT NULL,
    emoji TEXT NOT NULL,
    reaction_count INTEGER NOT NULL,
    hall_message_id BIGINT,
    certified_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## Configuration Commands

All configuration commands require `Manage Server` permission.

### Basic Setup

```bash
# Enable/disable the system
[p]dankhall enable true|false

# Set the default reaction threshold (how many reactions needed)
[p]dankhall threshold 5

# Set the default hall of fame channel
[p]dankhall channel #hall-of-fame
```

### Channel-Specific Overrides

```bash
# Set a custom threshold for a specific channel
[p]dankhall setchannel #memes 10

# Set both custom threshold AND custom hall channel
[p]dankhall setchannel #elite-memes 15 #ultra-hall

# Remove all overrides for a channel
[p]dankhall resetchannel #memes
```

### Blacklisting

```bash
# Prevent a channel from getting certifications
[p]dankhall blacklist #no-hall-channel

# Remove from blacklist
[p]dankhall unblacklist #no-hall-channel
```

### Emoji Management

By default, ALL emojis can trigger certification. You can restrict it to specific emojis:

```bash
# Add an emoji to the allowed list (both unicode and custom emojis work)
[p]dankhall addemoji 🔥
[p]dankhall addemoji :custom_emoji:

# Remove an emoji from the allowed list
[p]dankhall removeemoji 🔥

# Note: Once you add ANY emoji, ONLY those emojis will trigger certification
```

### Response Messages

Customize what the bot says when a post gets certified:

```bash
# Add a response
[p]dankhall addresponse "🎉 Certified Dank!"

# Remove a response
[p]dankhall removeresponse "🎉 Certified Dank!"
```

### View Settings

```bash
# View all current settings
[p]dankhall settings
```

## Statistics Commands

### User Statistics

```bash
# View your own stats
[p]dankhall stats user

# View another user's stats
[p]dankhall stats user @username

# Shows:
# - Total certifications
# - Top emojis used
# - Server rank
```

### Leaderboards

```bash
# Top 10 users (default)
[p]dankhall stats leaderboard

# Top 25 users
[p]dankhall stats leaderboard 25

# Aliases: [p]dankhall stats top, [p]dankhall stats lb
```

### Channel Statistics

```bash
# See which channels have the most certified posts
[p]dankhall stats channels

# Limit to top 5
[p]dankhall stats channels 5
```

### Emoji Statistics

```bash
# See the most popular certification emojis
[p]dankhall stats emojis

# Limit to top 5
[p]dankhall stats emojis 5
```

### Server Overview

```bash
# Get overall server statistics
[p]dankhall stats server

# Shows:
# - Total certifications
# - Top user
# - Most popular emoji
```

## Manual Certification

Sometimes messages get missed by the bot (deleted reactions, bot downtime, etc.). You can manually certify them:

```bash
# Manually certify a message
[p]dankhall certify #channel message_id emoji

# Example:
[p]dankhall certify #memes 123456789012345678 🔥

# Notes:
# - The message must exist in the specified channel
# - It will be posted to the appropriate hall of fame channel
# - It cannot already be certified
# - Reaction count will be shown as "Manual" in the embed
```

## How It Works

1. **User reacts** to a message with an emoji
2. **Bot checks** if the reaction count meets the threshold
3. **Bot verifies** the channel isn't blacklisted and the emoji is allowed
4. **Bot certifies** the message by:
   - Replying with a random response message
   - Creating a detailed embed with message info
   - Posting to the hall of fame channel
   - Recording in the database to prevent duplicates

## Example Configuration

Here's a typical setup for a server:

```bash
# Basic setup
[p]dankhall enable true
[p]dankhall threshold 5
[p]dankhall channel #hall-of-fame

# Channel overrides - higher quality channels need more reactions
[p]dankhall setchannel #casual-memes 5
[p]dankhall setchannel #top-tier-memes 10 #elite-hall
[p]dankhall setchannel #legendary-memes 20 #legendary-hall

# Blacklist administrative channels
[p]dankhall blacklist #announcements
[p]dankhall blacklist #rules

# Restrict to specific emojis
[p]dankhall addemoji 🔥
[p]dankhall addemoji ⭐
[p]dankhall addemoji :custom_stonks:
```

## Troubleshooting

### Messages aren't getting certified

1. Check if the system is enabled: `[p]dankhall settings`
2. Verify the threshold is set correctly
3. Confirm the channel isn't blacklisted
4. Check if emoji restrictions are blocking it
5. Verify the bot has permissions in the hall channel

### Database errors

- Ensure PostgreSQL is running and accessible
- Check your `dbclass.py` configuration
- Verify the bot can create tables (requires appropriate permissions)

### Duplicate certifications

The cog prevents duplicates by checking the database before certifying. If you see duplicates:
- Check database connectivity
- Verify the table was created successfully

## Permissions Required

- **Read Messages** - To detect reactions
- **Send Messages** - To reply and post to hall
- **Embed Links** - For hall of fame posts
- **Read Message History** - To fetch message details

## Support

For issues or feature requests, please open an issue on the repository.

## Changelog

### Version 2.0.0
- Complete rewrite with cleaner architecture
- Added PostgreSQL database integration
- Added comprehensive statistics system
- Added manual certification command
- Added per-channel configuration overrides
- Improved duplicate prevention
- Better error handling
- Cleaner code organization

### Version 1.0.0
- Initial release
- Basic certification system
- Configuration commands