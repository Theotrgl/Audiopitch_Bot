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
cashout = 1167864319497744394
mods_curator_application = 1173655198711939132

paypal = 1924729712987192571

@client.event
async def on_ready():
    global role_message_id
    print("Bot is Online...")
    print("...................")

    # Fetch the channel where you want to send the role selection message
    channel = client.get_channel(general_roles)

    role_message = await channel.send("React to assign yourself a role!\n\n"
                                      "Artist - 🎵\n"
                                      "Curator - 🔍")

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
    
    # Set an initial balance for the new member
    user_id = str(member.id)
    initial_balance = 0  # You can set any initial balance you want

    # Load existing user balances
    user_balances = load_user_balances()

    # Set the initial balance
    user_balances[user_id] = initial_balance

    # Save the updated balances to the file
    save_user_balances(user_balances)

    await channel.send(f"Welcome To The Audidopitch Server <@{member.id}>, We hope you'll enjoy it here. \n\n To get a list of commands please refer to the [] text-channel!!")

    # Optionally, you can send a message about the initial balance
    await member.send(f"Welcome to the AudioPitch server! You've received an initial balance of {initial_balance} coins.")


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
    guild = client.get_guild(payload.guild_id)

    if channel.id == general_roles:  # Check if the reaction is in the specific channel
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
                modCurator = guild.get_channel(mods_curator_application)
                role = discord.utils.get(guild.roles, name="Curator Pending")
                if role:
                    await member.add_roles(role)
                    if role.name == 'Curator Pending':
                        # For 'Pending' role, send additional steps message
                        await member.send(f"Choosing the Curator role requires additional steps. Please go to the curator-application text-channel and fill out the questions.")

                        # Update channel permissions for the reacting member
                        application_overwrites = {
                            guild.default_role: discord.PermissionOverwrite(read_messages=False),
                            guild.me: discord.PermissionOverwrite(read_messages=True),
                            member: discord.PermissionOverwrite(read_messages=True),
                        }
                        application_channel = await guild.create_text_channel(f'{member.name}-Curator-Application-TC', overwrites=application_overwrites)
                        await application_channel.send(f"{member.mention}, Private channel created! Please answer the following questions!")

                        questions = [
                        "What is your curator name?",
                        "In which media do you curate? (Spotify, Youtube, Blog, etc)",
                        "Please send us the links to your media",
                        "What song genres do you prefer in submissions?"
                        ]

                        header_list = [
                            "Curator Name:",
                            "Media for Curation:",
                            "Links to Media:",
                            "Preferred Song Genres:"
                        ]

                        answers_with_headers = []

                        for i, question in enumerate(questions):
                            await application_channel.send(question)

                            def check_author(message):
                                return message.author == member

                            # Wait for a message
                            answer = await client.wait_for('message', check=check_author)

                            # Append the answer along with its header to the list
                            answers_with_headers.append((header_list[i], answer.content))

                        thanks = await application_channel.send(f"Thank you, your request is being reviewed, please wait for notifications from the AudioPitch Bot or the AudioPitch mods.")
                        await asyncio.sleep(10)
                        await thanks.delete()
                        await asyncio.sleep(10)
                        await application_channel.delete()
                        mods_role = discord.utils.get(guild.roles, name=mods)
                        await modCurator.send(f"{mods_role.mention} A Pending Curator {member.name} has sent a request to become a Curator, please review their information.")
                        # Sending the stored answers as formatted text
                        for header, answer_content in answers_with_headers:
                            await modCurator.send(f'{header}\r{answer_content}')
                    else:
                        other = await member.send(f"You've been assigned the {role.name} role.")
                        await asyncio.sleep(5)
                        await other.delete()
                        await asyncio.sleep(10)
                        await application_channel.delete()
                    
                    selected_roles[user_id] = role.name
                    save_selected_roles(selected_roles)
                else:
                    print("Role not found.")  # Handle role not found scenario



