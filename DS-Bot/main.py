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

mods = "AudioPitch Team"
mod_channel = 1168550607867629659
submission_info_channel = 1167865127660433498
general_roles = 1167862425333284895
welcome = 1170634241894252564
audio_coins = 1167865516602429460
songs_to_share = 1167864257690489026

@client.event
async def on_ready():
    global role_message_id
    print("Bot is Online...")
    print("...................")

    # Fetch the channel where you want to send the role selection message
    channel = client.get_channel(general_roles)

    role_message = await channel.send("React to assign yourself a role!\n\n"
                                      "Artist - :artist:\n"
                                      "Curator - :curator:")

    # Add reactions to the message
    await role_message.add_reaction("🎵")  # Artist emoji
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
    channel = client.get_channel(welcome)
    await channel.send(f"Welcome To The Audidopitch Server <@{member.id}>, We hope you'll enjoy it here. \n\n To get a list of commands please refer to the [] text-channel!!")

# Leave Message
@client.event
async def on_member_remove(member):
    channel = client.get_channel(welcome)
    await channel.send(f"<@{member.id}> has left the server, sad to see you go.")

#KICK AND BAN FUNCTIONS
@client.command()
@has_required_role(mods)
async def Kick(member: discord.Member, *, reason=None):
    channel = client.get_channel(welcome)
    await member.kick(reason=reason)
    await channel.send(f"User {member} has been kicked.")

@Kick.error
async def kick_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("You don't have permission to kick people!")

@client.command()
@has_required_role(mods)
async def Ban(member: discord.Member, *, reason=None):
    channel = client.get_channel(welcome)
    await member.ban(reason=reason)
    await channel.send(f"User {member} has been banned.")

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

    if channel.id == general_roles:  # Check if the reaction is in the specific channel
        guild = client.get_guild(payload.guild_id)
        member = guild.get_member(payload.user_id)
        user_id = str(member.id)

        if payload.message_id == role_message_id:
            if str(payload.emoji) == '🎵':  # Artist emoji
                role = discord.utils.get(guild.roles, name="Artist")
                if role:
                    await member.add_roles(role)
                    await member.send(f"You've been assigned the {role.name} role.")
                    selected_roles[user_id] = role.name
                    save_selected_roles(selected_roles)
                else:
                    print("Role not found.")  # Handle role not found scenario
            elif str(payload.emoji) == '🔍':  # Curator emoji
                role = discord.utils.get(guild.roles, name="Curator Pending")
                if role:
                    await member.add_roles(role)
                    if role.name == 'Pending':
                        # For 'Pending' role, send additional steps message
                        await member.send(f"Choosing the Curator role requires additional steps. Please refer to the designated channel.")
                        
                        # Notify moderators in a separate channel
                        mod_channel = guild.get_channel(mod_channel)  # Replace MODERATOR_CHANNEL_ID with the actual channel ID
                        if mod_channel:
                            mods = discord.utils.get(guild.roles, name= mods)  # Assuming there is a role named "Moderators"
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
@has_required_role(mods)
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
@has_required_role(mods)
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
    channel = client.get_channel(audio_coins)
    user_id = str(ctx.author.id)
    user = ctx.author

    if user_id in user_balances:
        await user.send(f"Your balance is {user_balances[user_id]} coins.")
    else:
        await user.send("You don't have any coins yet.")

@client.command()
async def buy_coins(ctx, amount: int):
    channel = client.get_channel(audio_coins)
    user_id = str(ctx.author.id)
    if user_id not in user_balances:
        user_balances[user_id] = 0
    user_balances[user_id] += amount
    await channel.send(f"Successfully added {amount} coins to your account, please check your balance by using the !check_balance command.")

    # Save the updated balances to the file
    with open('user_balances.json', 'w') as file:
        json.dump(user_balances, file)

#SUBMISSION HANDLING
@client.command()
@has_required_role("Artist")

