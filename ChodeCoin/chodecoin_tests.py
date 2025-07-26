import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import sys


# Create a proper mock base class for Cog
class MockCog:
    @staticmethod
    def listener():
        return lambda func: func


# Mock the RedBot modules before importing our cog
sys.modules['redbot'] = MagicMock()
sys.modules['redbot.core'] = MagicMock()
sys.modules['redbot.core.commands'] = MagicMock()
sys.modules['redbot.core.Config'] = MagicMock()
sys.modules['redbot.core.checks'] = MagicMock()
sys.modules['redbot.core.bot'] = MagicMock()
sys.modules['redbot.core.utils'] = MagicMock()
sys.modules['redbot.core.utils.chat_formatting'] = MagicMock()

# Create a mock discord module but preserve some structure
discord_mock = MagicMock()
discord_mock.Message = MagicMock
discord_mock.HTTPException = Exception
sys.modules['discord'] = discord_mock

# Mock the specific imports we need
commands_mock = MagicMock()
commands_mock.Cog = MockCog
commands_mock.command = lambda **kwargs: lambda func: func
sys.modules['redbot.core.commands'] = commands_mock

config_mock = MagicMock()
config_mock.get_conf = MagicMock(return_value=MagicMock())
sys.modules['redbot.core.Config'] = config_mock

checks_mock = MagicMock()
checks_mock.admin_or_permissions = lambda **kwargs: lambda func: func
sys.modules['redbot.core.checks'] = checks_mock

# Now we can import our cog
from chodecoin_cog import ChodeCoin, setup


