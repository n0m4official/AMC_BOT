import datetime
import json
import nextcord
from nextcord.ext import commands, menus

# Load config
with open("config.json") as f:
    config = json.load(f)

# Pagination for pending members
class PendingMenu(menus.ListPageSource):
    def __init__(self, data):
        super().__init__(data, per_page=10)

    async def format_page(self, menu, page):
        description = "\n".join(page)
        return nextcord.Embed(title="Pending Members", description=description, color=0x00ff00)

class MembershipManager(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def notify_admins(self, guild, message: str):
        log_channel = guild.get_channel(config.get("log_channel"))
        if log_channel:
            await log_channel.send(message)

    async def safe_dm(self, member, message: str):
        try:
            await member.send(message)
        except nextcord.Forbidden:
            await self.notify_admins(member.guild, f"Could not DM {member.mention} (DMs disabled).")

    @commands.Cog.listener()
    async def on_member_join(self, member: nextcord.Member):
        guild = member.guild
        account_age = (datetime.datetime.utcnow() - member.created_at).days

        flagged_role = nextcord.utils.get(guild.roles, name=config["roles"]["flagged"])
        pending_role = nextcord.utils.get(guild.roles, name=config["roles"]["pending"])

        if account_age < 30:
            if flagged_role:
                await member.add_roles(flagged_role)
            await self.notify_admins(
                guild,
                f"{member.mention} joined with a new account ({account_age} days old). Flagged for review."
            )
            await self.safe_dm(member, "Welcome! Your account is too new to be auto-approved. Admins will review your membership.")
        else:
            if pending_role:
                await member.add_roles(pending_role)
            await self.notify_admins(
                guild,
                f"{member.mention} joined and was assigned Pending."
            )
            await self.safe_dm(member, "Welcome! You’ve been placed in pending verification. An admin will confirm your membership soon.")

    @commands.command()
    @commands.has_permissions(manage_roles=True)
    async def approve(self, ctx, member: nextcord.Member):
        """Approve a pending member and move them to Verified Member."""
        verified_role = nextcord.utils.get(ctx.guild.roles, name=config["roles"]["verified"])
        pending_role = nextcord.utils.get(ctx.guild.roles, name=config["roles"]["pending"])

        if verified_role:
            await member.add_roles(verified_role)
        if pending_role and pending_role in member.roles:
            await member.remove_roles(pending_role)

        await ctx.send(f"{member.mention} has been approved and verified.")
        await self.notify_admins(ctx.guild, f"{member.mention} was approved by {ctx.author.mention}.")
        await self.safe_dm(member, "Your membership has been approved. Welcome!")

    @commands.command()
    @commands.has_permissions(manage_roles=True)
    async def pending(self, ctx):
        """List all members currently in the Pending role, paginated."""
        pending_role = nextcord.utils.get(ctx.guild.roles, name=config["roles"]["pending"])
        if not pending_role:
            await ctx.send("Pending role not found.")
            return

        pending_members = [member.mention for member in pending_role.members]
        if not pending_members:
            await ctx.send("There are currently no members pending verification.")
            return

        pages = [pending_members[i:i + 10] for i in range(0, len(pending_members), 10)]
        menu = menus.MenuPages(source=PendingMenu(pages), clear_reactions_after=True)
        await menu.start(ctx)

def setup(bot):
    bot.add_cog(MembershipManager(bot))
