# -*- coding: utf-8 -*-
"""Projeto Fim de Master Pressão Psicológica Sporting CP.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1Sts4MhnzXYTFsWYhs8X8RuY_54Yc3jxS
"""

import pandas as pd
import sys
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
from datetime import datetime, timedelta

#connect code to google drive

from google.colab import drive
drive.mount('/content/drive')

#import crowd and ticket sales data
crowd_support_df = pd.read_excel(r'/content/Atendência Liga Portuguesa.xlsx')
#import match data
LigaPTResults = pd.read_excel(r'/content/LigaPTResults.xlsx')
#import team quality 538 (use API in final version)
spi_portugal = pd.read_excel(r'/content/spi_portugal.xlsx') # pra versão final usar o API da 538
#import team quality Opta
Opta_Power_Ranking = pd.read_excel(r'/content/Opta_Power_Ranking.xlsx')
#put the 2 of them together
spi_portugal['rating'] = spi_portugal['name'].map(Opta_Power_Ranking.set_index('name')['rating'])
spi_portugal['elo'] = round((spi_portugal['spi'] * 2 + spi_portugal['rating']) / 3, 2)
spi_portugal['elo_normalized'] = round((spi_portugal['elo'] - spi_portugal['elo'].min()) / (spi_portugal['elo'].max() - spi_portugal['elo'].min()),3)
spi_portugal['elo_category'] = pd.cut(spi_portugal['elo_normalized'], bins=[-0.1, 0.2, 0.4, 0.6, 0.8, 1], labels=[1, 2, 3, 4, 5])
spi_portugal_ranked = spi_portugal.sort_values(by='elo', ascending=False)
spi_portugal

# Unified example usage
team = "Sporting"
date = "26/05/2023"
date = pd.to_datetime(date, format='%d/%m/%Y')

# Calculate the day before the given date
previous_day = date - timedelta(days=1)

def find_opposition(team_name, date, LigaPTResults):
    date = pd.to_datetime(date, format='%d/%m/%Y')
    # Find the row that matches the date and team name
    row = LigaPTResults[(LigaPTResults['date'] == date) & ((LigaPTResults['home.team'] == team_name) | (LigaPTResults['away.team'] == team_name))]

    # Check if the team is in the home team column
    if row['home.team'].item() == team_name:
        opposition = row['away.team'].item()
    else:
        opposition = row['home.team'].item()

    return opposition

opposition = find_opposition(team, date, LigaPTResults)





# Code to calculate the League Table


def calculate_league_table(date, LigaPTResults):
    # Filter the results dataframe based on the specified date
    date = pd.to_datetime(date, format='%d/%m/%Y')
    filtered_results = LigaPTResults[LigaPTResults['date'] <= date]

    # Create an empty table with columns for team, games, wins, draws, losses, points, goals scored, goals conceded, and goal difference
    table = pd.DataFrame(columns=['Team', 'Games', 'Win', 'Draw', 'Loss', 'Points', 'Goals Scored', 'Goals Conceded', 'Goal Difference'])

    # Iterate over each row in the filtered results dataframe
    for index, row in filtered_results.iterrows():
        home_team = row['home.team']
        away_team = row['away.team']
        home_goals = row['home.goals']
        away_goals = row['away.goals']

        # Update the table with the match results for the home team
        if home_team not in table['Team'].values:
            table = pd.concat([table, pd.DataFrame([[home_team, 0, 0, 0, 0, 0, 0, 0, 0]], columns=table.columns)])
        if away_team not in table['Team'].values:
            table = pd.concat([table, pd.DataFrame([[away_team, 0, 0, 0, 0, 0, 0, 0, 0]], columns=table.columns)])

        table.loc[table['Team'] == home_team, 'Goals Scored'] += home_goals
        table.loc[table['Team'] == home_team, 'Goals Conceded'] += away_goals
        table.loc[table['Team'] == home_team, 'Goal Difference'] += home_goals - away_goals

        table.loc[table['Team'] == away_team, 'Goals Scored'] += away_goals
        table.loc[table['Team'] == away_team, 'Goals Conceded'] += home_goals
        table.loc[table['Team'] == away_team, 'Goal Difference'] += away_goals - home_goals

        # Update the Games, Wins, Draws, Losses, and Points columns for both teams
        table.loc[table['Team'] == home_team, 'Games'] += 1
        table.loc[table['Team'] == away_team, 'Games'] += 1

        if home_goals > away_goals:
            table.loc[table['Team'] == home_team, 'Win'] += 1
            table.loc[table['Team'] == home_team, 'Points'] += 3
            table.loc[table['Team'] == away_team, 'Loss'] += 1
        elif home_goals < away_goals:
            table.loc[table['Team'] == away_team, 'Win'] += 1
            table.loc[table['Team'] == away_team, 'Points'] += 3
            table.loc[table['Team'] == home_team, 'Loss'] += 1
        else:
            table.loc[table['Team'] == home_team, 'Draw'] += 1
            table.loc[table['Team'] == home_team, 'Points'] += 1
            table.loc[table['Team'] == away_team, 'Draw'] += 1
            table.loc[table['Team'] == away_team, 'Points'] += 1

    # Calculate the goal difference column
    table['Goal Difference'] = table['Goals Scored'] - table['Goals Conceded']

    # Sort the table in descending order of points
    table = table.sort_values(by=['Points'], ascending=False).reset_index(drop=True)

    return table




