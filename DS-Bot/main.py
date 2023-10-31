import discord
from discord.ext import commands, tasks
from discord.ext.commands import has_permissions, MissingPermissions

from apikeys import BOT_TOKEN

client = commands.Bot(command_prefix='!', intents=discord.Intents.all())

MAX_ROLES_PER_MEMBER = 1

@client.event
async def on_ready():
    print("Bot is Online...")
    print("...................")

# Hello Command
@client.command()
async def Hello(ctx):
    await ctx.send("Hello, I am the Audiopitch bot.")

# Join Message
@client.event
async def on_member_join(member):
    channel = client.get_channel(1168399261172502571)
    await channel.send(f"Welcome To The Audidopitch Server <@{member.id}>, We hope you'll enjoy it here. \n\n To get a list of commands please refer to the [] text-channel!!")
    # if member.bot:
    #     await channel.send("Bots cannot receive DM's!!")
    #     return
    # try:
    #     await member.send("To register yourself as an Artist or Curator please type the following commands in the specified text channel: \n \n'!assign_role Artist' for Artists \n '!assign_role Curator' for Curators. \n \n If you're encounterring difficulties, please contact our admins in the server.")
    #     await channel.send(f"Welcome to the Audiopitch server <@{member.id}>, we hope you'll enjoy it here!! Please check your DM's for role assignment.")
    # except discord.Forbidden:
    #     await channel.send(f"Couldn't send a message to <@{member.id}>. Please make sure your DMs are open.")
# Leave Message
@client.event
async def on_member_remove(member):
    channel = client.get_channel(1168399261172502571)
    await channel.send(f"<@{member.id}> has left the server, sad to see you go.")

@client.command()
@has_permissions(kick_members=True)
async def Kick(ctx, member: discord.Member, *, reason=None):
    await member.kick(reason=reason)
    await ctx.send(f"User {member} has been kicked.")

@Kick.error
async def kick_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("You don't have permission to kick people!")

@client.command()
@has_permissions(ban_members=True)
async def Ban(ctx, member: discord.Member, *, reason=None):
    await member.ban(reason=reason)
    await ctx.send(f"User {member} has been banned.")

@Ban.error
async def ban_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("You don't have permission to ban people!")

##ROLE PICKING SYSTEM
class RoleButton(discord.ui.View):
    def __init__(self):
        super().__init__()
        self.add_item(discord.ui.Button(label="Artist", custom_id="Artist", style=discord.ButtonStyle.red))
        self.add_item(discord.ui.Button(label="Curator", custom_id="Pending", style=discord.ButtonStyle.blurple))

@client.command()
async def role_pick(ctx):
    view = RoleButton()
    message = await ctx.send('Please choose the role you are applying as:', view=view, ephemeral = True)

@client.event
async def on_interaction(interaction):
    if isinstance(interaction, discord.Interaction):
        if interaction.data['custom_id'] == 'Artist':
            await setRole(interaction)
            await remove_buttons(interaction)
        elif interaction.data['custom_id'] == 'Pending':
            await setRole(interaction)  # Set the "Pending" role
            await remove_buttons(interaction)

async def setRole(interaction):
    role_name = interaction.data['custom_id']
    member = interaction.user
    guild = interaction.guild
    mods = guild.get_role(1168399823205052436)
    roles = member.roles[1:]  # Exclude @everyone role

    if role_name == 'Pending':
        # Notify the user
        await interaction.response.send_message(f"Applying for Curator role requires additional steps.\n\nPlease submit the following information to the [] text-channel within at least 24 hours.\n\nThank You", ephemeral=True)

        # Notify moderators in a separate channel and tag them
        mod_channel = guild.get_channel(1168806364697608303)
        if mod_channel:
            await mod_channel.send(f"{member.mention} applied for the Curator role. Please review. {mods.mention}")

        return

    # For other roles
    role = discord.utils.get(guild.roles, name=role_name)
    if role:
        if role in roles:
            await interaction.response.send_message(f"You already have the {role_name} role.", ephemeral=True)
        else:
            await member.add_roles(role)
            await interaction.response.send_message(f"You've been assigned the {role_name} role.", ephemeral=True)
    else:
        await interaction.response.send_message(f"Role '{role_name}' not found.", ephemeral=True)


async def remove_buttons(interaction):
    # Fetch the message to update and remove the buttons
    message = await interaction.message.channel.fetch_message(interaction.message.id)
    await message.edit(view=None)

@role_pick.error
async def role_pick_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("You don't have permissions to use this command.")

    
@client.command()
@has_permissions(manage_roles=True)
async def addRole(ctx, user: discord.Member, *, role: discord.Role):
    if role in user.roles:
        await ctx.send(f"{user.mention} already has the role {role}.")
    else:
        await user.add_roles(role)
        await ctx.send(f"Added {role} to {user.mention}.")

@addRole.error
async def role_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("You do not have permission to use this command.")

@client.command()
@has_permissions(manage_roles=True)
async def removeRole(ctx, user: discord.Member, *, role: discord.Role):
    if role in user.roles:
        await user.remove_roles(role)
        await ctx.send(f"Removed {role} from {user.mention}.")
    else:
        await ctx.send(f"{user.mention} does not have the role {role}.")

@removeRole.error
async def removeRole_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("You do not have permission to use this command.")

client.run(BOT_TOKEN)
