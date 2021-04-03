"""
bet.py - A simple bot made with python that will help you to predict the result of a football game using the SofaScore API

@ Bastien Lasorne - 2021
Edited by Anime no Sekai — 2021

v1.1 (beta)

data from api.sofascore.com

https://api.sofascore.com/api/v1/config/unique-tournaments/EN/football => Obtenir la liste des championnats
https://api.sofascore.com/api/v1/unique-tournament/<championship_id>/seasons => Obtenir les ID des différentes saisons de Premier League
https://api.sofascore.com/api/v1/unique-tournament/<championship_id>/season/<id_season>/standings/total => Obtenir les informations sur le championnat de Premier League
https://api.sofascore.com/api/v1/unique-tournament/17/season/29415/standings/home => Obtenir des informations sur les matchs joués à domicile en Premier League
https://api.sofascore.com/api/v1/unique-tournament/17/season/29415/standings/away => Obtenir des informations sur les matchs joués à l'extérieur en Premier League
https://api.sofascore.com/api/v1/unique-tournament/17/season/29415/rounds => Obtenir le round actuel
https://api.sofascore.com/api/v1/unique-tournament/17/season/29415/team-events/total => Obtenir l'historique des matchs de chaques équipes
https://api.sofascore.com/api/v1/unique-tournament/17/season/29415/events/round/27 => Voir les matchs pour une journée
https://api.sofascore.com/api/v1/event/8897086/odds/1/all => Obtenir les côtes pour le match

Objectif : Trouver le nombre d'appels d'API possible par heures
Envoyer un mail tout les matins avec les analyses du jour dans les 5 gros championnats
Envoyer les bons plans (comparaison côte/réalité, gros % de victoire, gros % d'avoir peu de buts, etc...)
Envoyer dans ce mail un lien qui permet de parier en simple tous les bons plan de manière automatique sur le raspberry PI

"""
# standard imports
from math import exp, factorial
from datetime import date, datetime

# pypi imports
from requests import get

# local imports
from constants import HEADERS, PROXY
from utils import convert_to_int, safe_division
from models import Probability

def get_championship(*args):
    """
    Returns the chosen Championship and Season ID
    """
    if args:
        champ_id = convert_to_int(args[0])
    else:
        print("Load the list of championships...")
        # List All the most popular championships
        championships = get("https://api.sofascore.com/api/v1/config/unique-tournaments/EN/football", headers=HEADERS, proxies=PROXY)
        if championships.status_code >= 400:
            raise AssertionError
        championships = championships.json()
        print("\n".join([f"{index + 1}. {championship['name']} - {championship['category']['flag']}" for index, championship in enumerate(championships["uniqueTournaments"])]))
        print("\nWhich championship do you want to bet on ?")
        champ_id = convert_to_int(input("=> "))
        # Find the chosen championship id
        if len(championships["uniqueTournaments"]) >= champ_id:
            champ_id = championships["uniqueTournaments"][champ_id - 1]["id"]
        else:
            raise AssertionError
    seasons = get(f"https://api.sofascore.com/api/v1/unique-tournament/{champ_id}/seasons", headers=HEADERS, proxies=PROXY) # Find the actual season id for the chosen championship
    if seasons.status_code >= 400:
        raise AssertionError
    return champ_id, seasons.json()["seasons"][0]["id"]

def proba(goal, local_goal_expected, visitor_goal_expected, local_name, visitor_name):
    """
    Returns the probability
    """
    home_proba_goal = ( float(local_goal_expected) ** goal ) * ( exp(-float(local_goal_expected)) ) / factorial(int(goal))
    visitor_proba_goal = ( float(visitor_goal_expected) ** goal ) * ( exp(-float(visitor_goal_expected)) ) / factorial(int(goal))
    print(f"Probability for {local_name} to score {goal} goals : {home_proba_goal}")
    print(f"Probability for {visitor_name} to score {goal} goals : {visitor_proba_goal}\n")
    return home_proba_goal, visitor_proba_goal