league_tablebefore = calculate_league_table(previous_day, LigaPTResults)
league_tableafter = calculate_league_table(date, LigaPTResults)

# Sort the dataframe by the specified columns in descending order
league_tablebefore = league_tablebefore.sort_values(by=["Points", "Win", "Goal Difference", "Goals Scored"], ascending=False)
league_tableafter = league_tableafter.sort_values(by=["Points", "Win", "Goal Difference", "Goals Scored"], ascending=False)

# Reset the index of the dataframe
league_tablebefore = league_tablebefore.reset_index(drop=True)
league_tableafter = league_tableafter.reset_index(drop=True)

# Add the position column
league_tablebefore["Position"] = league_tablebefore.index + 1
league_tableafter["Position"] = league_tableafter.index + 1

if len(league_tablebefore) < 18:
    league_tablebefore = league_tableafter.copy()


#Function to calculate complete Pre-Game Mental Pressure




def calculate_mental_pressure_metric(importance, scoreline, opposition_quality, crowd_support, away_game, team_form, recent_encounters):
    # Pesos
    weights = {
        'importance': 0.35,
        'scoreline': 0.1,
        'opposition_quality': 0.15,
        'crowd_support': 0.1,
        'away_game': 0.05,
        'team_form': 0.15,
        'recent_encounters': 0.1
    }

    # Divisão equânime dos pesos caso não seja partida eliminatória ou análise individual de jogador: scoreline or recent_performance is 0
    if scoreline == 0:
        non_zero_weights = [w for w in weights if w not in ['scoreline']]
        adjusted_weight_sum = sum(weights[w] for w in non_zero_weights)
        adjusted_weight = adjusted_weight_sum / len(non_zero_weights)

        weights['scoreline'] = adjusted_weight

    # Media Ponderada
    weighted_sum = (importance * weights['importance']) + (scoreline * weights['scoreline']) + \
                   (opposition_quality * weights['opposition_quality']) + \
                   (crowd_support * weights['crowd_support']) + \
                   (away_game * weights['away_game']) + \
                   (team_form * weights['team_form']) + \
                   (recent_encounters * weights['recent_encounters'])

    return weighted_sum




# Code to calculate Topic 1: Game Importance




