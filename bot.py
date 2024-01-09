# Import dependencies
import asyncio
import os
import discord

from discord.ext import commands
from dotenv import load_dotenv

import embeds
import scrape

# Import Bot Discord Token
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

intents = discord.Intents.default()
intents.message_content = True

# Initialize client variable
client = commands.Bot(command_prefix = '!', intents=intents, help_command=None)

# Define boot-up message
@client.event
async def on_ready():
    print(f'{client.user} is running!')

# !hello command for saying hello to the bot.
@client.command(name='hello')
async def hello(ctx):
    await ctx.send("Hello, my name's Sonny!")

# !help command for a list of possible commands.
@client.command(name='help')
async def command_help(ctx):
    await ctx.send(embed=embeds.command_help())

# !player command to retrieve player statistics from a particular season. (ex. !player Udogie)
@client.command(name='player')
async def get_player(ctx, *, command_args=''):
    """
    Arguments:
        command_args (string): Name of player that the user wishes to search
    """
    # Convert command_args into searchable transfermarkt query
    df = scrape.search_player(command_args)

    # Process dataframe, check if there are no results, only one result, or multiple results
    def process_and_display_df(df):
        player_info, player_stats_json, player_rumors = scrape.process_df(df)
        embed = embeds.display_player(player_info, player_stats_json, player_rumors)
        return embed

    # Case 1: No results
    if df.shape[0] == 0:
        msg = "The player name is invalid or does not exist. Please enter a valid name."
        await ctx.send(embed=embeds.simple_embed('Error', msg))

    # Case 2: One result
    elif df.shape[0] == 1:
        # Process info such as Active/Inactive, Name, Link, etc.
        await ctx.send(embed=process_and_display_df(df))

    # Case 3: More than one result
    else:
        embed = embeds.resulting_players(df, command_args)
        await ctx.send(embed=embed)

        # Await for user's response
        def check_input(message):
            return message.author == ctx.author and message.channel == ctx.channel

        try:
            response = await client.wait_for('message', timeout=30, check=check_input)

            # Retrieve selected index
            selected_index = int(response.content)-1

            # Process the selected player
            selected_df = df.iloc[[selected_index]]
            selected_df = selected_df.reset_index(drop=True)

            # Process info such as Active/Inactive, Name, Link, etc.
            await ctx.send(embed=process_and_display_df(selected_df))

        except asyncio.TimeoutError:
            msg = "Time limit exceeded. Please try the command again."
            await ctx.send(embed=embeds.simple_embed('Error', msg))

        except ValueError:
            msg = "Incorrect response entered. Please try the command again."
            await ctx.send(embed=embeds.simple_embed('Error', msg))

        finally:
            # Delete the previous message
            await response.delete()

# !club command to retrieve club statistics from a particular season. (ex. !club Manchester United)
@client.command(name='club')
async def get_club(ctx, *, command_args=''):
    # Convert args into searchable transfermarkt query
    # Obtain dataframe of results
    df = scrape.process_club(command_args)

    # Process dataframe, check if there are no results, only one result, or multiple results
    def process_and_display_df_clubs(df):
        club_info = scrape.process_df_clubs(df)
        embed = embeds.display_club(club_info, df)
        return embed

    # Process dataframe, check if there are no results, only one result, or multiple results
    # Case 1: No results
    if df.shape[0] == 0:
        msg = "The provided club name is invalid or does not exist. Please enter a valid club name."
        await ctx.send(embed=embeds.simple_embed('Error', msg))

    # Case 2: One result
    elif df.shape[0] == 1:
        # Below is where club information will be scraped, and output using embed
        await ctx.send(embed=process_and_display_df_clubs(df))

    # Case 3: More than one result
    else:
        embed = embeds.possible_clubs_embed(df, command_args)
        await ctx.send(embed=embed)

        # Await for user's response
        def check_input(message):
            return message.author == ctx.author and message.channel == ctx.channel

        try:
            response = await client.wait_for('message', timeout=30, check=check_input)

            # Retrieve selected index
            selected_index = int(response.content)-1

            # Process selected club
            selected_df = df.iloc[[selected_index]]
            selected_df = selected_df.reset_index(drop=True)

            # Below is where club information will be scraped, and output using embed
            await ctx.send(embed=process_and_display_df_clubs(df))

        except asyncio.TimeoutError:
            msg = "Time limit exceeded. Please try the command again."
            await ctx.send(embed=embeds.simple_embed('Error', msg))

        except ValueError:
            msg = "Incorrect response entered. Please try the command again."
            await ctx.send(embed=embeds.simple_embed('Error', msg))

        finally:
            # Delete the previous message
            await response.delete()

# Run Discord Bot
client.run(TOKEN)
