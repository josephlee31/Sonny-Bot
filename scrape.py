from datetime import datetime
import pandas as pd
import requests
from bs4 import BeautifulSoup

import config
import time

# Below function converts command argument into searchable transfermarkt query.
def search_player(command_args):
    """
    Arguments:
        - command_args (str): Name of player that the user wishes to search
    Returns:
        - results_df (df): pandas df of resulting player name, age, club, position, and link
    """
    # Process command_args string
    name_query = config.tm_search + '+'.join(command_args.split())

    # Initialize empty lists for names, clubs, positions, ages, and Transfermarkt links
    p_names, p_clubs, p_positions, p_links = [], [], [], []

    # Parse through HTML data
    pageTree = requests.get(name_query, headers=config.headers)
    soup = BeautifulSoup(pageTree.content, 'lxml')

    for result in soup.find_all('tr', {'class':['even', 'odd']}):
        # Remove managers or trainers from search
        if 'spieler' in result.find_all('a')[1].get('href'):
            # Check if player is retired. If so, not included in list.
            if result.find_all('td')[3].get_text() in ["Retired", "---"]:
                continue
            p_names.append(result.find_all('td')[2].get_text())
            p_clubs.append(result.find_all('td')[3].get_text())
            p_positions.append(result.find_all('td')[4].get_text())
            p_links.append(config.tm_main + result.find_all('a')[1].get('href'))

    # Complete dataframe
    cols = {'Name': p_names,
            'Club': p_clubs,
            'Position': p_positions,
            'Link': p_links}
    results_df = pd.DataFrame(cols)
    return results_df

# Below is a function used to scrape and parse player information
def process_df(df):
    """
    Arguments:
        - df (pandas df) --> Pandas df (single row) with columns Name, Club, Position, Link
    Returns:
        - player_info (dict) --> Dictionary version of df
        - player_stats_json (json) --> Scraped json file of player match stats
        - player_rumors_json (json) --> Scraped json file of player transfer rumors
    """
    # Initialize an empty dictionary to store info
    player_info = {}

    for col in df.columns:
        # More specific position information will be retrieved later
        if col == 'Position':
            pass
        else:
            player_info[col.lower()] = df.loc[0][col]

    # Get stats such as Goals, Assists, etc.
    player_info, player_stats_json, player_rumors_json = get_stats(player_info)

    return player_info, player_stats_json, player_rumors_json

# Below is a function used to retrieve player stats and rumors from TransferMarkt's API.
def get_stats(p_info):
    """
    Arguments:
        - player_info (dict): Dictionary of player name, club, and TransferMarkt URL
    Returns:
    """

    # Retrieve player's TransferMarkt URL and ID
    player_url = p_info['link']
    p_info['id'] = player_url.split("/")[-1]

    # Perform the scrape, obtain HTML data in soup
    pageTree = requests.get(player_url, headers=config.headers)
    soup = BeautifulSoup(pageTree.content, 'lxml')

    # Retrieve player image URL
    p_info['image_url'] = soup.find('img',
                                    {'class': 'data-header__profile-image'}).get('src')

    # Retrieve player position
    for label in soup.find_all('li', {'class': 'data-header__label'}):
        if label.get_text(strip=True).startswith('Position:'):
            p_info['position'] = label.get_text(strip=True).replace('Position:', '')

    # Get player stats (Injury, International Calls)
    try:
        p_info["status"] = soup.find_all('div', {'class': 'verletzungsbox'})[0].find_all('div', {'class': 'text'})[0].get_text(separator = ': ', strip=True)
    except IndexError:
        p_info["status"] = "Available"

    # Retrieve club page link
    p_info['clublink'] = soup.find_all('span', {'class': 'data-header__club'})[0].find_all('a')[0].get('href')

    # Retrieve player stats
    stats_link = "https://www.transfermarkt.us/ceapi/player/" + p_info['id'] + "/performance"
    response = requests.get(stats_link, headers=config.headers, timeout=1)

    # Stats are stored in a .json file
    player_stats_json = response.json()

    # Clean up .json file
    for tournament in player_stats_json:
        # Unique case of "AFC Champions League" being two rows long despite being 20 characters
        if tournament['competitionDescription'] == 'AFC Champions League':
            tournament['competitionDescription'] = 'AFC CL'

    # Retrieve player transfer rumors
    rumor_link = 'https://www.transfermarkt.us/ceapi/currentRumors/player/' + p_info['id']
    response = requests.get(rumor_link, headers=config.headers, timeout=1)
    rumors_json = response.json()['rumors']

    # Check if rumors exist:
    if rumors_json:
        # Initialize empty dictionary for rumors
        player_rumors = {}
        for rumor in rumors_json:
            club = rumor['club']['name']
            # Transfermarkt sometimes has duplicate team entries, so ensure there are no duplicates:
            if club in player_rumors:
                pass
            else:
                player_rumors[club] = rumor['probability']
        
        # Clean up dictionary for embeds otuput
        player_rumors_embeds = {'teams': "", 'probability': ""}
        for team in player_rumors:
            player_rumors_embeds['teams'] += f"{team}\n"
            if not player_rumors[team]:
                player_rumors_embeds['probability'] += "Unknown\n"
            else:
                player_rumors_embeds['probability'] += f"{player_rumors[team]}%\n"

    else:
        player_rumors_embeds = None
        
    return p_info, player_stats_json, player_rumors_embeds