def calculate_importance_value(team, date, league_tablebefore, league_tableafter, LigaPTResults,opposition):
    date = pd.to_datetime(date, format='%d/%m/%Y')
    team_positionbefore = league_tablebefore.loc[league_tablebefore['Team'] == team, 'Position'].values[0]
    team_pointsbefore = league_tablebefore.loc[league_tablebefore['Team'] == team, 'Points'].values[0]
    team_gamebefore = league_tablebefore.loc[league_tablebefore['Team'] == team, 'Games'].values[0]
    team_positionafter = league_tableafter.loc[league_tableafter['Team'] == team, 'Position'].values[0]
    team_pointsafter = league_tableafter.loc[league_tableafter['Team'] == team, 'Points'].values[0]
    team_gamesafter = league_tableafter.loc[league_tableafter['Team'] == team, 'Games'].values[0]
    derbi = 0

    # Check if the opposition matches any of the specified rivalries
    rivalries = [
        ("Porto", "Benfica"),
        ("Porto", "Sporting"),
        ("Benfica", "Sporting"),
        ("Braga", "Vitória"),
        ("Porto", "Boavista")
    ]

    for rivalry in rivalries:
        if (team == rivalry[0] and opposition == rivalry[1]) or (team == rivalry[1] and opposition == rivalry[0]):
            derbi += 1

    position2 = list(range(team_positionbefore + 1, 12))
    position3 = list(range(10, team_positionbefore - 1))

    # Check if the team can go up in position
    for position in [6, 5, 4, 3, 2, 1]:
        if team_positionbefore > position:
            competitors_points = league_tablebefore.loc[league_tablebefore['Position'] == position, 'Points'].values
            if team_pointsbefore + 1 >= competitors_points.min() or team_pointsbefore + 3 >= competitors_points.min():
                return ((5 / 34) * team_gamesafter) + derbi

    # Check if the team can go down in position
        else:
            competitors_points = league_tablebefore.loc[league_tablebefore['Position'].isin(position2), 'Points'].values
            if competitors_points.max() + 1 >= team_pointsbefore or competitors_points.max() + 3 >= team_pointsbefore:
                return ((5 / 34) * team_gamesafter) + derbi

    # Check if the team can go down in position
    for position in [16, 17, 18]:
        if team_positionbefore < position:
            competitors_points = league_tablebefore.loc[league_tablebefore['Position'] == position, 'Points'].values
            if team_pointsbefore < competitors_points.max() + 1 or team_pointsbefore < competitors_points.max() + 3:
                return ((5 / 34) * team_gamesafter) + derbi
        # Check if the team can go up in position
        else:
            competitors_points = league_tablebefore.loc[league_tablebefore['Position'].isin(position3), 'Points'].values
            if competitors_points.min() < team_pointsbefore + 1 or competitors_points.min() < team_pointsbefore + 3:
                return ((5 / 34) * team_gamesafter) + derbi

    return ((1 / 34) * team_gamesafter)  + derbi # If the team doesn't meet the criteria for going up or down


# Code to calculate Topic 2: Recent Encounters




Confronto_Direto = pd.DataFrame({
    'Team': [team, opposition],
    'Games': [0, 0],
    'Win': [0, 0],
    'Draw': [0, 0],
    'Lost': [0, 0],
    'Points': [0, 0]
})


def calculate_recent_encounters(team, opposition, LigaPTResults, Confronto_Direto, date):
    # Create a copy of the Confronto_Direto dataframe
    confronto_direto_copy = Confronto_Direto.copy()

    # Filter the dataframe based on team and opposition
    team_matches = LigaPTResults[
        (((LigaPTResults['home.team'] == team) & (LigaPTResults['away.team'] == opposition)) |
         ((LigaPTResults['home.team'] == opposition) & (LigaPTResults['away.team'] == team))) &
        (pd.to_datetime(LigaPTResults['date'], format='%d/%m/%Y') < pd.to_datetime(date, format='%d/%m/%Y'))
    ]

    if len(team_matches) == 0:
        return 1

    # Count the number of matches and update the Confronto_Direto dataframe copy
    matches_count = len(team_matches)
    confronto_direto_copy.loc[confronto_direto_copy['Team'] == team, 'Games'] += matches_count
    confronto_direto_copy.loc[confronto_direto_copy['Team'] == opposition, 'Games'] += matches_count

    # Update the points based on the match results
    for index, match in team_matches.iterrows():
        if match['winner'] == 0:
            confronto_direto_copy.loc[confronto_direto_copy['Team'] == match['away.team'], 'Draw'] += 1
            confronto_direto_copy.loc[confronto_direto_copy['Team'] == match['home.team'], 'Draw'] += 1
            confronto_direto_copy.loc[confronto_direto_copy['Team'] == match['away.team'], 'Points'] += 1
            confronto_direto_copy.loc[confronto_direto_copy['Team'] == match['home.team'], 'Points'] += 1
        elif match['winner'] == match['teamId.home']:
            confronto_direto_copy.loc[confronto_direto_copy['Team'] == match['home.team'], 'Win'] += 1
            confronto_direto_copy.loc[confronto_direto_copy['Team'] == match['home.team'], 'Points'] += 3
            confronto_direto_copy.loc[confronto_direto_copy['Team'] == match['away.team'], 'Lost'] += 1
        elif match['winner'] == match['teamId.away']:
            confronto_direto_copy.loc[confronto_direto_copy['Team'] == match['away.team'], 'Win'] += 1
            confronto_direto_copy.loc[confronto_direto_copy['Team'] == match['away.team'], 'Points'] += 3
            confronto_direto_copy.loc[confronto_direto_copy['Team'] == match['home.team'], 'Lost'] += 1

    # Verify if there are matching rows before accessing the points values
    if team in confronto_direto_copy['Team'].values and opposition in confronto_direto_copy['Team'].values:
        team_points = confronto_direto_copy.loc[confronto_direto_copy['Team'] == team, 'Points'].values[0]
        opposition_points = confronto_direto_copy.loc[confronto_direto_copy['Team'] == opposition, 'Points'].values[0]
        if team_points == opposition_points:
            return 2  # Draw
        elif team_points > opposition_points:
            return 1  # Team 1 has more points
        else:
            return 4  # Team 2 has more points
    else:
        return 1  # Default value if there are no matching rows