#ROLE ADDING AND REMOVING FOR MODS
@client.command()
@has_required_role(mods)
async def addRole(ctx, user: discord.Member, *, role: discord.Role):
    await asyncio.sleep(3)
    await ctx.message.delete()
    if role in user.roles:
        err = await ctx.send(f"{user.mention} already has the role {role}.")
        await asyncio.sleep(5)
        await err.delete()
    else:
        await user.add_roles(role)
        msg = await ctx.send(f"Added {role} to {user.mention}.")
        await asyncio.sleep(5)
        await msg.delete()

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
    await asyncio.sleep(3)
    await ctx.message.delete()
    user_id = str(user.id)
    if role in user.roles:
        await user.remove_roles(role)
        success = await ctx.send(f"Removed {role} from {user.mention}.")
        await asyncio.sleep(10)
        await success.delete()
        
        # Update selected_roles data
        if user_id in selected_roles and role.name in selected_roles[user_id]:
            del selected_roles[user_id]
            print(f"Role {role.name} removed from {user_id} in the JSON file.")
            save_selected_roles(selected_roles)
        else:
            error = await ctx.send(f"Role {role.name} not found in selected_roles for {user_id}.")
            await asyncio.sleep(10)
            await error.delete()
    else:
        error_2 = await ctx.send(f"{user.mention} does not have the role {role}.")
        await asyncio.sleep(10)
        await error_2.delete()

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
    await asyncio.sleep(3)
    await ctx.message.delete()
    channel = client.get_channel(audio_coins)
    user_id = str(ctx.author.id)
    user = ctx.author
    if user_id in user_balances:
        await user.send(f"Your balance is {user_balances[user_id]} coins.")
    else:
        await user.send("You don't have any coins yet.")

@client.command()
async def buy_coins(ctx, amount: int):
    await asyncio.sleep(3)
    await ctx.message.delete()
    modChannel = client.get_channel(mod_channel)
    channel = client.get_channel(audio_coins)
    user_id = str(ctx.author.id)
    overwrites = {
        ctx.guild.default_role: discord.PermissionOverwrite(read_messages=False),
        ctx.guild.me: discord.PermissionOverwrite(read_messages=True),
        ctx.author: discord.PermissionOverwrite(read_messages=True),
    }
    temp_channel = await ctx.guild.create_text_channel(f'{ctx.author.name}-Coin-Purchase-TC', overwrites=overwrites)
    await temp_channel.send(f"Please transfer your money to the following PayPal Account {paypal}")
    
    def payment_check(message):
                return message.author == ctx.author and message.channel == temp_channel

    response = await client.wait_for('message', check=payment_check, timeout=604800)
    if user_id not in user_balances:
        user_balances[user_id] = 0
    user_balances[user_id] += amount
    await ctx.author.send(f"Successfully added {amount} coins to your account, please check your balance by using the !check_balance command.")
    await modChannel.send(f"{ctx.author.mention} has purchased {amount} Coins, please check for purchase confirmation!!")
    # Save the updated balances to the file
    with open('user_balances.json', 'w') as file:
        json.dump(user_balances, file)

    await asyncio.sleep(10)
    await temp_channel.delete()

#SUBMISSION HANDLING
@client.command()
@has_required_role("Artist")

