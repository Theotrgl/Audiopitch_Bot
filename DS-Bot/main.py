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
submit_your_song = 1167864900337549363
general_roles = 1167862425333284895
welcome = 1170634241894252564
audio_coins = 1167865516602429460
songs_to_share = 1167864257690489026
Cashout = 1174171461473284096
mods_curator_application = 1173655198711939132
mods_buy_coins = 1174165449206927380
bot_commands = 1168549555038584902
curator_cashout = 1167864319497744394
submissionTrack = 1174600646125690910

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
async def hello(ctx):
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

    await channel.send(f"Welcome To The Audidopitch Server <@{member.id}>.\n\nPlease take a look at our rules in the rules text-channel, and don't forget to pick a role in the general-roles TC.\n\nAdditionally, please refer to the tutorial TC after you have chosen your role.\n\nFinally, to get a list of commands please refer to the list-of-commands text-channel!!\n\nWe hope you'll enjoy it here.")

    # Optionally, you can send a message about the initial balance
    await member.send(f"Welcome to the AudioPitch server! You've received an initial balance of {initial_balance} coins.")


# Leave Message
@client.event
async def on_member_remove(member):
    user_id = str(member.id)
    user_balances = load_user_balances()
    selected_roles = load_selected_roles()

    channel = client.get_channel(welcome)
    await channel.send(f"<@{member.id}> has left the server, sad to see you go.")

    if user_id in user_balances:
        del user_balances[user_id]
        save_user_balances(user_balances)
        print("Balance successfully deleted")
    else:
        print("Balance does not exist")

    if user_id in selected_roles:
        # Retrieve the role_name associated with the user_id
        role_names = selected_roles[user_id].keys()
        for role_name in role_names:
            del selected_roles[user_id][role_name]
            save_selected_roles(selected_roles)
            print("Successfully deleted role of user")
    else:
        print('User Does not have a role.')
    

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

def restrict_channel(*channel_ids):
    def predicate(ctx):
        if ctx.channel.id in channel_ids:
            return True
        else:
            async def prompt():
                warning_msg = await ctx.send("Invalid Text-Channel, Please use the command in the designated text-channel!!!")
                await asyncio.sleep(5)  # Wait for 5 seconds
                await warning_msg.delete()
                await ctx.message.delete()

            # Use asyncio to handle the warning message and deletion
            asyncio.create_task(prompt())
            return False  # Returning False directly indicates the check failed

    return commands.check(predicate)

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
                        await asyncio.sleep(2)
                        await application_channel.delete()
                        mods_role = discord.utils.get(guild.roles, name=mods) 
                        message_content = f"{mods_role.mention} A Pending Curator {member.name} has sent a request to become a Curator, please click the reaction to approve or decline the request.\n"
                        # Sending the stored answers as formatted text
                        for header, answer_content in answers_with_headers:
                            message_content += f'\n\n{header}\r{answer_content}'
                        
                        def mods_check(reaction, user):
                            return user in mods_role.members and reaction.message.id == message.id
                        
                        message = await modCurator.send(message_content)
                        # Add reactions for approval or decline
                        await message.add_reaction('✅')  # Approve
                        await message.add_reaction('❌')  # Decline
                        
                        try:
                            # Wait for a reaction from the curator
                            reaction, user = await client.wait_for('reaction_add', check=mods_check, timeout=999999999999)

                            if str(reaction.emoji) == '✅':  # Curator approved
                                role = discord.utils.get(guild.roles, name="Curator")
                                delete = discord.utils.get(guild.roles, name="Curator Pending")
                                if role and delete:
                                    await member.remove_roles(delete)
                                    await member.add_roles(role)
                                    await member.send(f"{member.mention} your application has been approved, you've been assigned the {role.name} role.")
                                    selected_roles[user_id] = role.name
                                    save_selected_roles(selected_roles)
                                else:
                                    print("Role not found.")  # Handle role not found scenario
                                message_2 = await modCurator.send(f"Application approved! {member.mention} has been given role of Curator!!")
                                await asyncio.sleep(10)
                                await message.delete()
                                await message_2.delete()

                            elif str(reaction.emoji) == '❌':  # Curator declined
                                delete = discord.utils.get(guild.roles, name="Curator Pending")
                                if delete:
                                    await member.remove_roles(delete)
                                    prompt = await member.send(f"{member.mention} Application declined by moderators!Please try again later.")
                                    await asyncio.sleep(10)
                                    await prompt.delete()
                                    selected_roles[user_id] = role.name
                                    save_selected_roles(selected_roles)
                                else:
                                    print("Role not found.")  # Handle role not found scenario
                        except asyncio.TimeoutError:  # Curator didn't react in time
                            await modCurator.send("Time's up. Application unprocessed.")
                            await member.send(f"the mods failed to answer your request in time, please make another request.")
                        
                    else:
                        other = await member.send(f"{member.mention} You've been assigned the {role.name} role.")
                        await asyncio.sleep(5)
                        await other.delete()
                        await asyncio.sleep(10)
                        await application_channel.delete()
                    
                    selected_roles[user_id] = role.name
                    save_selected_roles(selected_roles)
                else:
                    print("Role not found.")  # Handle role not found scenario