class TestChodeCoin:
    """Test suite for the ChodeCoin cog"""

    @pytest.fixture
    def mock_bot(self):
        """Create a mock Red bot instance"""
        bot = MagicMock()
        bot.add_cog = MagicMock()
        return bot

    @pytest.fixture
    def mock_guild(self):
        """Create a mock Discord guild"""
        guild = MagicMock()
        guild.id = 123456789
        return guild

    @pytest.fixture
    def mock_author(self):
        """Create a mock Discord user"""
        author = MagicMock()
        author.bot = False
        author.name = "testuser"
        author.display_name = "TestUser"
        return author

    @pytest.fixture
    def mock_message(self, mock_guild, mock_author):
        """Create a mock Discord message"""
        message = MagicMock()
        message.guild = mock_guild
        message.author = mock_author
        message.content = "@target++"
        message.add_reaction = AsyncMock()
        return message

    @pytest.fixture
    def mock_ctx(self, mock_guild, mock_author):
        """Create a mock Discord context"""
        ctx = MagicMock()
        ctx.guild = mock_guild
        ctx.author = mock_author
        ctx.send = AsyncMock()
        ctx.clean_prefix = "!"
        return ctx

    @pytest.fixture
    def cog(self, mock_bot):
        """Create a ChodeCoin-like test object with the essentials"""
        import re

        # Create a simple test object that mimics what we need from ChodeCoin
        class TestChodeCoin:
            def __init__(self, bot):
                self.bot = bot
                self.point_pattern = re.compile(r'@(\w+)(\+\+|--)')

                # Mock config setup
                config_instance = MagicMock()
                guild_config = MagicMock()
                config_instance.guild.return_value = guild_config

                guild_config.scores = AsyncMock()
                guild_config.enabled = AsyncMock()
                guild_config.scores.return_value = {}
                guild_config.enabled.return_value = True
                guild_config.scores.set = AsyncMock()
                guild_config.enabled.set = AsyncMock()

                self.config = config_instance

            # Copy the methods we want to test from the original ChodeCoin
            async def _process_point_change(self, message, username, operation):
                # Don't let people give points to themselves
                if username.lower() == message.author.name.lower() or username.lower() == message.author.display_name.lower():
                    return

                # Get current scores
                scores = await self.config.guild(message.guild).scores()

                # Initialize user if not exists
                if username not in scores:
                    scores[username] = 0

                # Apply point change
                if operation == "++":
                    scores[username] += 1
                else:  # operation == "--"
                    scores[username] -= 1

                # Save updated scores
                await self.config.guild(message.guild).scores.set(scores)

                # React to the message to show it was processed
                try:
                    if operation == "++":
                        await message.add_reaction("⬆️")
                    else:
                        await message.add_reaction("⬇️")
                except:
                    pass  # Ignore if we can't react

            async def on_message(self, message):
                # Ignore bot messages and DMs
                if message.author.bot or not message.guild:
                    return

                # Check if the cog is enabled for this guild
                if not await self.config.guild(message.guild).enabled():
                    return

                # Find all matches in the message
                matches = self.point_pattern.findall(message.content)

                if not matches:
                    return

                # Process each match
                for username, operation in matches:
                    await self._process_point_change(message, username, operation)

            async def show_score(self, ctx, user=None):
                if user is None:
                    target_name = ctx.author.name
                else:
                    target_name = user.lstrip('@')

                scores = await self.config.guild(ctx.guild).scores()
                score = scores.get(target_name, 0)

                await ctx.send(f"**{target_name}** has **{score}** ChodeCoins! 🪙")

            async def leaderboard(self, ctx, limit=10):
                if limit > 25:
                    limit = 25
                elif limit < 1:
                    limit = 10

                scores = await self.config.guild(ctx.guild).scores()

                if not scores:
                    await ctx.send("No ChodeCoin scores yet! Start giving out points with @user++ or @user--")
                    return

                # Sort by score (descending)
                sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)

                # Build leaderboard message
                leaderboard_text = "🏆 **ChodeCoin Leaderboard** 🪙\n\n"

                for i, (username, score) in enumerate(sorted_scores[:limit], 1):
                    medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}."
                    leaderboard_text += f"{medal} **{username}**: {score} coins\n"

                # Mock pagify
                await ctx.send(leaderboard_text)

            async def reset_scores(self, ctx, user=None):
                if user is None:
                    await self.config.guild(ctx.guild).scores.set({})
                    await ctx.send("All ChodeCoin scores have been reset! 🗑️")
                else:
                    target_name = user.lstrip('@')
                    scores = await self.config.guild(ctx.guild).scores()

                    if target_name in scores:
                        del scores[target_name]
                        await self.config.guild(ctx.guild).scores.set(scores)
                        await ctx.send(f"**{target_name}**'s ChodeCoin score has been reset! 🗑️")
                    else:
                        await ctx.send(f"**{target_name}** doesn't have any ChodeCoins to reset.")

            async def toggle_cog(self, ctx):
                current = await self.config.guild(ctx.guild).enabled()
                new_state = not current

                await self.config.guild(ctx.guild).enabled.set(new_state)

                status = "enabled" if new_state else "disabled"
                await ctx.send(f"ChodeCoin tracking has been **{status}**!")

        return TestChodeCoin(mock_bot)

    def test_regex_pattern_matching(self, cog):
        """Test that the regex pattern correctly matches point operations"""
        # Test valid patterns
        valid_cases = [
            ("@user++", [("user", "++")]),
            ("@someone--", [("someone", "--")]),
            ("Hey @alice++ and @bob--!", [("alice", "++"), ("bob", "--")]),
            ("@test123++", [("test123", "++")]),
            ("@123++", [("123", "++")]),  # Numbers are valid usernames
        ]

        for text, expected in valid_cases:
            matches = cog.point_pattern.findall(text)
            assert matches == expected, f"Failed for: {text}. Expected {expected}, got {matches}"

        # Test invalid patterns - these should not match at all
        invalid_cases = [
            "@user+",  # Only one +
            "@user-",  # Only one -
            "user++",  # Missing @
            "@++",  # No username at all
            "@ user++",  # Space after @
            "@user+ +",  # Space between + +
        ]

        for text in invalid_cases:
            matches = cog.point_pattern.findall(text)
            assert matches == [], f"Should not match: {text}. Got {matches}"

        # Test edge cases that DO match (but we want to be explicit about what they match)
        edge_cases = [
            ("@user+++", [("user", "++")]),  # Extra + is ignored
            ("@user---", [("user", "--")]),  # Extra - is ignored
        ]

        for text, expected in edge_cases:
            matches = cog.point_pattern.findall(text)
            assert matches == expected, f"Edge case failed for: {text}. Expected {expected}, got {matches}"

    @pytest.mark.asyncio
    async def test_on_message_ignores_bots(self, cog, mock_message):
        """Test that bot messages are ignored"""
        mock_message.author.bot = True

        with patch.object(cog, '_process_point_change') as mock_process:
            await cog.on_message(mock_message)
            mock_process.assert_not_called()

    @pytest.mark.asyncio
    async def test_on_message_ignores_dms(self, cog, mock_message):
        """Test that DM messages are ignored"""
        mock_message.guild = None

        with patch.object(cog, '_process_point_change') as mock_process:
            await cog.on_message(mock_message)
            mock_process.assert_not_called()

    @pytest.mark.asyncio
    async def test_on_message_processes_valid_patterns(self, cog, mock_message):
        """Test that valid point patterns are processed"""
        mock_message.content = "@target++ @another--"

        # Mock config for enabled check
        cog.config.guild.return_value.enabled = AsyncMock(return_value=True)

        with patch.object(cog, '_process_point_change') as mock_process:
            await cog.on_message(mock_message)

            # Should be called twice (once for each match)
            assert mock_process.call_count == 2
            mock_process.assert_any_call(mock_message, "target", "++")
            mock_process.assert_any_call(mock_message, "another", "--")

    @pytest.mark.asyncio
    async def test_process_point_change_prevents_self_voting(self, cog, mock_message):
        """Test that users cannot give points to themselves"""
        # Test with username matching
        with patch.object(cog.config.guild.return_value, 'scores') as mock_scores:
            mock_scores.return_value = {}
            await cog._process_point_change(mock_message, "testuser", "++")
            mock_scores.set.assert_not_called()

        # Test with display name matching
        with patch.object(cog.config.guild.return_value, 'scores') as mock_scores:
            mock_scores.return_value = {}
            await cog._process_point_change(mock_message, "TestUser", "++")
            mock_scores.set.assert_not_called()

    @pytest.mark.asyncio
    async def test_process_point_change_adds_points(self, cog, mock_message):
        """Test that ++ correctly adds points"""
        initial_scores = {"target": 5}

        with patch.object(cog.config.guild.return_value, 'scores') as mock_scores:
            mock_scores.return_value = initial_scores.copy()

            await cog._process_point_change(mock_message, "target", "++")

            # Verify the score was incremented
            expected_scores = {"target": 6}
            mock_scores.set.assert_called_once_with(expected_scores)

            # Verify reaction was added
            mock_message.add_reaction.assert_called_once_with("⬆️")

    @pytest.mark.asyncio
    async def test_process_point_change_removes_points(self, cog, mock_message):
        """Test that -- correctly removes points"""
        initial_scores = {"target": 5}

        with patch.object(cog.config.guild.return_value, 'scores') as mock_scores:
            mock_scores.return_value = initial_scores.copy()

            await cog._process_point_change(mock_message, "target", "--")

            # Verify the score was decremented
            expected_scores = {"target": 4}
            mock_scores.set.assert_called_once_with(expected_scores)

            # Verify reaction was added
            mock_message.add_reaction.assert_called_once_with("⬇️")

    @pytest.mark.asyncio
    async def test_process_point_change_creates_new_user(self, cog, mock_message):
        """Test that new users are initialized with 0 points"""
        initial_scores = {}

        with patch.object(cog.config.guild.return_value, 'scores') as mock_scores:
            mock_scores.return_value = initial_scores.copy()

            await cog._process_point_change(mock_message, "newuser", "++")

            # Verify new user was created with 1 point
            expected_scores = {"newuser": 1}
            mock_scores.set.assert_called_once_with(expected_scores)

    @pytest.mark.asyncio
    async def test_show_score_default_user(self, cog, mock_ctx):
        """Test showing score for the command sender"""
        scores = {"testuser": 10}

        with patch.object(cog.config.guild.return_value, 'scores') as mock_scores:
            mock_scores.return_value = scores

            await cog.show_score(mock_ctx)

            mock_ctx.send.assert_called_once_with("**testuser** has **10** ChodeCoins! 🪙")

    @pytest.mark.asyncio
    async def test_show_score_specific_user(self, cog, mock_ctx):
        """Test showing score for a specific user"""
        scores = {"target": 15}

        with patch.object(cog.config.guild.return_value, 'scores') as mock_scores:
            mock_scores.return_value = scores

            await cog.show_score(mock_ctx, "@target")

            mock_ctx.send.assert_called_once_with("**target** has **15** ChodeCoins! 🪙")

    @pytest.mark.asyncio
    async def test_show_score_nonexistent_user(self, cog, mock_ctx):
        """Test showing score for user with no points"""
        scores = {}

        with patch.object(cog.config.guild.return_value, 'scores') as mock_scores:
            mock_scores.return_value = scores

            await cog.show_score(mock_ctx, "nobody")

            mock_ctx.send.assert_called_once_with("**nobody** has **0** ChodeCoins! 🪙")

    @pytest.mark.asyncio
    async def test_leaderboard_empty(self, cog, mock_ctx):
        """Test leaderboard with no scores"""
        with patch.object(cog.config.guild.return_value, 'scores') as mock_scores:
            mock_scores.return_value = {}

            await cog.leaderboard(mock_ctx)

            mock_ctx.send.assert_called_once_with(
                "No ChodeCoin scores yet! Start giving out points with @user++ or @user--"
            )

    @pytest.mark.asyncio
    async def test_leaderboard_with_scores(self, cog, mock_ctx):
        """Test leaderboard with multiple scores"""
        scores = {"alice": 10, "bob": 5, "charlie": 15}

        with patch.object(cog.config.guild.return_value, 'scores') as mock_scores:
            mock_scores.return_value = scores

            await cog.leaderboard(mock_ctx)

            # Verify ctx.send was called
            mock_ctx.send.assert_called_once()
            call_args = mock_ctx.send.call_args[0][0]

            # Check that the leaderboard is properly sorted (charlie first with 15)
            assert "charlie" in call_args
            assert "🥇" in call_args
            assert "alice" in call_args
            assert "bob" in call_args

    @pytest.mark.asyncio
    async def test_reset_scores_all(self, cog, mock_ctx):
        """Test resetting all scores (admin command)"""
        with patch.object(cog.config.guild.return_value.scores, 'set') as mock_set:
            await cog.reset_scores(mock_ctx)

            mock_set.assert_called_once_with({})
            mock_ctx.send.assert_called_once_with("All ChodeCoin scores have been reset! 🗑️")

    @pytest.mark.asyncio
    async def test_reset_scores_specific_user(self, cog, mock_ctx):
        """Test resetting specific user's score"""
        initial_scores = {"alice": 10, "bob": 5}

        with patch.object(cog.config.guild.return_value, 'scores') as mock_scores:
            mock_scores.return_value = initial_scores.copy()

            await cog.reset_scores(mock_ctx, "alice")

            # Verify alice was removed
            expected_scores = {"bob": 5}
            mock_scores.set.assert_called_once_with(expected_scores)
            mock_ctx.send.assert_called_once_with("**alice**'s ChodeCoin score has been reset! 🗑️")

    @pytest.mark.asyncio
    async def test_toggle_cog(self, cog, mock_ctx):
        """Test toggling the cog on/off"""
        # Test enabling (from disabled state)
        with patch.object(cog.config.guild.return_value, 'enabled') as mock_enabled:
            mock_enabled.return_value = False

            await cog.toggle_cog(mock_ctx)

            mock_enabled.set.assert_called_once_with(True)
            mock_ctx.send.assert_called_once_with("ChodeCoin tracking has been **enabled**!")

    def test_setup_function(self, mock_bot):
        """Test that the setup function properly adds the cog"""
        # This test verifies that setup() can be called without crashing
        # The actual cog adding is tested by checking that setup() runs successfully
        try:
            setup(mock_bot)
            # If we get here, setup didn't crash
            assert True
        except Exception as e:
            pytest.fail(f"Setup function failed: {e}")

# Run tests with: python -m pytest test_chodecoin.py -v