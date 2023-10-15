import discord
from discord.ext import commands
import json
import asyncio

TOKEN = 'TOKEN'
PREFIX = '!'

intents = discord.Intents.default()
intents.dm_messages = True

bot = commands.Bot(command_prefix=PREFIX, intents=intents)

def load_data():
    try:
        with open('tournament_data.json', 'r') as file:
            return json.load(file)
    except FileNotFoundError:
        return {'participants': [], 'gifs': [], 'current_round': 1}

def save_data():
    with open('tournament_data.json', 'w') as file:
        json.dump(tournament_data, file, indent=2)

def load_tournament_state():
    try:
        with open('tournament_state.json', 'r') as file:
            return json.load(file)
    except FileNotFoundError:
        return None

def save_tournament_state():
    with open('tournament_state.json', 'w') as file:
        json.dump(tournament_data, file, indent=2)

tournament_data = load_data()
tournament_state = load_tournament_state()

if tournament_state:
    tournament_data = tournament_state

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name}')

@bot.command()
async def join(ctx):
    if ctx.author.id not in tournament_data['participants']:
        tournament_data['participants'].append(ctx.author.id)
        save_data()
        await ctx.send(f'You have joined the tournament, {ctx.author.display_name}!')
    else:
        await ctx.send(f'You are already in the tournament, {ctx.author.display_name}!')

@bot.command()
async def starttournament(ctx):
    authorized_users = [amdin_id]

    if ctx.author.id not in authorized_users:
        await ctx.send('You are not authorized to start the tournament.')
        return

    if len(tournament_data['participants']) < 1:
        await ctx.send('There are not enough participants to start the tournament.')
        return

    await ctx.send('The tournament is starting!')

    while len(tournament_data['gifs']) > 1:
        round_gifs = tournament_data['gifs'][:2]

        await ctx.send(f'**Round {tournament_data["current_round"]}** :')

        for gif in round_gifs:
            await ctx.send(gif)
            await ctx.send('React with 👍 to vote for this GIF!')

            for participant_id in tournament_data['participants']:
                participant = await bot.fetch_user(participant_id)
                if participant:
                    try:
                        dm_channel = await participant.create_dm()
                        await dm_channel.send(f'Round {tournament_data["current_round"]} - Vote for this GIF:')
                        await dm_channel.send(gif)
                    except Exception as e:
                        print(f'Error sending DM to user {participant_id}: {e}')

        tournament_data['current_round'] += 1

        # Wait for a certain time for voting (you can adjust this)
        await asyncio.sleep(60)

        votes = await count_votes(ctx, round_gifs)

        winning_gif = votes[0]['gif']
        tournament_data['gifs'].append(winning_gif)
        save_tournament_state()

    await ctx.send(f'The winner of the tournament is : {tournament_data["gifs"][0]}')

@bot.command()
async def submit(ctx, gif_url: str):
    if ctx.author.id not in tournament_data['participants']:
        await ctx.send('You are not a participant in the tournament. Use !join to join the tournament.')
        return

    # set limit of gifs to store
    if len(tournament_data['gifs']) >= 32:
        await ctx.send('The maximum number of GIFs (32) has been reached for the tournament.')
        return

    tournament_data['gifs'].append(gif_url)
    save_data()
    await ctx.send(f'Your GIF ({gif_url}) has been submitted to the tournament!')

@bot.event
async def count_votes(ctx, gifs):
    vote_counts = [{'gif': gif, 'votes': 0} for gif in gifs]

    for gif in gifs:
        await ctx.send(f'Round - Vote for this GIF:')
        await ctx.send(gif)
        await ctx.send('React with 👍 to vote for this GIF!')

    # Wait for a certain time for voting (you can adjust this)
    await asyncio.sleep(60)

    messages = await ctx.history(limit=10).flatten()

    for message in messages:
        for reaction in message.reactions:
            if reaction.emoji == '👍':
                voted_gif = next((gif for gif in gifs if gif in message.content), None)
                if voted_gif:
                    index = next((i for i, vote in enumerate(vote_counts) if vote['gif'] == voted_gif), None)
                    if index is not None:
                        vote_counts[index]['votes'] += 1

    vote_counts.sort(key=lambda x: x['votes'], reverse=True)

    return vote_counts

bot.run(TOKEN)