#MOD COMMANDS
#ROLE ADDING AND REMOVING FOR MODS
@client.command()
@has_required_role(mods)
@restrict_channel(bot_commands)
async def addRole(ctx, user: discord.Member, *, role: discord.Role):
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
@restrict_channel(bot_commands)
async def removeRole(ctx, user: discord.Member, *, role: discord.Role):
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

@client.command()
@has_required_role(mods)
@restrict_channel(mods_buy_coins)
async def addCoins(ctx, member: discord.Member, amount: int):
    user_balances = load_user_balances()

    # Check if the tagged member already has an entry in the balance data
    user_id = str(member.id)
    if user_id in user_balances:
        # Add coins to the existing balance
        user_balances[user_id] += amount
        await member.send(f"You have successfully purchased 6 AudioCoins. Please check your balance by typing the command !check_balance in the #audio-coins text channel")
    else:
        # Create a new entry for the tagged member
        user_balances[user_id] = amount

    # Save the updated balances to the JSON file
    save_user_balances(user_balances)

    msg = await ctx.send(f"Added {amount} coins to {member.display_name}'s account.")

@client.command()
@has_required_role(mods)
@restrict_channel(bot_commands)
async def checkBalance(ctx, member: discord.Member):
    user_balances = load_user_balances()

    user_id = str(member.id)
    if user_id in user_balances:
        await ctx.send(f"{member.mention} has {user_balances[user_id]} coins.")
    else:
        await ctx.send(f"No record of {member.mention} in the database.")

@client.command()
@has_required_role(mods)
@restrict_channel(bot_commands)
async def addBalance(ctx, member:discord.Member):
    user_id = str(member.id)
    initial_balance = 0  # You can set any initial balance you want
    user_balances = load_user_balances()

    if user_id not in user_balances:
        user_balances[user_id] = initial_balance
        await ctx.send(f"Successfully initialized {member.mention}'s balance!!")
        save_user_balances(user_balances)
    else:
        await ctx.send(f"{member.mention} already has a balance!!")

    

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
@restrict_channel(audio_coins, curator_cashout)
async def check_balance(ctx):
    await asyncio.sleep(3)
    await ctx.message.delete()
    user_balances = load_user_balances()
    channel = client.get_channel(audio_coins)
    user_id = str(ctx.author.id)
    user = ctx.author
    if user_id in user_balances:
        await user.send(f"Your balance is {user_balances[user_id]} coins.")
    else:
        await user.send("You don't have any coins yet.")

