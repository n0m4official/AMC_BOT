import json
import nextcord
from nextcord.ext import commands

# Load config
with open("config.json") as f:
    config = json.load(f)

intents = nextcord.Intents.default()
intents.members = True
intents.message_content = True  # Needed for prefix commands (optional here)

bot = commands.Bot(command_prefix="/", intents=intents)  # prefix won't matter, using slash commands

# Load cog
try:
    bot.load_extension("cogs.membership_manager")
    print("✅ Loaded cogs.membership_manager")
except Exception as e:
    print(f"❌ Failed to load cogs.membership_manager: {e}")

@bot.event
async def on_ready():
    print(f"✅ Bot logged in as {bot.user}")

bot.run(config["token"])