# Below function converts command argument into searchable transfermarkt query. 
def process_club(command_args):
    name_query = config.tm_search + '+'.join(command_args.split())

    # Perform the scrape, obtain HTML data in soup
    pageTree = requests.get(name_query, headers=config.headers)
    soup = BeautifulSoup(pageTree.content, 'html.parser')

    # Initialize empty lists for creating dataframe
    c_name, c_club_link = [], []

    # Start searching through the table of clubs to get club name and link
    for x in soup.find_all('td', {'class':'hauptlink'}):
        if x.find_all('a'):
            if 'startseite' in x.find_all('a')[0].get('href'):
                c_name.append(x.find_all('a')[0].get('title'))
                c_club_link.append(config.tm_main + x.find_all('a')[0].get('href'))

    # Complete dataframe
    cols = {'Club': c_name, 'Club Link': c_club_link}
    results_df = pd.DataFrame(cols)

    # Remove youth clubs
    for string_to_remove in ['Youth', 'U19', 'U21', 'U18', 'U17', 'Reserves']:
        results_df = results_df[~results_df.Club.str.contains(string_to_remove)]
    
    # Reset index
    results_df = results_df.reset_index(drop=True)
    return results_df  

def process_df_clubs(df):
    # Initialize an empty dictionary to store info
    club_info = {}

    # 1. Extract club information from df
    club_info['name'] = df.loc[0]['Club']
    club_info['link'] = df.loc[0]['Club Link']
    club_info['id'] = df.loc[0]['Club Link'].split('/')[-1]

    # Perform the scrape, obtain HTML data in soup
    club_info['link'] = club_info['link'].replace('startseite', 'spielplan')
    pageTree = requests.get(club_info['link'], headers=config.headers)
    soup = BeautifulSoup(pageTree.content, 'html.parser')

    # 2. Get club image url
    img_query = soup.find_all('div', {'class':'data-header__profile-container'})[0]
    club_info['image_url'] = img_query.find('img').get('src')

    # 3. Get club league
    club_info['league'] = soup.find_all('span', {'class':"data-header__club"})[0].get_text(strip=True)
    club_info['league_link'] = soup.find_all('span', {'class':"data-header__club"})[0].find('a').get('href')

    # 4. Get club standing
    club_info['standing'] = soup.find_all('span', {'class':"data-header__content"})[1].find('a').get_text(strip=True)

    # 5. Scrape past match results
    results = []
    for x in soup.find_all('div', {'class': 'box'}):
        h2_a = x.find('h2').find('a')
        if h2_a and club_info['league_link'] in h2_a.get('href'):
            table = x.find('div', {'class': 'responsive-table'}).find('table').find('tbody').find_all('tr')
            for table_2 in table:
                for match in table_2.find_all('td', {'class': 'zentriert'}):
                    a_span = match.find('a').find('span') if match.find('a') else None
                    if a_span:
                        score = a_span.text.strip()
                        if score[0] != '-':
                            result = a_span.get('class')
                            results.append('D' if not result else 'W' if result[0] == 'greentext' else 'L')

    club_info['past_results'] = (" ").join(results[-5:])

    # 6. Get next match info
    page = 'https://www.transfermarkt.us/ceapi/nextMatches/team/' + club_info['id']
    pageTree = requests.get(page, headers=config.headers)

    teams = pageTree.json()['teams']
    next_matches = pageTree.json()['matches']

    club_info['next_match_timestamp'] = ""
    club_info['next_match_opponent_name'] = ""
    club_info['next_match_league'] = ""

    for match in next_matches[0:5]:
        # Parse information
        awayteam_id = match['match']['away']
        hometeam_id = match['match']['home']
        timestamp = str(datetime.utcfromtimestamp(match['match']['time']))

        # Store in dictionary
        club_info['next_match_timestamp'] += f"{timestamp}\n"
        if str(awayteam_id) == str(club_info['id']):
            club_info['next_match_opponent_name'] += f"{teams[str(hometeam_id)]['name']}\n"

        elif str(hometeam_id) == str(club_info['id']):
            club_info['next_match_opponent_name'] += f"{teams[str(awayteam_id)]['name']}\n"

        club_info['next_match_league'] += f"[{match['competition']['label']}]({match['competition']['link']})\n"
    
    return club_info
