import discord
import json
import asyncio
from discord.ext import commands, tasks
from discord.ext.commands import has_permissions, MissingPermissions
from discord.ext.commands import has_role


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

def has_required_role(role_name):
    async def predicate(ctx):
        # Retrieve the guild and the user
        guild = ctx.guild
        user = ctx.author

        # Get the required role object
        required_role = discord.utils.get(guild.roles, name=role_name)

        # Check if the user has the required role
        return required_role in user.roles

    return commands.check(predicate)

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

        if payload.message_id == role_message_id:
            if str(payload.emoji) == '🎨':  # Artist emoji
                role = discord.utils.get(guild.roles, name="Artist")
                if role:
                    await member.add_roles(role)
                    await member.send(f"You've been assigned the {role.name} role.")
                    selected_roles[user_id] = role.name
                    save_selected_roles(selected_roles)
                else:
                    print("Role not found.")  # Handle role not found scenario
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
                    
                    selected_roles[user_id] = role.name
                    save_selected_roles(selected_roles)
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
        selected_roles[user_id] = role.name  # Store the user's selected role directly
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
def load_user_balances():
    try:
        with open("user_balances.json", "r") as file:
            return json.load(file)
    except FileNotFoundError:
        return {}

# Save selected roles to JSON file
def save_user_balances(selected_roles):
    with open('user_balances.json', 'w') as file:
        json.dump(selected_roles, file)
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

#SUBMISSION HANDLING
@client.command()
async def submit_application(ctx, curator: discord.User):
    # Create temporary channel
    overwrites = {
        ctx.guild.default_role: discord.PermissionOverwrite(read_messages=False),
        ctx.guild.me: discord.PermissionOverwrite(read_messages=True),
        ctx.author: discord.PermissionOverwrite(read_messages=True),
        curator: discord.PermissionOverwrite(read_messages=True)
    }
    channel = await ctx.guild.create_text_channel('application', overwrites=overwrites)
    
    # Start the application process
    await channel.send(f"Application started! Please answer the following questions.")
    
    def check_author(message):
        return message.author == ctx.author and message.channel == channel
    
    # Ask questions one at a time
    questions = [
        "What's your inspiration?",
        "What mediums do you use?",
        "Tell us about your experience."
    ]
    
    answers = []
    for question in questions:
        await channel.send(question)
        answer = await client.wait_for('message', check=check_author)
        answers.append(answer.content)

    # Notify mods and tagged curator
    mod_channel = ctx.guild.get_channel(1169964747156893716)  # Replace with your channel ID
    if mod_channel:
        await mod_channel.send(f"{curator.mention}, {ctx.author.mention} has submitted their application.")
    else:
        print("Moderator channel not found.")

    # Inform the tagged curator
    await channel.send(f"{curator.mention}, your input has been requested. Check the information submitted by {ctx.author.mention}.")

     # Prepare the answers for the moderator channel
    answers_summary = "\n".join(answers)
    mod_channel = ctx.guild.get_channel(1169964747156893716)  # Replace with your actual channel ID
    if mod_channel:
        await mod_channel.send(f"{ctx.author.mention}'s answers:\n{answers_summary}")
    else:
        print("Moderator channel not found.")

     # Deduct 1 coin from the artist's balance
    user_id = str(ctx.author.id)
    if user_id in user_balances:
        user_balances[user_id] -= 1  # Deduct 1 coin
        save_user_balances()
    else:
        print("User balance not found.")

    await asyncio.sleep(60)
    
    # Delete the temporary channel
    await channel.delete()

#CURATOR CONFIRMATION
@client.command()
@has_required_role("Curator")
async def share_song(ctx, artist: discord.User, playlist_link: str):
    # Replace CHANNEL_ID with the specific channel ID where the link will be forwarded
    target_channel = client.get_channel(1170291523234041916)

    # Forward the playlist link to the target channel
    await target_channel.send(f"The song has been shared: {playlist_link}. Tagging {artist.mention} for notification.")

    # Notify the artist about the shared song
    await ctx.send(f"You've successfully shared the song. The artist has been notified.")
    await artist.send(f"Your song has been shared. Check it out here: {playlist_link}")

    # You can perform further actions or logging as needed

client.run(BOT_TOKEN)
