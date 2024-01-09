import discord
from datetime import datetime

import config

transfermarkt_footer = "Data obtained from transfermarkt.us"

# Below is a function for initializing embed color.
def embed_setup(r, g, b):
    embed = discord.Embed(
        color = discord.Color.from_rgb(r, g, b)
    )
    return embed

# Below is a function to produce a simple embed with a title and message.
def simple_embed(title, msg):
    embed = embed_setup(255, 255, 255)
    embed.add_field(name=title, value=msg, inline=True)
    
    embed.timestamp = datetime.now()
    return embed

# Below is a function to produce an embed for the !help command.
def command_help():
    embed = embed_setup(255, 255, 255)
    embed.add_field(name='!hello', value = "Test command to check whether or not Sonny Bot is up.", inline=False)
    embed.add_field(name='!player [player_name]', value = "Search the TransferMarkt profile of a player.", inline=False)
    embed.add_field(name='!club [club_name]', value = "Search the TransferMarkt profile of a team.", inline=False)
    return embed

# Below is a function to produce an embed, displaying all resulting players upon searching.
def resulting_players_embed(df, player_name):
    embed = embed_setup(255, 255, 255)
    embed.set_author(
        name = f"Multiple players found with the name '{player_name}'. Please type the command [index] to select your player. \n")
    
    players_dict = {'index': "", 'names': "", 'clubs': "", 'positions': ""}

    for ind in df.index:
        # Extract player name, position
        name = df['Name'][ind]
        position = df['Position'][ind]
        club = df['Club'][ind]

        # Update dictionary
        players_dict['index'] += f'{ind+1}\n'
        players_dict['names'] += f'{name} ({position})\n'
        players_dict['clubs'] += f'{club}\n'
    
    embed.add_field(name='Index', value=players_dict['index'], inline=True)
    embed.add_field(name='Name (Position)', value=players_dict['names'], inline=True)
    embed.add_field(name='Club', value=players_dict['clubs'], inline=True)
    
    embed.timestamp = datetime.now()
    embed.set_footer(text=transfermarkt_footer)
    return embed

# Below is a function to produce an embed, displaying all resulting clubs upon searching.
def resulting_clubs_embed(df, club_name):
    embed = embed_setup(255, 255, 255)
    embed.set_author(
        name = f"Multiple clubs found with the name '{club_name}'. Please type the command [index] to select your club. \n")
    
    clubs_dict = {'index': "", 'clubs': ""}

    for ind in df.index:
        club = df['Club'][ind]

        # Update clubs_dict
        clubs_dict['index'] += f'{ind+1}\n'
        clubs_dict['clubs'] += f'{club}\n'
    
    embed.add_field(name='Index', value=clubs_dict['index'], inline=True)
    embed.add_field(name='Club', value=clubs_dict['clubs'], inline=True)

    embed.timestamp = datetime.now()
    embed.set_footer(text=transfermarkt_footer)
    return embed

# Below is a function to display overall player information.
def display_player(player_data, player_stats_json, player_rumors):
    
    # Set up embed
    embed = embed_setup(255, 255, 255)
    embed.set_author(name = f"⚽{player_data['name']} (2023-24 Stats)")
    embed.set_thumbnail(url = player_data['image_url'])

    # 1. Display player club data
    club = f"[{player_data['club']}]({config.tm_main + player_data['clublink']})"
    embed.add_field(name='Current Club', value = club, inline=True)
    
    # 2. Display player position data
    embed.add_field(name='Position', value = player_data['position'], inline=False)

    # 3. Display player statistics for the current season
    # Displayed information is different depending on player position.
    if player_data['position'] == 'Goalkeeper':
        embed = display_goalkeeper(player_data['club'], player_stats_json, embed)

    else:
        embed = display_outfield(player_data['club'], player_stats_json, embed)
    
    # 4. Add player status, and line break
    embed.add_field(name='Availability Status', value=player_data['status'], inline=False)

    # 5. Display transfer rumors
    if player_rumors:
        embed.add_field(name='Team (Transfer Rumors)', value=player_rumors['teams'], inline=True)
        embed.add_field(name='Probability', value=player_rumors['probability'], inline=True)
    
    else:
        embed.add_field(name='Transfer Rumors', value="None", inline=False)

    # Add Transfermarkt Profile
    embed.add_field(name='TransferMarkt Profile', value=f"[Link]({player_data['link']})", inline=False)

    # Final touches
    embed.timestamp = datetime.now()
    embed.set_footer(text=transfermarkt_footer)
    return embed