# Code to calculate Topic 4: Opposition Quality




def opposition_quality(spi_portugal, team, opposition):
    team_elo_category = spi_portugal.loc[spi_portugal['name'] == team, 'elo_category'].values[0]
    opposition_elo_category = spi_portugal.loc[spi_portugal['name'] == opposition, 'elo_category'].values[0]

    if team_elo_category >= opposition_elo_category + 2:
        return 1
    elif team_elo_category >= opposition_elo_category + 1:
        return 2
    elif team_elo_category == opposition_elo_category:
        return 3
    elif team_elo_category <= opposition_elo_category - 2:
        return 5
    elif team_elo_category <= opposition_elo_category - 1:
        return 4
    else:
        return None



#Function to calculate Topic 5: Level of Crowd Support




def calculate_crowd_support(opposition, LigaPTResults, date, crowd_support_df):
    # Filter the dataframe based on the home_team_name
    team_row = crowd_support_df[crowd_support_df['TIME'] == opposition]
    date = pd.to_datetime(date, format='%d/%m/%Y')

    if len(team_row) == 0:
        # If the team is not found in the dataframe, return a default value (e.g., neutral crowd)
        print("Time não encontrado.")
        return None

    # Calculate the weighted average
    capacidade_weight = 0.1
    atendimento_weight = 0.4

    weighted_avg = (
        (team_row['CAPACIDADE'] * capacidade_weight + team_row['ATENDÊNCIA MÉDIA'] * atendimento_weight) *
        team_row['TAXA DE OCUPAÇÃO']
    )

    # Determine the crowd support value based on the weighted average, since the Portuguese league has 18 teams
    # we divided it into 3 categories of 6 stadiums. These results are exclusive for the Portuguese league.
    crowd_support_value = None

    if len(LigaPTResults.loc[(LigaPTResults['date'] == date) & (LigaPTResults['away.team'] == opposition)]) > 0:
        crowd_support_value = 1  # Home crowd
    else:
        if weighted_avg.apply(lambda x: x >= 1100).any():
            crowd_support_value = 5  # Hostile crowd
        elif weighted_avg.apply(lambda x: x >= 370).any():
            crowd_support_value = 3  # Enthusiastic crowd
        else:
            crowd_support_value = 1  # Neutral crowd

    return crowd_support_value




# Code to calculate Topic 7: Home or Away game



def check_team_home_or_away(team, date, LigaPTResults):
    date = pd.to_datetime(date, format='%d/%m/%Y')
    # Filter the dataframe based on the specified team name and date
    home_match = LigaPTResults[(LigaPTResults['home.team'] == team) & (LigaPTResults['date'] == date)]
    away_match = LigaPTResults[(LigaPTResults['away.team'] == team) & (LigaPTResults['date'] == date)]

    if not home_match.empty:
        return 0  # Team played as the home team on the given date
    elif not away_match.empty:
        return 1  # Team played as the away team on the given date
    else:
        return -1  # Team did not play on the given date




# Code to calculate Topic 8: Teams Form




def get_team_form(team, date, LigaPTResults):
    date = pd.to_datetime(date, format='%d/%m/%Y')
    # Filter the dataframe based on team and date
    team_matches = LigaPTResults[(LigaPTResults['home.team'] == team) | (LigaPTResults['away.team'] == team)]
    team_matches = team_matches[team_matches['date'] < date]

    # Sort the matches by date in descending order and select the last 5 matches
    team_matches = team_matches.sort_values('date', ascending=False).head(5)

    # Create the team_form dataframe with columns: "Team", "Games", "Win", "Draw", "Lost", "Points"
    team_form = pd.DataFrame({'Team': [team],
                              'Games': [0],
                              'Win': [0],
                              'Draw': [0],
                              'Lost': [0],
                              'Points': [0]})

    # Update the team_form dataframe based on the match results
    for index, match in team_matches.iterrows():
        if match['winner'] == 0:
            team_form['Draw'] += 1
            team_form['Points'] += 1
        elif match['winner'] == match['teamId.home'] and team_form['Team'].iloc[0] == match['home.team']:
            team_form['Win'] += 1
            team_form['Points'] += 3
        elif match['winner'] == match['teamId.away'] and team_form['Team'].iloc[0] == match['away.team']:
            team_form['Win'] += 1
            team_form['Points'] += 3
        else:
            team_form['Lost'] += 1

    # Update the Games column
    team_form['Games'] = team_form['Win'] + team_form['Draw'] + team_form['Lost']

    return team_form

