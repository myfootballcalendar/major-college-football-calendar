import os
import requests
from datetime import datetime, timedelta, timezone
from icalendar import Calendar, Event


# ============================================================
# SETTINGS
# ============================================================

YEAR = 2026

API_URL = "https://api.collegefootballdata.com"

OUTPUT_FILE = "major-college-football-2026.ics"

MAJOR_CONFERENCES = {
    "SEC",
    "Big Ten",
    "Big 12",
    "ACC",
}

EXTRA_MAJOR_TEAMS = {
    "Notre Dame",
}


# ============================================================
# API KEY
# ============================================================

API_KEY = os.environ.get("CFBD_API_KEY")

if not API_KEY:

    print("ERROR: CFBD_API_KEY is not set.")
    print()
    print("Run:")
    print("set CFBD_API_KEY=YOUR_API_KEY")

    raise SystemExit(1)


HEADERS = {
    "Authorization": f"Bearer {API_KEY}"
}


def get_api(endpoint, params=None):

    response = requests.get(
        API_URL + endpoint,
        headers=HEADERS,
        params=params,
        timeout=60
    )

    response.raise_for_status()

    return response.json()


# ============================================================
# GET MAJOR TEAMS
# ============================================================

print()
print("Getting major-college teams...")

teams = get_api("/teams")

major_teams = set()

for team in teams:

    school = team.get("school")
    conference = team.get("conference")

    if not school:
        continue

    if conference in MAJOR_CONFERENCES:
        major_teams.add(school)

    if school in EXTRA_MAJOR_TEAMS:
        major_teams.add(school)


print(
    f"Major teams found: {len(major_teams)}"
)


# ============================================================
# GET REGULAR SEASON
# ============================================================

print()
print("Downloading regular-season games...")

regular_games = get_api(
    "/games",
    {
        "year": YEAR,
        "seasonType": "regular"
    }
)

print(
    f"Regular-season games: {len(regular_games)}"
)


# ============================================================
# GET POSTSEASON
# ============================================================

print()
print("Downloading postseason games...")

postseason_games = get_api(
    "/games",
    {
        "year": YEAR,
        "seasonType": "postseason"
    }
)

print(
    f"Postseason games: {len(postseason_games)}"
)


# ============================================================
# COMBINE
# ============================================================

all_games = (
    regular_games
    + postseason_games
)


# ============================================================
# FILTER + DEDUPLICATE
# ============================================================

selected_games = []

seen_ids = set()

for game in all_games:

    game_id = game.get("id")

    if not game_id:
        continue

    if game_id in seen_ids:
        continue

    home_team = game.get(
        "homeTeam"
    )

    away_team = game.get(
        "awayTeam"
    )

    if not home_team or not away_team:
        continue

    # Include game if either team is major.
    if (
        home_team in major_teams
        or
        away_team in major_teams
    ):

        seen_ids.add(game_id)

        selected_games.append(game)


print()
print(
    f"Major-college games selected: "
    f"{len(selected_games)}"
)


# ============================================================
# CREATE CALENDAR
# ============================================================

calendar = Calendar()

calendar.add(
    "prodid",
    "-//Major College Football Calendar//EN"
)

calendar.add(
    "version",
    "2.0"
)

calendar.add(
    "X-WR-CALNAME",
    "Major College Football 2026"
)

calendar.add(
    "X-WR-CALDESC",
    "Major college football games - 2026"
)


# ============================================================
# ADD EVENTS
# ============================================================

events_added = 0

for game in selected_games:

    game_id = game.get("id")

    home_team = game.get(
        "homeTeam",
        "TBD"
    )

    away_team = game.get(
        "awayTeam",
        "TBD"
    )

    start_date = game.get(
        "startDate"
    )

    if not start_date:
        continue


    try:

        start = datetime.fromisoformat(
            start_date.replace(
                "Z",
                "+00:00"
            )
        )

    except ValueError:

        print(
            "Could not read date:",
            start_date
        )

        continue


    end = start + timedelta(
        hours=4
    )


    event = Event()


    # IMPORTANT:
    # Stable UID prevents Google Calendar
    # from treating updated games as new events.

    event.add(
        "uid",
        f"cfbd-{YEAR}-{game_id}@major-college-football"
    )

    event.add(
        "dtstamp",
        datetime.now(timezone.utc)
    )

    event.add(
        "dtstart",
        start
    )

    event.add(
        "dtend",
        end
    )

    event.add(
        "summary",
        f"{away_team} at {home_team}"
    )


    # --------------------------------------------------------
    # DESCRIPTION
    # --------------------------------------------------------

    description = []

    description.append(
        "Major College Football"
    )

    description.append("")

    description.append(
        f"Away: {away_team}"
    )

    description.append(
        f"Home: {home_team}"
    )


    home_conf = game.get(
        "homeConference"
    )

    away_conf = game.get(
        "awayConference"
    )

    if away_conf:

        description.append(
            f"Away conference: {away_conf}"
        )

    if home_conf:

        description.append(
            f"Home conference: {home_conf}"
        )


    # TV/media information.

    media = game.get(
        "mediaType"
    )

    if media:

        description.append(
            f"TV/Media: {media}"
        )


    # Venue.

    venue = game.get(
        "venue"
    )

    if venue:

        description.append(
            f"Venue: {venue}"
        )


    description.append("")

    description.append(
        f"CFBD Game ID: {game_id}"
    )


    event.add(
        "description",
        "\n".join(description)
    )


    calendar.add_component(
        event
    )

    events_added += 1


# ============================================================
# SAVE
# ============================================================

with open(
    OUTPUT_FILE,
    "wb"
) as file:

    file.write(
        calendar.to_ical()
    )


# ============================================================
# RESULTS
# ============================================================

print()
print("==============================================")
print("CALENDAR CREATED")
print("==============================================")
print()

print(
    f"Major teams: {len(major_teams)}"
)

print(
    f"Regular games downloaded: "
    f"{len(regular_games)}"
)

print(
    f"Postseason games downloaded: "
    f"{len(postseason_games)}"
)

print(
    f"Major games selected: "
    f"{len(selected_games)}"
)

print(
    f"Calendar events: "
    f"{events_added}"
)

print()
print(
    f"File: {OUTPUT_FILE}"
)
print()
