import base64
from os import getcwd
from random import randint
from time import sleep

import requests
from requests import Response
from datetime import datetime, timedelta
from pytz import timezone

rooms = [
    'Eltern-Kind-Raum.1 (Geb. 30.50, 3. OG  Tisch 1 Kapazität 6 Personen)',
    'Eltern-Kind-Raum.2 (Geb. 30.50, 3. OG  Tisch 1 Kapazität 6 Personen)',
    'Raum 11 (Geb. 30.50, 1. OG Kapazität 06 Personen)',
    'Raum 12 (Geb. 30.50, 1. OG Kapazität 06 Personen)',
    'Raum 13 (Geb. 30.50, 1. OG Kapazität 12 Personen)',
    'Raum 14 (Geb. 30.50, 1. OG Kapazität 12 Personen)',
    'Raum 16 (Geb. 30.50, 1. OG Kapazität 12 Personen)',
    'Raum 17 (Geb. 30.50, 1. OG Kapazität 06 Personen)',
    'Raum 18 (Geb. 30.50, 1. OG Kapazität 06 Personen)',
    'Raum 31.1 (Geb. 30.50, 3. OG  Tisch 1 Kapazität 6 Personen)',
    'Raum 31.2 (Geb. 30.50, 3. OG  Tisch 1 Kapazität 6 Personen)',
]

human_room_names = [
    'Eltern-Kind-Raum.1 (6)',
    'Eltern-Kind-Raum.2 (6)',
    'Raum 11 (6)',
    'Raum 12 (6)',
    'Raum 13 (12)',
    'Raum 14 (12)',
    'Raum 16 (12)',
    'Raum 17 (6)',
    'Raum 18 (6)',
    'Raum 31.1 (6)',
    'Raum 31.2 (6)',
]

url = base64.b64decode(
    "aHR0cHM6Ly9iLmFubnkuZXUvYXBpL3YxL3Jlc291cmNlcy9ncnVwcGVucmF1bWUta2l0LWJpYmxpb3RoZWstc3VkL2NoaWxkcmVu")
headers = {
    "User-Agent": "i_only_do_this_so_i_have_a_per_day_table_view_of_all_group_rooms_bitcheeeesss"
}
output_dir = "/var/www/html/tabloid"

default_params = {
    'page[number]': 1,
    'page[size]': 15,
    'filter[include_unavailable]': 0,
    'filter[exclude_hidden]': 0,
    'filter[exclude_child_resources]': 0,
    'filter[availability_exact_match]': 1,
    'sort': 'name',
    'fields[resources]': 'name'
}
booking_day_count = 14


def create_time_range(date: datetime, hour: int, minutes: int) -> tuple:
    start = date.replace(hour=hour, minute=0) + timedelta(minutes=minutes)
    end = date.replace(hour=hour, minute=0) + timedelta(minutes=minutes + 30)
    return start, end


def time_ranges_single_day(day: datetime) -> list[tuple[datetime]]:
    times = []
    for hour in range(day.hour, 24):
        times.append(create_time_range(day, hour, 0))
        times.append(create_time_range(day, hour, 30))
    return times


def request_single_range(start: datetime, end: datetime) -> Response:
    time_params = {
        'filter[available_from]': start.isoformat(),
        'filter[available_to]': end.isoformat(),
    }
    print(f"Requesting {start.isoformat()}")
    return requests.get(url, params=default_params | time_params)


def get_room_name(entry) -> str:
    return entry["attributes"]["name"]


def get_available_rooms_idx(data) -> list[int]:
    return list(map(lambda entry: rooms.index(get_room_name(entry)), data))


def empty_table(day: datetime) -> dict:
    table = {}
    midnight = day.replace(hour=0, minute=0)

    while True:
        table[midnight.strftime("%H:%M")] = None
        midnight = midnight + timedelta(minutes=30)
        if midnight.day != day.day:
            break
    return table


def request_all() -> dict:
    tables = {}
    for day_count in range(booking_day_count + 1):
        day = now.replace(hour=0, minute=0) + timedelta(days=day_count)
        tables[day.date().isoformat()] = empty_table(day)
        time_ranges = time_ranges_single_day(day)
        for time_range in time_ranges:
            if time_range[0] < now:
                continue
            resp = request_single_range(*time_range)
            sleep(randint(5, 10) / 10)
            if resp.status_code != 200:
                print("error")
            available_rooms = get_available_rooms_idx(resp.json()["data"])
            tables[day.date().isoformat()][time_range[0].strftime("%H:%M")] = available_rooms
    return tables


def day_to_tr(time: str, bookings: list) -> str:
    tds = []
    for idx in range(0, len(rooms)):
        if bookings is None:
            tds.append('<td><div style="background: grey"/></td>')
        elif idx not in bookings:
            tds.append('<td><div style="background: red"/></td>')
        else:
            tds.append('<td><div style="background: green"/></td>')
    return ('<tr>'
            + f"<td>{time}</td>"
            + "".join(tds)
            + '</tr>')


def day_to_tbody(table: dict) -> str:
    tds_list = []
    for hour in table.keys():
        tds_list.append(day_to_tr(hour, table[hour]))
    return "".join(tds_list)


def html_doc(day: str, thead: str, tbody: str) -> str:
    datetimeday = datetime.strptime(day, '%Y-%m-%d').date()
    before = (datetimeday - timedelta(days=1)).isoformat()
    after = (datetimeday + timedelta(days=1)).isoformat()
    return ('<!DOCTYPE html>'
            '<html lang="en">'
            '<head><meta charset="utf-8">'
            f'<title>tabloid {day} ({now.isoformat()})</title>'
            '<style>div {width: 100px;height: 18px; }</style></head><body>'
            f'<a href="{before}.html">{before}</a> {datetimeday.isoformat()} '
            f'<a href="{after}.html">{after}</a>'
            f'<table> <thead>{thead}</thead>'
            f'<tbody>{tbody}</tbody></table></body></html>')


def do_it() -> dict:
    global now
    now = datetime.now(timezone("Europe/Berlin")).replace(microsecond=0, second=0)
    thead = ""
    for room in human_room_names:
        thead += f"<th>{room}</th>"
    thead = f"<tr><th></th>{thead}</tr>"
    tables = request_all()
    html = {}
    for single_day in tables.keys():
        html[single_day] = html_doc(single_day, thead, day_to_tbody(tables[single_day]))
    return html


if __name__ == "__main__":
    print(f"URL: {url}")
    pages = do_it()
    for day_page in pages.keys():
        file_name = day_page + ".html"
        with open(f"{output_dir}/{file_name}", "w+") as file:
            print(f"Writing {file_name} to {output_dir}")
            file.write(pages[day_page])