team_form = get_team_form(team, date, LigaPTResults)
opposition_form = get_team_form(opposition, date, LigaPTResults)

def calculate_form_value(team_form, opposition_form):
    team_points = team_form['Points'].values[0]
    opposition_points = opposition_form['Points'].values[0]

    if team_points >= 10:
        if opposition_points > 10:
            return 3
        elif opposition_points > 5:
            return 2
        else:
            return 1
    elif team_points > 5:
        if opposition_points > 10:
            return 4
        elif opposition_points > 5:
            return 2
        else:
            return 1
    else:
        if opposition_points > 10:
            return 5
        elif opposition_points > 5:
            return 4
        else:
            return 3


# Exemplo de Valores

importance_value = calculate_importance_value(team, date, league_tablebefore, league_tableafter, LigaPTResults,opposition)
scoreline_value = 0 # From 1 to 3 (0 if it is not a knockout 2nd leg match)
opposition_quality_value = opposition_quality(spi_portugal, team, opposition)
crowd_support_value = calculate_crowd_support(opposition, LigaPTResults, date, crowd_support_df)
away_game_value = check_team_home_or_away(team, date, LigaPTResults)
team_form_value = calculate_form_value(team_form, opposition_form)
recent_encounters_value = calculate_recent_encounters(team, opposition, LigaPTResults, Confronto_Direto, date)

# Calculo da métrica


metric = calculate_mental_pressure_metric(importance_value, scoreline_value, opposition_quality_value,
                                          crowd_support_value, away_game_value,
                                          team_form_value, recent_encounters_value)


print(f"The importance value for {team} on {date} is {importance_value}") # tópico 1
print("The recent encounters value for the teams is:", recent_encounters_value) # tópico 2
print("Opposition Quality Value:", opposition_quality_value) # tópico 4
print("The crowd support value for the game is:", crowd_support_value) # tópico 5
print("The away game value for the game is:", away_game_value) # tópico 7
print("The teams form for the game team is:", team_form_value) # tópico 8
print("The pre-game mental pressure metric is: {:.3f}".format(metric)) # Final

def normalize_metric(metric):
    min_metric = 0.61
    max_metric = 4.85
    normalized_metric = (metric - min_metric) / (max_metric - min_metric)
    return normalized_metric

normalized_metric =   normalize_metric(metric)
print("The pre-game mental pressure normalized metric is: {:.3f}".format(normalized_metric)) # Final

def process_events(eventsSCP):
    goalstime = pd.DataFrame(columns=['matchId', 'team1_goals', 'team1_minutes', 'team2_goals', 'team2_minutes'])

    for matchId in eventsSCP['matchId'].unique():
        match_events = eventsSCP[eventsSCP['matchId'] == matchId]

        team1_goals = []
        team1_minutes = []
        team2_goals = []
        team2_minutes = []

        for index, row in match_events.iterrows():
            if row['shot.isGoal'] == 'True':
                team1_goals.append(1)
                team1_minutes.append(row['minute'])
            elif 'conceded_goal' in row['type.secondary'] or 'penalty_conceded_goal' in row['type.secondary']:
                team2_goals.append(1)
                team2_minutes.append(row['minute'])

        goalstime = pd.concat([goalstime, pd.DataFrame({
            'matchId': [matchId],
            'team1_goals': [team1_goals],
            'team1_minutes': [team1_minutes],
            'team2_goals': [team2_goals],
            'team2_minutes': [team2_minutes]
        })], ignore_index=True)

    return goalstime

eventsSCP = pd.read_excel('/content/eventsSCP.xlsx')
goalstime = process_events(eventsSCP)
goalstime

def find_match_id(team_name, date, LigaPTResults):
    date = pd.to_datetime(date, format='%d/%m/%Y')
    row = LigaPTResults[(LigaPTResults['date'] == date) & ((LigaPTResults['home.team'] == team_name) | (LigaPTResults['away.team'] == team_name))]

    match_id = row['matchId'].item()

    return match_id

match_id = find_match_id(team, date, LigaPTResults)
print(match_id)

