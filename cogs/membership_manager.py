import datetime
import json
import nextcord
from nextcord.ext import commands
from nextcord import ui

# Load config
with open("config.json") as f:
    config = json.load(f)

# Pagination for pending members
class PendingView(ui.View):
    def __init__(self, pages):
        super().__init__(timeout=120)
        self.pages = pages
        self.current_page = 0

    async def update_message(self, interaction: nextcord.Interaction):
        description = "\n".join(self.pages[self.current_page])
        embed = nextcord.Embed(
            title=f"Pending Members (Page {self.current_page+1}/{len(self.pages)})",
            description=description,
            color=0x00ff00
        )
        await interaction.response.edit_message(embed=embed, view=self)

    @ui.button(label="Previous", style=nextcord.ButtonStyle.secondary)
    async def previous(self, button: ui.Button, interaction: nextcord.Interaction):
        if self.current_page > 0:
            self.current_page -= 1
            await self.update_message(interaction)

    @ui.button(label="Next", style=nextcord.ButtonStyle.secondary)
    async def next(self, button: ui.Button, interaction: nextcord.Interaction):
        if self.current_page < len(self.pages)-1:
            self.current_page += 1
            await self.update_message(interaction)

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
        account_age = (datetime.datetime.utcnow() - member.created_at.replace(tzinfo=None)).days

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

    @nextcord.slash_command(name="approve", description="Approve a pending member")
    async def approve(self, interaction: nextcord.Interaction, member: nextcord.Member):
        verified_role = nextcord.utils.get(interaction.guild.roles, name=config["roles"]["verified"])
        pending_role = nextcord.utils.get(interaction.guild.roles, name=config["roles"]["pending"])

        if verified_role:
            await member.add_roles(verified_role)
        if pending_role and pending_role in member.roles:
            await member.remove_roles(pending_role)

        await interaction.response.send_message(f"{member.mention} has been approved and verified.", ephemeral=True)
        await self.notify_admins(interaction.guild, f"{member.mention} was approved by {interaction.user.mention}.")
        await self.safe_dm(member, "Your membership has been approved. Welcome!")

    @nextcord.slash_command(name="pending", description="List members pending verification")
    async def pending(self, interaction: nextcord.Interaction):
        pending_role = nextcord.utils.get(interaction.guild.roles, name=config["roles"]["pending"])
        if not pending_role:
            await interaction.response.send_message("Pending role not found.", ephemeral=True)
            return

        pending_members = [member.mention for member in pending_role.members]
        if not pending_members:
            await interaction.response.send_message("There are currently no members pending verification.", ephemeral=True)
            return

        pages = [pending_members[i:i+10] for i in range(0, len(pending_members), 10)]
        embed = nextcord.Embed(
            title=f"Pending Members (Page 1/{len(pages)})",
            description="\n".join(pages[0]),
            color=0x00ff00
        )
        await interaction.response.send_message(embed=embed, view=PendingView(pages), ephemeral=True)


def setup(bot):
    bot.add_cog(MembershipManager(bot))
