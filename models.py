"""
The classes used in this project

© Anime no Sekai — 2021
"""

from constants import HEADERS, PROXY
from time import gmtime, strftime
from requests import get
from utils import convert_to_int, evaluate_fraction

class Results():
    def __init__(self) -> None:
        self.home_victory = 0
        self.draw = 0
        self.away_victory = 0

class Odds():
    def __init__(self, match_id) -> None:
        self.bookmakers_odds = get(f"https://api.sofascore.com/api/v1/event/{match_id}/odds/1/all", headers=HEADERS, proxies=PROXY)
        if self.bookmakers_odds.status_code >= 400:
            raise AssertionError
        self.bookmakers_odds = self.bookmakers_odds.json()
        self.home_victory_odds = 1 + evaluate_fraction(self.bookmakers_odds["markets"][0]["choices"][0]["fractionalValue"])
        self.draw_odds =  1 + evaluate_fraction(self.bookmakers_odds["markets"][0]["choices"][1]["fractionalValue"])
        self.away_victory_odds =  1 + evaluate_fraction(self.bookmakers_odds["markets"][0]["choices"][2]["fractionalValue"])

class Probability():
    def __init__(self, game) -> None:
        self.match_id = convert_to_int(game["id"])
        self.league_name = str(game["tournament"]["name"])
        self.hometeam_name = str(game["homeTeam"]["name"])
        self.awayteam_name = str(game["awayTeam"]["name"])
        self.game_start = strftime("%Y-%m-%d %H:%M:%S", gmtime(game["startTimestamp"]))
        self.home_team_goal = []
        self.visitor_team_goal = []
        self.score_probability = {}
        self.result_proba = Results()
        self.odds = Odds(self.match_id)