def extract_goals_minutes(match_id, goalstime):
    row = goalstime[goalstime['matchId'] == match_id]

    team1_goals = row['team1_goals'].iloc[0]
    team1_minutes = row['team1_minutes'].iloc[0]
    team2_goals = row['team2_goals'].iloc[0]
    team2_minutes = row['team2_minutes'].iloc[0]

    return team1_goals, team1_minutes, team2_goals, team2_minutes

team1_goals, team1_minutes, team2_goals, team2_minutes = extract_goals_minutes(match_id, goalstime)

print("Team 1 Goals:", team1_goals)
print("Team 1 Minutes:", team1_minutes)
print("Team 2 Goals:", team2_goals)
print("Team 2 Minutes:", team2_minutes)

import pandas as pd
import sys
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
from datetime import datetime
import math

max_goals1 = 5
max_goals2 = 5
specific_minute = 86

def find_opposition(team_name, date, LigaPTResults):
    date = pd.to_datetime(date, format='%d/%m/%Y')
    row = LigaPTResults[(LigaPTResults['date'] == date) & ((LigaPTResults['home.team'] == team_name) | (LigaPTResults['away.team'] == team_name))]

    if row['home.team'].item() == team_name:
        opposition = row['away.team'].item()
    else:
        opposition = row['home.team'].item()

    return opposition

opposition = find_opposition(team, date, LigaPTResults)

def extract_team_data(team_name):

    team_data = spi_portugal[spi_portugal['name'] == team_name]
    elo_rating = team_data['spi'].values[0]
    offensive_ability = team_data['off'].values[0]
    defensive_ability = team_data['def'].values[0]
    return elo_rating, offensive_ability, defensive_ability

opposition = find_opposition(team, date, LigaPTResults)

elo1, off1, def1 = extract_team_data(team)
elo2, off2, def2 = extract_team_data(opposition)


def calculate_expected_goals(elo1, elo2, off1, off2, def1, def2):
    # Calculate the expected number of goals for each team
    lambda1 = (off1 + def2) / 2
    lambda2 = (off2 + def1) / 2

    # Return the expected number of goals
    return lambda1, lambda2

def calculate_poisson_probability(lambda_val, k):
    # Calculate the Poisson probability for a given lambda value and k (number of goals)
    probability = (math.exp(-lambda_val) * (lambda_val ** k)) / math.factorial(k)
    return probability

def calculate_win_draw_loss_probabilities(elo1, elo2, off1, off2, def1, def2, max_goals1, max_goals2,goal_diff):
    lambda1, lambda2 = calculate_expected_goals(elo1, elo2, off1, off2, def1, def2)

    # Calculate win/draw/loss probabilities
    win_prob = 0.0
    draw_prob = 0.0
    loss_prob = 0.0

    for goals1 in range(max_goals1 + 1):
        for goals2 in range(max_goals2 + 1):
            if goals1 + goal_diff > goals2:
                win_prob += calculate_poisson_probability(lambda1, goals1) * calculate_poisson_probability(lambda2, goals2)
            elif goals1 + goal_diff < goals2:
                loss_prob += calculate_poisson_probability(lambda1, goals1) * calculate_poisson_probability(lambda2, goals2)
            else:
                draw_prob += calculate_poisson_probability(lambda1, goals1) * calculate_poisson_probability(lambda2, goals2)

    return win_prob, draw_prob, loss_prob

def calculate_goal_difference(goals1, minutes1, goals2, minutes2, specific_minute):

    # Find the number of goals scored by each team before the specific minute
    goals1_before = sum([1 for minute in minutes1 if minute <= specific_minute])
    goals2_before = sum([1 for minute in minutes2 if minute <= specific_minute])

    # Calculate the goal difference
    goal_diff = goals1_before - goals2_before

    return goal_diff

goal_diff = calculate_goal_difference(team1_goals, team1_minutes, team2_goals, team2_minutes, specific_minute)


def pressure_minute(minute, goal_diff):


    # Calculate the win, draw, loss probabilities for the given goal difference
    win_prob, draw_prob, loss_prob = calculate_win_draw_loss_probabilities(elo1, elo2, off1, off2, def1, def2, max_goals1, max_goals2, goal_diff)

    if goal_diff < 0:
        # Calculate X for goal difference less than 0
        X = abs(win_prob - calculate_win_draw_loss_probabilities(elo1, elo2, off1, off2, def1, def2, max_goals1, max_goals2, goal_diff - 1)[0]) + \
            abs(win_prob - calculate_win_draw_loss_probabilities(elo1, elo2, off1, off2, def1, def2, max_goals1, max_goals2, goal_diff + 1)[0]) + \
            abs(draw_prob - calculate_win_draw_loss_probabilities(elo1, elo2, off1, off2, def1, def2, max_goals1, max_goals2, goal_diff - 1)[1]) + \
            abs(draw_prob - calculate_win_draw_loss_probabilities(elo1, elo2, off1, off2, def1, def2, max_goals1, max_goals2, goal_diff + 1)[1])
    else:
        # Calculate X for goal difference greater than or equal to 0
        X = abs(win_prob - calculate_win_draw_loss_probabilities(elo1, elo2, off1, off2, def1, def2, max_goals1, max_goals2, goal_diff - 1)[0]) + \
            abs(win_prob - calculate_win_draw_loss_probabilities(elo1, elo2, off1, off2, def1, def2, max_goals1, max_goals2, goal_diff + 1)[0])

    # Calculate the pressure
    pressure = X * minute / 98.66

    return pressure


