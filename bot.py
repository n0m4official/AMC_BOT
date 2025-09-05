import json
import nextcord
from nextcord.ext import commands

with open("config.json") as f:
    config = json.load(f)

intents = nextcord.Intents.default()
intents.members = True  # required to detect new member joins

bot = commands.Bot(command_prefix="!", intents=intents)

# Load cog
bot.load_extension("cogs.membership_manager")

@bot.event
async def on_ready():
    print(f"Bot logged in as {bot.user}")

bot.run(config["token"])