async def submit_tracks(ctx, curator: discord.User):
    # Create the first temporary channel for the artist
    overwrites = {
        ctx.guild.default_role: discord.PermissionOverwrite(read_messages=False),
        ctx.guild.me: discord.PermissionOverwrite(read_messages=True),
        ctx.author: discord.PermissionOverwrite(read_messages=True),
    }
    channel = await ctx.guild.create_text_channel('application', overwrites=overwrites)

    # Start the application process
    await channel.send(f"Application started! Please answer the following questions.")

    def check_author(message):
        return message.author == ctx.author and message.channel == channel

    # Ask questions one at a time
    questions = [
        "Please provide your track link.",
        "What is the genre of this song?",
        "When is it released?"
    ]

    answers = []
    for question in questions:
        await channel.send(question)
        answer = await client.wait_for('message', check=check_author)
        answers.append(answer.content)

    # Notify mods and tagged curator
    modChannel = ctx.guild.get_channel(mod_channel)  # Replace with your channel ID
    submission_channel = ctx.guild.get_channel(submission_info_channel)
    if modChannel:
        await modChannel.send(f"{curator.mention}, {ctx.author.mention} has submitted their application.")
    else:
        print("Moderator channel not found.")
    
    if submission_channel:
        await submission_channel.send(f"{ctx.author.mention}, We have successfully sent your track submission to {curator.mention}!!")
    else:
        print("Submission_info channel not found.")

    # Inform the tagged curator
    await channel.send(f"{curator.mention}, your input has been requested. Check the information submitted by {ctx.author.mention}.")

    # Prepare the answers for the moderator channel
    answers_summary = "\n".join(answers)
    if modChannel:
        await modChannel.send(f"{ctx.author.mention}'s answers:\n{answers_summary}")
    else:
        print("Moderator channel not found.")

    # Deduct 1 coin from the artist's balance
    user_id = str(ctx.author.id)
    if user_id in user_balances:
        user_balances[user_id] -= 1  # Deduct 1 coin
        save_user_balances(user_balances)
    else:
        print("User balance not found.")

    await asyncio.sleep(15)
    # Delete the temporary channel for the artist
    await channel.delete()

     # Second temporary channel for the curator
    curator_overwrites = {
        ctx.guild.default_role: discord.PermissionOverwrite(read_messages=False),
        ctx.guild.me: discord.PermissionOverwrite(read_messages=True),
        curator: discord.PermissionOverwrite(read_messages=True),
    }
    curator_channel = await ctx.guild.create_text_channel('curator-application', overwrites=curator_overwrites)
    
    await curator_channel.send(f"Hello {curator.mention}, please approve or decline this application using the reactions below.")

    # Send the artist's answers to the curator's channel
    message = await curator_channel.send(f"{ctx.author.mention}'s answers:\n{answers_summary}")
    
    # Add reactions for approval or decline
    await message.add_reaction('✅')  # Approve
    await message.add_reaction('❌')  # Decline

    def curator_check(reaction, user):
        return user == curator and reaction.message.channel == curator_channel
    songs2share = ctx.guild.get_channel(songs_to_share)
    try:
        # Wait for a reaction from the curator
        reaction, _ = await client.wait_for('reaction_add', check=curator_check, timeout=60)

        if str(reaction.emoji) == '✅':  # Curator approved
            await curator_channel.send("Application approved! Notifying the artist.")
            # Notify the artist about approval
            await submission_channel.send(f" {ctx.author.mention}, your application has been approved by @{curator}.")
            await songs2share.send(f"{curator.mention}, you have approved to share @{ctx.author}'s track. please confirm by using the !shared command.")

        elif str(reaction.emoji) == '❌':  # Curator declined
            await curator_channel.send("Application declined! Provide feedback to the artist.")
            # Ask the curator to provide feedback
            await submission_channel.send(f"{ctx.author.mention}, your application has been declined by @{curator}. Please check your DMs for feedback.")
            
            def feedback_check(message):
                return message.author == curator and message.channel == curator_channel

            feedback = await client.wait_for('message', check=feedback_check)
            # Forward the feedback to the artist's DM
            await ctx.author.send(f"Feedback from {curator.mention}:\n{feedback.content}")

            # Timer after the curator has provided feedback
            await asyncio.sleep(15)
            # Delete the temporary channel for the curator
            await curator_channel.delete()
            
    except asyncio.TimeoutError:  # Curator didn't react in time
        await curator_channel.send("Time's up. Application unprocessed.")



#CURATOR CONFIRMATION
@client.command()
@has_required_role("Curator")
async def shared(ctx, artist: discord.User, playlist_link: str):
    # Replace CHANNEL_ID with the specific channel ID where the link will be forwarded
    target_channel = client.get_channel(submission_info_channel)

    # Forward the playlist link to the target channel
    await target_channel.send(f"The song has been shared: {playlist_link}. Tagging {artist.mention} for notification.")

    # Notify the artist about the shared song
    await ctx.send(f"You've successfully shared the song. The artist has been notified.")
    await artist.send(f"Your song has been shared. Check it out here: {playlist_link}")

@client.command()
@has_required_role("Curator")
async def cashout(ctx, amount: int):
    user_id = str(ctx.author.id)
    user= ctx.author

    # Check the user's current balance
    await check_balance(ctx)

    if user_id in user_balances:
        balance = user_balances[user_id]

        if amount <= balance:
            # Simulate a payment or currency conversion
            price = amount * 2
            paypal = 1924729712987192571
            await user.send(f"Your AudioPitch coin cashout totals to ${price}, please send your payment to the following paypal account:\nPayPal Account Number: {paypal}.\nPlease send the receipt manually to []'s DM. Thank you!")

            # Simulate deduction of coins
            user_balances[user_id] -= amount
            save_user_balances(user_balances)

        else:
            await ctx.send("Insufficient balance to cash out.")
    else:
        await ctx.send("User balance not found.")

client.run(BOT_TOKEN)
