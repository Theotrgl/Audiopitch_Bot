import discord
from discord.ext import commands
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
    if member.bot:
        await channel.send("Bots cannot receive DM's!!")
        return
    try:
        await member.send("To register yourself as an Artist or Curator please type the following commands in the specified text channel: \n \n'!assign_role Artist' for Artists \n '!assign_role Curator' for Curators. \n \n If you're encounterring difficulties, please contact our admins in the server.")
        await channel.send(f"Welcome to the Audiopitch server <@{member.id}>, we hope you'll enjoy it here!! Please check your DM's for role assignment.")
    except discord.Forbidden:
        await channel.send(f"Couldn't send a message to <@{member.id}>. Please make sure your DMs are open.")
# Leave Message
@client.event
async def on_member_remove(member):
    channel = client.get_channel(1168399261172502571)
    await channel.send(f"<@{member.id}> has left the server, sad to see you go.")

# @client.event
# async def on_message(message):
#     if message.author == client.user:
#         return  # Ignore bot's own messages

#     with open('profanity_wordlist.txt', 'r') as file:
#         banned_words = [word.strip() for word in file.readlines()]

#     for word in banned_words:
#         if word.lower() in message.content.lower():
#             await message.delete()
#             await message.channel.send("Please keep the server profanity-free.")
#             break

#     await client.process_commands(message)

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

@client.command()
async def assign_role(ctx, *, role_name):
    member = ctx.author
    roles = member.roles[1:]  # Exclude @everyone role

    if len(roles) >= MAX_ROLES_PER_MEMBER:
        await ctx.send(f"You've reached the maximum limit of roles ({MAX_ROLES_PER_MEMBER}).")
        return

    role = discord.utils.get(ctx.guild.roles, name=role_name)
    if role:
        if role in roles:
            await ctx.send(f"You already have the {role_name} role.")
        else:
            await member.add_roles(role)
            await ctx.send(f"You've been assigned the {role_name} role.")
    else:
        await ctx.send(f"Role '{role_name}' not found.")
@assign_role.error
async def assign_role_error(ctx, error):
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