@client.command()
@restrict_channel(audio_coins)
async def buy_coins(ctx):
    await asyncio.sleep(3)
    await ctx.message.delete()
    buyCoins = ctx.guild.get_channel(mods_buy_coins)
    # Create a temporary text channel for the purchase
    overwrites = {
            ctx.guild.default_role: discord.PermissionOverwrite(read_messages=False),
            ctx.guild.me: discord.PermissionOverwrite(read_messages=True),
            ctx.author: discord.PermissionOverwrite(read_messages=True),
        }
    coin_purchase_channel = await ctx.guild.create_text_channel(f'{ctx.author.name}-Buy-AudioCoins', overwrites=overwrites)

    # Send the purchase options
    purchase_options = {
        "1": {"coins": 6, "price": 6},
        "2": {"coins": 9, "price": 8},
        "3": {"coins": 12, "price": 10},
    }

    purchase_prompt = "Please choose an option by typing numbers 1, 2 or 3:\n"
    for option, details in purchase_options.items():
        purchase_prompt += f"Option {option}: {details['coins']} coins for ${details['price']}\n"

    await coin_purchase_channel.send(purchase_prompt)

    def check(message):
        return message.author == ctx.author and message.channel == coin_purchase_channel

    def check_receipt(message):
        return message.author == ctx.author and message.channel == coin_purchase_channel and message.attachments

    try:
        paypal = "https://paypal.me/jaysiegers"
        msg = await client.wait_for('message', check=check, timeout=3600 * 24)
        selected_option = msg.content

        if selected_option in purchase_options:
            selected_purchase = purchase_options[selected_option]
            await coin_purchase_channel.send(f"You've chosen Option {selected_option}. Please transfer ${selected_purchase['price']} to this PayPal account:\n\n {paypal}\n\n")
            await coin_purchase_channel.send(f"Please provide receipt screenshot once the payment is complete.\n\n*Note that our working ours are 03:00 - 15:00 GMT. We will notify you once your payment is verified by our team.")

            receipt_msg = await client.wait_for('message', check=check_receipt, timeout=3600 * 24)

            if receipt_msg.attachments:
                attachment_url = receipt_msg.attachments[0].url  # Get the URL of the first attachment
                # You can now use this URL to download or handle the attachment as needed
                await coin_purchase_channel.send(f"Thank you {ctx.author.mention} for purchasing AudioCoins. You will receive your AudioCoins once the payment is verified by our team, and you will be notified soon.\n\nBest,\nJay Siegers\nAudioPitch Team")
                await buyCoins.send(f"{ctx.author.mention} has filed a coin purchase request option {selected_option}, please verify whether the receipt is valid or not.\n\nReceipt:\n{attachment_url}")
                await asyncio.sleep(10)
                await coin_purchase_channel.delete()
            else:
                await coin_purchase_channel.send("Please provide a clear screenshot of a valid transaction receipt!!")
                await asyncio.sleep(10)
                await coin_purchase_channel.delete()
        else:
            await coin_purchase_channel.send("Invalid option selected. Purchase canceled.")
            await asyncio.sleep(10)
            await coin_purchase_channel.delete()
    except asyncio.TimeoutError:
        await coin_purchase_channel.send("Purchase timed out.")
        await coin_purchase_channel.delete()