print("Team", team, " Elo:", elo1, "Offensive:", off1, "Defensive:", def1)
print("Team", opposition, " Elo:", elo2, "Offensive:", off2, "Defensive:", def2)
expected_goals1, expected_goals2 = calculate_expected_goals(elo1, elo2, off1, off2, def1, def2)
print("Gols ",team,":", expected_goals1)
print("Gols", opposition, ":", expected_goals2)
print("Goal difference at minute for ", team, "at", specific_minute," minutes:", goal_diff)
win_prob, draw_prob, loss_prob = calculate_win_draw_loss_probabilities(elo1, elo2, off1, off2, def1, def2, max_goals1, max_goals2, goal_diff)
print("Win probability (",team," with", goal_diff, " goal difference):", win_prob)
print("Draw probability (",team," with", goal_diff, " goal difference):", draw_prob)
print("Loss probability (",team," with", goal_diff, " goal difference):", loss_prob)
pressure = pressure_minute(specific_minute, goal_diff)
print("Pressure at minute", specific_minute, "with goal difference", goal_diff, ":", pressure)

def live_and_pre_game_pressure(normalized_metric, pressure):
    final_pressure = (normalized_metric+pressure)/2
    return final_pressure

final_pressure =   round(live_and_pre_game_pressure(normalized_metric, pressure), 4)

print("Final pressure at minute", specific_minute, "with goal difference", goal_diff, ":", final_pressure)

import datetime

def get_match_date(match_id, LigaPTResults):
    row = LigaPTResults[LigaPTResults['matchId'] == match_id]
    match_date = row['date'].iloc[0]
    match_date_formatted = datetime.datetime.strftime(match_date, '%d/%m/%Y')

    return match_date_formatted

match_id = 5369565  # Replace with the desired matchId
match_date = get_match_date(match_id, LigaPTResults)
print("Match Date:", match_date)

eventsSCP = pd.read_excel('/content/eventsSCP.xlsx')
filtered_events = eventsSCP[eventsSCP['type.primary'] == 'shot'].copy()
filtered_events

import pandas as pd
from tqdm import tqdm

team = "Sporting"  # Doesn't change
total_rows = len(filtered_events)