async def submit_track(ctx, curator: discord.User):
    await asyncio.sleep(3)
    await ctx.message.delete()

    guild = ctx.guild
    curator_user = guild.get_member(curator.id)
    modChannel = ctx.guild.get_channel(mod_channel)  # Replace with your channel ID
    
    required_role = "Curator"

    if required_role not in [role.name for role in curator_user.roles]:
        error = await ctx.send(f"{curator.mention} does not have the required role ({required_role}).")
        await asyncio.sleep(2)
        await error.delete()
        return
    else:
        # Create the first temporary channel for the artist
        overwrites = {
            ctx.guild.default_role: discord.PermissionOverwrite(read_messages=False),
            ctx.guild.me: discord.PermissionOverwrite(read_messages=True),
            ctx.author: discord.PermissionOverwrite(read_messages=True),
        }
        channel = await ctx.guild.create_text_channel(f'{ctx.author.name}-Track-Info-TC', overwrites=overwrites)

        # Start the application process
        await channel.send(f"{ctx.author.mention}, Private channel created! Please answer the following questions!\n\nIMPORTANT NOTE: If you want to cancel the submission please type in CANCEL in this text channel. Your Coins Hasn't been deducted yet at this point.")

        questions = [
        "Please provide your track link.",
        "What is the genre of this song?",
        "When is it released?"
        ]

        header_list = [
            "Track Link:",
            "Genre of Song",
            "Release Date",
        ]

        answers = []
        cancel_triggered = False
        answers_with_headers = []

        for i, question in enumerate(questions):
            await channel.send(question)

            def check_author(message):
                return message.author == ctx.author

            # Wait for a message
            answer = await client.wait_for('message', check=check_author)

            if "CANCEL" in answer.content.upper():
                await channel.send("Submission request has been cancelled, your coins have not been deducted yet.")
                await modChannel.send(f"{ctx.author.name} has cancelled their track submission request for {curator.name}.")
                cancel_triggered = True
                break

            # Append the answer along with its header to the list
            answers_with_headers.append((header_list[i], answer.content))
        
        if cancel_triggered:
            await asyncio.sleep(1)
            await channel.delete()
        else:
            if modChannel:
                await modChannel.send(f"{ctx.author.mention} has filed a submitted a track to {curator.mention}, awaiting confirmation from {ctx.author.mention}.")
            else:
                print("Moderator channel not found.")
            
            submission_overwrites = {
                ctx.guild.default_role: discord.PermissionOverwrite(read_messages=False),
                ctx.guild.me: discord.PermissionOverwrite(read_messages=True),
                ctx.author: discord.PermissionOverwrite(read_messages=True),
            }
            submission_channel = await ctx.guild.create_text_channel(f'{ctx.author.name}-Curator-Submission', overwrites=submission_overwrites)

            if submission_channel:
                await submission_channel.send(f"{ctx.author.mention}, We have successfully sent your track submission to {curator.mention}!!")
            else:
                print("Submission_info channel not found.")

            # Inform the tagged curator
            await channel.send(f"{curator.mention}, your input has been requested. Check the information submitted by {ctx.author.mention}.")

            # Deduct 1 coin from the artist's balance
            user_id = str(ctx.author.id)
            if user_id in user_balances:
                user_balances[user_id] -= 1  # Deduct 1 coin
                save_user_balances(user_balances)
            else:
                print("User balance not found.")

            await asyncio.sleep(10)
            # Delete the temporary channel for the artist
            await channel.delete()

            # Second temporary channel for the curator
            curator_overwrites = {
                ctx.guild.default_role: discord.PermissionOverwrite(read_messages=False),
                ctx.guild.me: discord.PermissionOverwrite(read_messages=True),
                curator: discord.PermissionOverwrite(read_messages=True),
            }
            curator_channel = await ctx.guild.create_text_channel(f'submission {curator.name}', overwrites=curator_overwrites)
            
            await curator_channel.send(f"Hello {curator.mention}, {ctx.author.mention} has filed a track submission for you, please approve or decline this application using the reactions below.\nHere are {ctx.author.mention}'s track data:")
            # Send the artist's answers to the curator's channel           
            for header, answer_content in answers_with_headers:
                message = await curator_channel.send(f'{header}\r{answer_content}')
            
            # Add reactions for approval or decline
            await message.add_reaction('✅')  # Approve
            await message.add_reaction('❌')  # Decline

            def curator_check(reaction, user):
                return user == curator and reaction.message.channel == curator_channel
            songstoshare = {
                ctx.guild.default_role: discord.PermissionOverwrite(read_messages=False),
                ctx.guild.me: discord.PermissionOverwrite(read_messages=True),
                curator: discord.PermissionOverwrite(read_messages=True),
            }
            try:
                # Wait for a reaction from the curator
                reaction, _ = await client.wait_for('reaction_add', check=curator_check, timeout=604800)

                if str(reaction.emoji) == '✅':  # Curator approved
                    await curator_channel.send("Application approved! Notifying the artist.")
                    # Notify the artist about approval
                    await submission_channel.send(f" {ctx.author.mention}, your application has been approved by @{curator}.")
                    
                    songs2share = await ctx.guild.create_text_channel(f'submission {curator.name}', overwrites=songstoshare)
                    await songs2share.send(f"{curator.mention}, you have approved to share @{ctx.author}'s track. Please confirm by sending the link to your playlist here.")

                    # Wait for the curator's response to share the link
                    def link_check(message):
                        return message.author == curator and message.channel == songs2share

                    curator_link = await client.wait_for('message', check=link_check, timeout=604800)

                    curator_id = str(curator.id)
                    if curator_id in user_balances:
                        user_balances[curator_id] += 1  # Add 1 coin to Curator's balance
                        save_user_balances(user_balances)
                        await curator.send(f"Successfully Added 1 coin to your account from a successful transaction with {ctx.author.name}")
                        await ctx.author.send(f"Curator {curator.mention} has added your track to their playlist, go ahead and check here: {curator_link.content}")
                    else:
                        print("User's balance not found.")
                    if modChannel:
                        await modChannel.send(f"{ctx.author.mention}'s Request has been accepted by {curator.mention}, Here are the track's metadata:\n")
                        for header, answer_content in answers_with_headers:
                            message = await modChannel.send(f'{header}\r{answer_content}')
                    else:
                        print("Moderator channel not found.")
                    # Timer after the curator has provided feedback
                    await asyncio.sleep(10)
                    # Delete the temporary channel for the curator
                    await curator_channel.delete()
                    await songs2share.delete()
                    await submission_channel.delete()

                elif str(reaction.emoji) == '❌':  # Curator declined
                    await curator_channel.send("Application declined! Provide feedback to the artist.")
                    def feedback_check(message):
                        return message.author == curator and message.channel == curator_channel

                    feedback = await client.wait_for('message', check=feedback_check)
                    await curator_channel.send("Thank You for your feedback. Deleting channel in a sec.")
                    await asyncio.sleep(10)
                    await curator_channel.delete()
                    # Forward the feedback to the artist's DM
                    await submission_channel.send(f"{ctx.author.mention}, your application has been declined by @{curator}. Please wait for {curator.name}'s feedback.\nFeedback from {curator.mention}:\n{feedback.content}\n\nPlease reply CONFIRM to finish request.")

                    def confirm_check(message):
                        return message.author == ctx.author and message.channel == submission_channel
                    confirm_message = await client.wait_for('message', check=confirm_check)
                    if "CONFIRM" in confirm_message.content.upper():
                        await submission_channel.send(f"Confirmed, deleting channel in a sec.")
                        # Timer after the curator has provided feedback
                        await asyncio.sleep(10)
                        await submission_channel.delete()
                    
            except asyncio.TimeoutError:  # Curator didn't react in time
                await curator_channel.send("Time's up. Application unprocessed.")
                if user_id in user_balances:
                    user_balances[user_id] += 1  # Add 1 coin back if the curator fails to respond
                    save_user_balances(user_balances)
                    await ctx.author.send(f"{curator.name} failed to answer your request in time. Here's your coin back.")
                else:
                    print("User balance not found.")