#SUBMISSION HANDLING
@client.command()
@has_required_role("Artist")
@restrict_channel(submit_your_song)
async def submit_track(ctx, curator: discord.User):
    await asyncio.sleep(3)
    await ctx.message.delete()

    guild = ctx.guild
    curator_user = guild.get_member(curator.id)
    modChannel = ctx.guild.get_channel(mod_channel)  # Replace with your channel ID
    submission_tracking = ctx.guild.get_channel(submissionTrack)
    
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
        await channel.send(f"{ctx.author.mention}, Private channel created! Please answer the following questions!\n\nIMPORTANT NOTE: If you want to cancel the submission please type in CANCEL in this text channel. Your Coins Hasn't been deducted yet at this point.\n(2 AudioCoins will be deducted from your balance if you submit your track).")

        questions = [
        "Please provide your track link.",
        "What is the genre of this song?",
        "Please provide your song and/or artist description."
        ]

        header_list = [
            "Track Link:",
            "Genre of Song",
            "Song or Artist Description",
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
            
            user_id = str(ctx.author.id)
            if user_id in user_balances:
                if user_balances[user_id]>=2:
                    # Deduct 2 coin from the artist's balance
                    user_balances[user_id] -= 2  # Deduct 2 coin
                    save_user_balances(user_balances)
                    await channel.send(f"Thank You {ctx.author.mention} for submitting the necessary information, please check the Curator-Submission-Info Text Channel for further updates.")
                    await asyncio.sleep(3)
                    await channel.delete()

                    submission_overwrites = {
                        ctx.guild.default_role: discord.PermissionOverwrite(read_messages=False),
                        ctx.guild.me: discord.PermissionOverwrite(read_messages=True),
                        ctx.author: discord.PermissionOverwrite(read_messages=True),
                    }

                    submission_channel = await ctx.guild.create_text_channel(f'{curator.name}-Curator-Submission-Info', overwrites=submission_overwrites)
                    

                    if submission_channel:
                        await submission_channel.send(f"{ctx.author.mention}, We have successfully sent your track submission to {curator.mention}!!")
                    else:
                        print("Submission_info channel not found.")
                    # Second temporary channel for the curator
                    curator_overwrites = {
                        ctx.guild.default_role: discord.PermissionOverwrite(read_messages=False),
                        ctx.guild.me: discord.PermissionOverwrite(read_messages=True),
                        curator: discord.PermissionOverwrite(read_messages=True),
                    }
                    curator_channel = await ctx.guild.create_text_channel(f'{ctx.author.name}-Submission-Request', overwrites=curator_overwrites)
                    
                    message = await curator_channel.send(f"Hello {curator.mention}, {ctx.author.mention} has filed a track submission for you, please approve or decline this application using the reactions below.\nHere are {ctx.author.mention}'s track data:")
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
                            
                            songs2share = await ctx.guild.create_text_channel(f'Approve-Track-For-{ctx.author.name}', overwrites=songstoshare)
                            await songs2share.send(f"{curator.mention}, you have approved to share @{ctx.author}'s track. Please confirm by sending the link to your playlist here.")

                            # Wait for the curator's response to share the link
                            def link_check(message):
                                return message.author == curator and message.channel == songs2share

                            curator_link = await client.wait_for('message', check=link_check, timeout=604800)
                            await songs2share.send("Thank You for providing the link to your playlist, the link is currently being reveiwed by the mods, please wait for further notifications!")
                            track_link = answers_with_headers[0]
                            header_of_track_link, content_of_track_link = track_link
                            # await ctx.author.send(f"Curator {curator.mention} has added your track to their playlist, go ahead and check here: {curator_link.content}")
                            confirmation_message = await submission_tracking.send(f"{curator.mention} has approved and confirmed that they have added {ctx.author.mention}'s track to their playlist, please review the validity of that statement.\n\nTrack Link: {content_of_track_link}\nPlaylist Link: {curator_link.content}")
                            mods_role = discord.utils.get(guild.roles, name=mods)
                            def moderators_check(reaction, user):
                                return user in mods_role.members and reaction.message.id == confirmation_message.id
                            
                            # Add reactions for approval or decline
                            await confirmation_message.add_reaction('✅')  # Approve
                            await confirmation_message.add_reaction('❌')  # Decline
                            
                            try:
                                # Wait for a reaction from the curator
                                reaction, user = await client.wait_for('reaction_add', check=moderators_check, timeout=604800)
                                if str(reaction.emoji) == '✅':  # mods approved
                                    curator_id = str(curator.id)
                                    if curator_id in user_balances:
                                        user_balances[curator_id] += 1  # Add 1 coin to Curator's balance
                                        save_user_balances(user_balances)
                                        await curator.send(f"Successfully Added 1 coin to your account from a successful transaction with {ctx.author.name}")
                                        await submission_channel.send(f"Curator {curator.mention} has added your track to their playlist, go ahead and check here: {curator_link.content}")
                                        await submission_channel.send(f"Please reply CONFIRM to finish request.")

                                        def confirm_check(message):
                                            return message.author == ctx.author and message.channel == submission_channel
                                        
                                        confirm_message = await client.wait_for('message', check=confirm_check)
                                        if "CONFIRM" in confirm_message.content.upper():
                                            await submission_channel.send(f"Confirmed, deleting channel in a sec.")
                                            # Timer after the curator has provided feedback
                                            await asyncio.sleep(10)
                                            await submission_channel.delete()
                                    else:
                                        print("User's balance not found.")
                                elif str(reaction.emoji) == '❌':  # Mods declined
                                    if user_id in user_balances:
                                        user_balances[user_id] += 2  # Add 2 coin to Artist's balance
                                        save_user_balances(user_balances)
                                        await curator.send(f"{curator.mention}, the moderators has taken a look at your playlist, and it seems that we could not find the track {content_of_track_link} in your playlist.")
                                        await submission_channel.send(f"Curator {curator.mention} has failed to add your track to their playlist {curator_link.content}, your coins have been refunded back to your account. Check using the !check_balance command.")
                                        await submission_channel.send(f"Please reply CONFIRM to finish request.")

                                        def confirm_check(message):
                                            return message.author == ctx.author and message.channel == submission_channel
                                        confirm_message = await client.wait_for('message', check=confirm_check)
                                        if "CONFIRM" in confirm_message.content.upper():
                                            await submission_channel.send(f"Confirmed, deleting channel in a sec.")
                                            await asyncio.sleep(10)
                                            await submission_channel.delete()
                                    else:
                                        print("User's balance not found.")
                            except asyncio.TimeoutError:  # Mods didn't react in time
                                await submission_tracking.send("Time's up. Application unprocessed.")
                                await curator.send(f"the mods failed to review your request in time, please make another request.")
                                await ctx.author.send(f"The mods failed to review the curator's request in time, your coins have been refunded back to your account. Check using the !check_balance command.")
                                if user_id in user_balances:
                                        user_balances[user_id] += 2  # Add 2 coins back to Artist's balance
                                        save_user_balances(user_balances)
                                else:
                                    print("User's balance not found.")
                                await asyncio.sleep(1)
                                await curator_channel.delete()
                                await songs2share.delete()
                                await submission_channel.delete()
                            # Timer after the curator has provided feedback
                            await asyncio.sleep(10)
                            # Delete the temporary channel for the curator
                            await curator_channel.delete()
                            await songs2share.delete()
                            # await submission_channel.delete()

                        elif str(reaction.emoji) == '❌':  # Curator declined
                            await curator_channel.send("Application declined! Provide feedback to the artist.")
                            await submission_tracking.send(f"{curator.mention} has declined {ctx.author.mention}'s track submission request.")
                            curator_id = str(curator.id)
                            def feedback_check(message):
                                return message.author == curator and message.channel == curator_channel

                            feedback = await client.wait_for('message', check=feedback_check)
                            if curator_id in user_balances:
                                user_balances[curator_id] += 1  # Add 1 coin to Curator's balance
                                save_user_balances(user_balances)
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
                            user_balances[user_id] += 2  # Add 2 coin back if the curator fails to respond
                            save_user_balances(user_balances)
                            await ctx.author.send(f"{curator.name} failed to answer your request in time. Here's your coin back.")
                        else:
                            print("User balance not found.")
                else:
                    await channel.send("Insufficient balance to conduct transaction, please top-up first!!")
                    await modChannel.send(f"{ctx.author.mention}'s track submission was cancelled due to insufficient balance.")
                    await asyncio.sleep(3)
                    await channel.delete()
            else:
                print("User balance not found.")
                await channel.delete()

@client.command()
@has_required_role("Curator")
@restrict_channel(curator_cashout)
async def cashout(ctx):
    await asyncio.sleep(3)
    await ctx.message.delete()
    user_id = str(ctx.author.id)
    user= ctx.author
    cashout_channel = client.get_channel(Cashout)
    overwrites = {
        ctx.guild.default_role: discord.PermissionOverwrite(read_messages=False),
        ctx.guild.me: discord.PermissionOverwrite(read_messages=True),
        user: discord.PermissionOverwrite(read_messages=True),
    }
    temp = await ctx.guild.create_text_channel(f'{user.name} Cashout-TC', overwrites=overwrites)

    await temp.send(f"{ctx.author.mention}How many audiocoins would you like to cashout?")

    def amount_check(message):
        return message.author == ctx.author and message.channel == temp
    
    amount = await client.wait_for('message', check=amount_check)
    if user_id in user_balances:
        balance = user_balances[user_id]
        
        if int(amount.content) <= balance:
            price = int(amount.content) * 1
            await temp.send(f"Please send your paypal email information in this text-channel.")
            def info_check(message):
                return message.author == ctx.author and message.channel == temp
            info = await client.wait_for('message', check=info_check)
            await temp.send(f"Thank You {ctx.author.mention} for trusting us, please wait for the AudioPitch team's response. You will be notified immediately")
            await cashout_channel.send(f"{ctx.author.name} has cashed out {amount.content} AudioCoins, please transfer ${price} to this PayPal account: \n\n{info.content}")
            await asyncio.sleep(5)
            await temp.delete()
        else:
            await temp.send("Insufficient AudioCoins balance to cash out.")
            await asyncio.sleep(3)
            await temp.delete()
    else:
        balance_error = await temp.send("User balance not found.")
        await asyncio.sleep(5)
        await temp.delete()
        await balance_error.delete()
    


client.run(BOT_TOKEN)