# Iterate over each row in the events dataframe
for index, row in tqdm(filtered_events.iterrows(), total=total_rows, desc="Calculating Pressure"):

    Confronto_Direto = pd.DataFrame({
    'Team': [team, opposition],
    'Games': [0, 0],
    'Win': [0, 0],
    'Draw': [0, 0],
    'Lost': [0, 0],
    'Points': [0, 0]
    })

    # Get the match date and opposition
    date = get_match_date(row['matchId'], LigaPTResults)
    opposition = find_opposition(team, date, LigaPTResults)
    date = pd.to_datetime(date, format='%d/%m/%Y')


    # Calculate the day before the given date
    previous_day = date - timedelta(days=1)
    date = get_match_date(row['matchId'], LigaPTResults)

    # Calculate the league table

    league_tablebefore = calculate_league_table(previous_day, LigaPTResults)
    league_tableafter = calculate_league_table(date, LigaPTResults)

    # Sort the dataframe by the specified columns in descending order
    league_tablebefore = league_tablebefore.sort_values(by=["Points", "Win", "Goal Difference", "Goals Scored"], ascending=False)
    league_tableafter = league_tableafter.sort_values(by=["Points", "Win", "Goal Difference", "Goals Scored"], ascending=False)

    # Reset the index of the dataframe
    league_tablebefore = league_tablebefore.reset_index(drop=True)
    league_tableafter = league_tableafter.reset_index(drop=True)

    # Add the position column
    league_tablebefore["Position"] = league_tablebefore.index + 1
    league_tableafter["Position"] = league_tableafter.index + 1

    if len(league_tablebefore) < 18:
        league_tablebefore = league_tableafter.copy()

    # Calculate the importance value
    importance_value = calculate_importance_value(team, date, league_tablebefore, league_tableafter, LigaPTResults, opposition)

    # Set the scoreline value (assuming it doesn't change)
    scoreline_value = 0

    # Calculate the opposition quality value
    opposition_quality_value = opposition_quality(spi_portugal, team, opposition)

    # Calculate the crowd support value
    crowd_support_value = calculate_crowd_support(opposition, LigaPTResults, date, crowd_support_df)

    # Calculate the away game value
    away_game_value = check_team_home_or_away(team, date, LigaPTResults)

    # Calculate the team form value
    team_form = get_team_form(team, date, LigaPTResults)
    opposition_form = get_team_form(opposition, date, LigaPTResults)
    team_form_value = calculate_form_value(team_form, opposition_form)

    # Calculate the recent encounters value if available
    recent_encounters_value = calculate_recent_encounters(team, opposition, LigaPTResults, Confronto_Direto, date)

    # Calculate the mental pressure metric
    metric = calculate_mental_pressure_metric(importance_value, scoreline_value, opposition_quality_value,
                                              crowd_support_value, away_game_value,
                                              team_form_value, recent_encounters_value)

    # Normalize the metric
    normalized_metric = normalize_metric(metric)

    # Find the matchId for the specific row
    match_id = row['matchId']

    # Extract goals and minutes for the matchId
    team1_goals, team1_minutes, team2_goals, team2_minutes = extract_goals_minutes(match_id, goalstime)

    # Set the max goals for each team (assuming it doesn't change)
    max_goals1 = 5
    max_goals2 = 5

    # Extract team data (elo, off, def)
    elo1, off1, def1 = extract_team_data(team)
    elo2, off2, def2 = extract_team_data(opposition)

    # Calculate the goal difference using the specific minute from the row
    specific_minute = row['minute']
    goal_diff = calculate_goal_difference(team1_goals, team1_minutes, team2_goals, team2_minutes, specific_minute)

    # Calculate the expected goals
    expected_goals1, expected_goals2 = calculate_expected_goals(elo1, elo2, off1, off2, def1, def2)

    # Calculate the win/draw/loss probabilities
    win_prob, draw_prob, loss_prob = calculate_win_draw_loss_probabilities(elo1, elo2, off1, off2, def1, def2,
                                                                            max_goals1, max_goals2, goal_diff)

    # Calculate the pressure using the specific minute and goal difference
    pressure = pressure_minute(specific_minute, goal_diff)

    # Calculate the final pressure
    final_pressure = round(live_and_pre_game_pressure(normalized_metric, pressure), 4)

    # Update the 'pressure' column in the events dataframe with the calculated value
    filtered_events.at[index, 'pressure'] = final_pressure

# Print the updated dataframe
filtered_events

from google.colab import files

# Save the filtered_events dataframe as an Excel file
filtered_events.to_excel('filtered_events.xlsx', index=False)

# Download the Excel file to your local PC
files.download('filtered_events.xlsx')

# Calculate the quintiles
quintiles = filtered_events['pressure'].quantile([0.2, 0.4, 0.6, 0.8])

# Print the quintiles
print("Quintiles:")
print("20%:", quintiles[0.2])
print("40%:", quintiles[0.4])
print("60%:", quintiles[0.6])
print("80%:", quintiles[0.8])

# Define the quintile labels with numbering
quintile_labels = ['1. Very Low Pressure', '2. Low Pressure', '3. Normal Pressure', '4. High Pressure', '5. Very High Pressure']

# Add the "pressure_level" column using quintile labels
filtered_events['pressure_level'] = pd.qcut(filtered_events['pressure'], q=5, labels=quintile_labels)

# Print the updated dataframe
print("Updated DataFrame:")
filtered_events

from google.colab import files

# Save the filtered_events dataframe as an Excel file
filtered_events.to_excel('filtered_events.xlsx', index=False)

# Download the Excel file to your local PC
files.download('filtered_events.xlsx')

# Count the occurrences of each "player.id" value in each quintile bin
quintile_counts = filtered_events.groupby(['player.id', 'pressure_level']).size().unstack(fill_value=0)

# Print the quintile counts
print("Quintile Counts:")
quintile_counts

# Filter the players with sum greater than 20
filtered_quintile_counts = quintile_counts[quintile_counts.sum(axis=1) > 20]

# Print the filtered dataframe
print("Filtered Quintile Counts:")
filtered_quintile_counts

