import discord
import json
from discord.ext import commands, tasks
from discord.ext.commands import has_permissions, MissingPermissions


from apikeys import BOT_TOKEN

client = commands.Bot(command_prefix='!', intents=discord.Intents.all())

MAX_ROLES_PER_MEMBER = 1
role_message_id = None

@client.event
async def on_ready():
    global role_message_id
    print("Bot is Online...")
    print("...................")

    # Fetch the channel where you want to send the role selection message
    channel = client.get_channel(1168815727516590081)

    role_message = await channel.send("React to assign yourself a role!\n\n"
                                      "Artist - :artist:\n"
                                      "Curator - :curator:")

    # Add reactions to the message
    await role_message.add_reaction("🎨")  # Artist emoji
    await role_message.add_reaction("🔍")  # Curator emoji

    role_message_id = role_message.id 

# Hello Command
@client.command()
async def Hello(ctx):
    await ctx.send("Hello, I am the Audiopitch bot.")

#GREETINGS AND LEAVE PROMPT
# Join Message
@client.event
async def on_member_join(member):
    channel = client.get_channel(1168815727516590081)
    await channel.send(f"Welcome To The Audidopitch Server <@{member.id}>, We hope you'll enjoy it here. \n\n To get a list of commands please refer to the [] text-channel!!")

# Leave Message
@client.event
async def on_member_remove(member):
    channel = client.get_channel(1168815727516590081)
    await channel.send(f"<@{member.id}> has left the server, sad to see you go.")

#KICK AND BAN FUNCTIONS
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
# Load selected roles from JSON file
def load_selected_roles():
    try:
        with open("selected_roles.json", "r") as file:
            return json.load(file)
    except FileNotFoundError:
        return {}

# Save selected roles to JSON file
def save_selected_roles(selected_roles):
    with open('selected_roles.json', 'w') as file:
        json.dump(selected_roles, file)


# Load the selected roles from the JSON file
selected_roles = load_selected_roles()

@client.event
async def on_raw_reaction_add(payload):
    global role_message_id
    channel = client.get_channel(payload.channel_id)
    if channel.id == 1168815727516590081:  # Check if the reaction is in the specific channel
        guild = client.get_guild(payload.guild_id)
        member = guild.get_member(payload.user_id)
        user_id = str(member.id)

        if user_id in selected_roles:
            # User has already selected a role, prevent any additional changes
            return

        if payload.message_id == role_message_id:
            if str(payload.emoji) == '🎨':  # Artist emoji
                role = discord.utils.get(guild.roles, name="Artist")
            elif str(payload.emoji) == '🔍':  # Curator emoji
                role = discord.utils.get(guild.roles, name="Pending")
                if role:
                    await member.add_roles(role)
                    if role.name == 'Pending':
                        # For 'Pending' role, send additional steps message
                        await member.send(f"Choosing the Curator role requires additional steps. Please refer to the designated channel.")
                        
                        # Notify moderators in a separate channel
                        mod_channel = guild.get_channel(1168806364697608303)  # Replace MODERATOR_CHANNEL_ID with the actual channel ID
                        if mod_channel:
                            mods = discord.utils.get(guild.roles, name="kont")  # Assuming there is a role named "Moderators"
                            if mods:
                                await mod_channel.send(f"{member.mention} applied for the Curator role. Please review. {mods.mention}")
                            else:
                                print("Moderators role not found.")
                        else:
                            print("Moderator channel not found.")
                    else:
                        await member.send(f"You've been assigned the {role.name} role.")

                    selected_roles[user_id] = role.name  # Store the user and their selected role
                    save_selected_roles(selected_roles)  # Save the updated data to the JSON file
                else:
                    print("Role not found.")  # Handle role not found scenario



#ROLE ADDING AND REMOVING FOR MODS
@client.command()
@has_permissions(manage_roles=True)
async def addRole(ctx, user: discord.Member, *, role: discord.Role):
    if role in user.roles:
        await ctx.send(f"{user.mention} already has the role {role}.")
    else:
        await user.add_roles(role)
        await ctx.send(f"Added {role} to {user.mention}.")

        # Update selected_roles data
        user_id = str(user.id)
        if user_id not in selected_roles:
            selected_roles[user_id] = []

        selected_roles[user_id].append(role.name)
        save_selected_roles(selected_roles)

@addRole.error
async def addRole_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("You do not have permission to use this command.")

@client.command()
@has_permissions(manage_roles=True)
async def removeRole(ctx, user: discord.Member, *, role: discord.Role):
    user_id = str(user.id)
    
    if role in user.roles:
        await user.remove_roles(role)
        await ctx.send(f"Removed {role} from {user.mention}.")

        # Update selected_roles data
        if user_id in selected_roles and role.name in selected_roles[user_id]:
            del selected_roles[user_id]
            print(f"Role {role.name} removed from {user_id} in the JSON file.")
            save_selected_roles(selected_roles)
        else:
            await ctx.send(f"Role {role.name} not found in selected_roles for {user_id}.")
    else:
        await ctx.send(f"{user.mention} does not have the role {role}.")



        
@removeRole.error
async def removeRole_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("You do not have permission to use this command.")


#COIN SYSTEM
try:
    with open('user_balances.json', 'r') as file:
        user_balances = json.load(file)
except FileNotFoundError:
    # If the file doesn't exist yet, create an empty balance dictionary
    user_balances = {}

@client.command()
async def check_balance(ctx):
    user_id = str(ctx.author.id)
    if user_id in user_balances:
        await ctx.send(f"Your balance is {user_balances[user_id]} coins.", ephemeral=True)
    else:
        await ctx.send("You don't have any coins yet.", ephemeral=True)

@client.command()
async def buy_coins(ctx, amount: int):
    user_id = str(ctx.author.id)
    if user_id not in user_balances:
        user_balances[user_id] = 0
    user_balances[user_id] += amount

    # Save the updated balances to the file
    with open('user_balances.json', 'w') as file:
        json.dump(user_balances, file)

client.run(BOT_TOKEN)