# Below is a function to display goalkeeper performance metrics.
def display_goalkeeper(club, player_stats_json, embed):
    
    # Initialize strings for display
    pl_tournament, pl_apps, pl_conc_goals = "", "", ""

    # Iterate through tournament to update player stats
    for tournament in player_stats_json:
        pl_tournament += f"{tournament['competitionDescription']}\n"

        # Change formatting depending on tournament name length
        if len(tournament['competitionDescription']) >= 21:
            pl_apps += f"{tournament['gamesPlayed']} ({tournament['cleanSheets']})\n\n"
            pl_conc_goals += f"{tournament['concededGoals']}\n\n"
        else:
            pl_apps += f"{tournament['gamesPlayed']} ({tournament['cleanSheets']})\n"
            pl_conc_goals += f"{tournament['concededGoals']}\n"
    
    # Set-up embed
    if club != 'Without Club':
        embed.add_field(name='Tournament', value=pl_tournament, inline=True)
        embed.add_field(name='Apps (CS)', value=pl_apps, inline=True)
        embed.add_field(name='Gls. Conceded', value=pl_conc_goals, inline=True)
    else:
        pass
    return embed

# Below is a function to display defender performance metrics.
def display_outfield(club, player_stats_json, embed):
    
    # Initialize strings for display
    pl_tournament, pl_apps, starting_per = "", "", ""

    # Iterate through tournament to update player stats
    for tournament in player_stats_json:
        pl_tournament += f"{tournament['competitionDescription']}\n"

        # Change formatting depending on tournament name length
        if len(tournament['competitionDescription']) >= 21:
            pl_apps += f"{tournament['gamesPlayed']} ({tournament['goalsScored']}/{tournament['assists']})\n\n"
            starting_per += f"{round(tournament['startElevenPercent'], 2)}\n\n"
        else:
            pl_apps += f"{tournament['gamesPlayed']} ({tournament['goalsScored']}/{tournament['assists']})\n"
            starting_per += f"{round(tournament['startElevenPercent'], 2)}\n"
    
    # Set-up embed
    if club != 'Without Club':
        embed.add_field(name='Tournament', value=pl_tournament, inline=True)
        embed.add_field(name='Apps (G/A)', value=pl_apps, inline=True)
        embed.add_field(name='SE (%)', value=starting_per, inline=True)
    else:
        pass
    return embed

# Below is a function to display overall team information.
def display_club(club_info, df):
    embed = embed_setup(255, 255, 255)
    embed.set_author(name = f"⚽{club_info['name']} (2023-24 Stats)")
    embed.set_thumbnail(url = club_info['image_url'])

    # Add League \
    league = f"[{club_info['league']}]({config.tm_main + club_info['league_link']})"
    embed.add_field(name='League', value = league, inline=False)

    # Add Table Position
    embed.add_field(name='Table Position', value = club_info['standing'], inline=False)

    # Add Next Match Information
    embed.add_field(name='Next Matches', value = club_info['next_match_opponent_name'], inline=True)
    embed.add_field(name='League', value = club_info['next_match_league'], inline=True)
    embed.add_field(name='Match Time', value = club_info['next_match_timestamp'], inline=True)

    # Add Domestic Form
    embed.add_field(name='Domestic League Form', value = club_info['past_results'], inline=False)

    # Add Transfermarkt Link
    embed.add_field(name='TransferMarkt Profile', value=f"[Link]({club_info['link']})", inline=False)
    return embed