@client.command()
@has_required_role("Curator")
async def cashout(ctx, amount: int):
    await asyncio.sleep(3)
    await ctx.message.delete()
    user_id = str(ctx.author.id)
    user= ctx.author
    cashout_channel = client.get_channel(cashout)
    modChannel = client.get_channel(mod_channel)

    # Check the user's current balance
    await check_balance(ctx)
    curator_overwrites = {
        ctx.guild.default_role: discord.PermissionOverwrite(read_messages=False),
        ctx.guild.me: discord.PermissionOverwrite(read_messages=True),
        user: discord.PermissionOverwrite(read_messages=True),
    }
    curator_channel = await ctx.guild.create_text_channel(f'{user.name} Cashout-TC', overwrites=curator_overwrites)
    if user_id in user_balances:
        balance = user_balances[user_id]

        if amount <= balance:
            # Simulate a payment or currency conversion
            price = amount * 2
            await curator_channel.send(f"You're cashing out {amount} or ${price} worth of AudioCoins, please send a DM to [] in order to process your cashout request")
            await modChannel.send(f"{ctx.author.name} has used the !cashout command, please be alert for DM's pertaining to the cashout request.")
            
            await asyncio.sleep(5)
            await cashout_channel.delete()

        else:
            await curator_channel.send("Insufficient balance to cash out.")
            await asyncio.sleep(5)
            await cashout_channel.delete()
    else:
        balance_error = await cashout_channel.send("User balance not found.")
        await asyncio.sleep(5)
        await cashout_channel.delete()
        await balance_error.delete()

client.run(BOT_TOKEN)
