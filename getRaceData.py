import requests


def get_race_data():
    # 1) Get the checksum from ebayi.tjk.org
    checksum_url = "https://ebayi.tjk.org/s/d/bet/checksum.json"
    # Typical headers from your DevTools (minimally, you often only need a User-Agent).
    # Adjust or remove if not strictly needed.
    headers_for_checksum = {
        "Accept": "application/json, text/javascript, */*; q=0.01",
        "Accept-Encoding": "gzip, deflate, br, zstd",
        "Accept-Language": "tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7",
        "Cache-Control": "no-cache",
        "Pragma": "no-cache",
        "Referer": "https://ebayi.tjk.org/",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
        "X-Requested-With": "XMLHttpRequest",
    }

    # If cookies are required, you can supply them in headers or use a session
    # "Cookie": "...",

    # GET the first JSON
    response_checksum = requests.get(checksum_url, headers=headers_for_checksum)
    if response_checksum.status_code != 200:
        print(f"Checksum request failed. Status code: {response_checksum.status_code}")
        return

    # Parse the JSON
    try:
        checksum_data = response_checksum.json()
    except ValueError:
        print("Could not parse checksum JSON.")
        print("Raw response:", response_checksum.text)
        return

    # 2) Extract the actual checksum value
    #    (The key name below is just an EXAMPLE. Use the correct key from the JSON.)
    #    For instance, if the JSON looks like {"checksum":"1d96719d"}, we do:
    actual_checksum_value = checksum_data.get("checksum")  # Adjust key name as needed

    if not actual_checksum_value:
        print("Could not find checksum value in response.")
        print("Response JSON:", checksum_data)
        return

    # 3) Build the URL for the second request
    #    From your example: /s/d/bet/bet-1d96719d.json
    #    Replace 1d96719d with the actual checksum value.
    second_url = f"https://emedya-cdn.tjk.org/s/d/bet/bet-{actual_checksum_value}.json"

    # 4) Make the second request
    #    Here we replicate the headers from DevTools for the second request.
    headers_for_race_data = {
        # Remove lines like ":authority", ":method", ":scheme", ":path"

        "Accept": "application/json, text/javascript, */*; q=0.01",
        "Accept-Encoding": "gzip, deflate, br, zstd",
        "Accept-Language": "tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7",
        "Cache-Control": "no-cache",
        "Origin": "https://ebayi.tjk.org",
        "Pragma": "no-cache",
        "Referer": "https://ebayi.tjk.org/",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-site",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
        # "Cookie": "..."  # if needed
        # "X-Requested-With": "XMLHttpRequest"  # if needed
    }

    response_race = requests.get(second_url, headers=headers_for_race_data)
    if response_race.status_code != 200:
        print(f"Second request failed. Status code: {response_race.status_code}")
        print("Response text:", response_race.text)
        return

    # Parse the race data JSON
    try:
        race_data = response_race.json()
        return race_data  # Now we have the race data as a Python dict
    except ValueError:
        print("Could not parse race data JSON.")
        print("Raw response:", response_race.text)
        return


if __name__ == "__main__":
    data = get_race_data()
    if data:
        print("Race data successfully retrieved:")
        print(data)