def championship_data(championship, season):
    """
    Returns the data for the chosen championship
    """
    ### GETTING THE DATA
    base_url = f"https://api.sofascore.com/api/v1/unique-tournament/{championship}/season/{season}"
    print("Load home's data...")
    home_data = get(f"{base_url}/standings/home", headers=HEADERS, proxies=PROXY)
    if home_data.status_code >= 400:
        print(home_data.status_code)
        print(home_data.text)
        print(base_url)
        raise AssertionError
    home_data = home_data.json()
    print("Load away's data...")
    away_data = get(f"{base_url}/standings/away", headers=HEADERS, proxies=PROXY)
    if away_data.status_code >= 400:
        raise AssertionError
    away_data = away_data.json()
    print("Load informations about the current round")
    round_data = get(f"{base_url}/rounds", headers=HEADERS, proxies=PROXY)
    if round_data.status_code >= 400:
        raise AssertionError
    current_round = round_data.json()["currentRound"]["round"]
    current_round_data = get(f"{base_url}/events/round/{current_round}", headers=HEADERS, proxies=PROXY)
    if current_round_data.status_code >= 400:
        raise AssertionError
    current_round_data = current_round_data.json()


    ### CALCULATING THINGS
    # COUNTING
    print("Calculating the average number of goals scored and conceded per home and away game")
    home_matches_played = 0
    home_goal_scored = 0
    home_goal_conceded = 0
    away_matches_played = 0
    away_goal_scored = 0
    away_goal_conceded = 0

    for team in home_data["standings"][0]["rows"]:
        home_matches_played += team["matches"]
        home_goal_scored += team["scoresFor"]
        home_goal_conceded += team["scoresAgainst"]

    for team in away_data["standings"][0]["rows"]:
        away_matches_played += team["matches"]
        away_goal_scored += team["scoresFor"]
        away_goal_conceded += team["scoresAgainst"]

    average_home_goal_scored = home_goal_scored / home_matches_played
    average_home_goal_conceded = home_goal_conceded / home_matches_played
    average_away_goal_scored = away_goal_scored / away_matches_played
    average_away_goal_conceded = away_goal_conceded / away_matches_played
    print(f"Average number of goals scored at home in this league : {average_home_goal_scored}")
    print(f"Average number of goals conceded at home in this league : {average_home_goal_conceded}")
    print(f"Average number of goals scored away in this league : {average_away_goal_scored}")
    print(f"Average number of goals conceded away in this league : {average_away_goal_conceded}\n")

    # Do the predictions for the games that are not already played
    print(f"Round {current_round}")

    global_probability = []

    for game in current_round_data["events"]:
        probability = Probability(game)
        print("============================================================\n")
        if game["status"]["type"] == "notstarted":
            print(f"{probability.hometeam_name} - {probability.awayteam_name} => Not yet played\n")
            # first check that we really want to calculate this one

            hometeam_id = game["homeTeam"]["id"]
            awayteam_id = game["awayTeam"]["id"]
            hometeam_name = game["homeTeam"]["name"]
            awayteam_name = game["awayTeam"]["name"]

            for team in home_data["standings"][0]["rows"]:
                if team["team"]["id"] == hometeam_id:
                    average_goal_scored_by_home_team = team["scoresFor"] / team["matches"]
                    average_goal_conceded_by_home_team = team["scoresAgainst"] / team["matches"]
                    print(f"Average Goal scored by {probability.hometeam_name} at home : {average_goal_scored_by_home_team}")
                    print(f"Average Goal scored by {probability.hometeam_name} at home : {average_goal_conceded_by_home_team}\n")
                if team["team"]["id"] == awayteam_id:
                    average_goal_scored_by_away_team = team["scoresFor"] / team["matches"]
                    average_goal_conceded_by_away_team = team["scoresAgainst"] / team["matches"]
                    print(f"Average Goal scored by {probability.awayteam_name} away : {average_goal_scored_by_away_team}")
                    print(f"Average Goal scored by {probability.awayteam_name} away : {average_goal_conceded_by_away_team}\n")

            home_attack_strength = float(average_goal_scored_by_home_team) / float(average_home_goal_scored)
            away_attack_strength = float(average_goal_scored_by_away_team) / float(average_away_goal_scored)
            home_defense_strength = float(average_goal_conceded_by_home_team) / float(average_home_goal_conceded)
            away_defense_strength = float(average_goal_conceded_by_away_team) / float(average_away_goal_conceded)

            print(f"{probability.hometeam_name} Attack Strength : {home_attack_strength}")
            print(f"{probability.awayteam_name} Attack Strength : {away_attack_strength}\n")
            print(f"{probability.hometeam_name} Defense Strength : {home_defense_strength}")
            print(f"{probability.awayteam_name} Defense Strength : {away_defense_strength}\n")

            home_goal_expectancy = float(home_attack_strength) * float(away_defense_strength) * float(average_home_goal_scored)
            away_goal_expectancy = float(away_attack_strength) * float(home_defense_strength) * float(average_away_goal_scored)

            print(f"{probability.hometeam_name}'s goal expectancy : {home_goal_expectancy}")
            print(f"{probability.awayteam_name}'s goal expectancy : {away_goal_expectancy}\n")

            results = [proba(i, home_goal_expectancy, away_goal_expectancy, hometeam_name, awayteam_name) for i in range(6)]
            probability.home_team_goal = [result[0] for result in results]
            probability.visitor_team_goal = [result[1] for result in results]

            for home_goal, home_value in enumerate(probability.home_team_goal): # might consider changing this ? (is O(n^2) needed here?)
                for away_goal, away_value in enumerate(probability.visitor_team_goal):
                    score_proba = home_value * away_value
                    probability.score_probability["{}-{}".format(home_goal, away_goal)] = score_proba

                    if home_goal > away_goal:
                        probability.result_proba.home_victory += score_proba
                    elif away_goal > home_goal:
                        probability.result_proba.away_victory += score_proba
                    else:
                        probability.result_proba.draw += score_proba

            print(f"=> Probability for {probability.hometeam_name} to win : {probability.result_proba.home_victory * 100} % \t\t Odds : {safe_division(1, probability.result_proba.home_victory)}")
            print(f"Bookmakers' odds : {probability.odds.home_victory_odds}")
            print(f"=> Probability of a draw : {probability.result_proba.draw * 100} % \t\t Odds : {safe_division(1, probability.result_proba.draw)}")
            print(f"Bookmakers' odds : {probability.odds.draw_odds}")
            print(f"=> Probability for {probability.awayteam_name} to win : {probability.result_proba.away_victory * 100} % \t\t Odds : {safe_division(1, probability.result_proba.away_victory)}")
            print(f"Bookmakers' odds : {probability.odds.away_victory_odds}")

            # Sort the probable score by probability

            probability.score_probability = {k: v for k, v in sorted(probability.score_probability.items(), key=lambda i: i[1], reverse=True)} # sorting in ascending order

            print("\nTop 5 probable scores : ")
            for index, proba_key in enumerate(list(probability.score_probability)[0:5]):
                print(f"{index + 1}. \t {proba_key} \t Probability : {probability.score_probability[proba_key] * 100} %")


            if date.today() != datetime.fromtimestamp(game["startTimestamp"]).date():
                continue
            global_probability.append(probability)
        else:
            print(f"{probability.hometeam_name} - {probability.awayteam_name} => {game['homeScore']['current']} - {game['awayScore']['current']}\n")
        print("============================================================\n")

    return global_probability

def main(*args):
    """
    The main function (wrapping up all of the functions)
    """
    print("Welcome to our bet program\n")
    if args:
        champ_id, actual_season_id = get_championship(args[0])
    else:
        champ_id, actual_season_id = get_championship()
    return championship_data(champ_id, actual_season_id)
    # Send an email if we get the argument "send_mail" equal to True
    # if "send_mail" in kwargs:
    #     if kwargs["send_mail"] == True:
    #         if not "email_address" in kwargs:
    #             print("You forgot to give us an email address")
    #         else:
    #             send_mail(kwargs["email_address"])

if __name__ == "__main__":
    main()
