"""
The constants used in this project

© Anime no Sekai - 2021
"""


from pyuseragents import random

HEADERS = {"User-Agent": random()}

# found on a free proxy list
PROXY = {
    "http": "http://157.230.6.23:8080",
    "https": "http://157.230.6.23:8080"
}
