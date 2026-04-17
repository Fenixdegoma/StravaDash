import os
import requests
import json
import re

def extract_code(input_text: str):
    """
    Extracts Strava auth code from either:
    - full redirect URL
    - pasted query string
    - raw code
    """

    input_text = input_text.strip()

    # Case 1: raw code (no URL structure)
    if "http" not in input_text and "code=" not in input_text:
        return input_text

    # Case 2: URL or query string
    match = re.search(r"code=([^&\s]+)", input_text)
    if match:
        return match.group(1)

    return None


def exchange_token(client_id, client_secret, code):
    res = requests.post(
        "https://www.strava.com/oauth/token",
        data={
            "client_id": client_id,
            "client_secret": client_secret,
            "code": code,
            "grant_type": "authorization_code"
        }
    )
    return res.json()


def main():
    print("\n=== STRAVA AUTH SETUP ===\n")

    client_id = input("Enter your Strava CLIENT ID: ").strip()
    client_secret = input("Enter your Strava CLIENT SECRET: ").strip()

    auth_url = (
        "https://www.strava.com/oauth/authorize"
        f"?client_id={client_id}"
        "&response_type=code"
        "&redirect_uri=http://localhost"
        "&approval_prompt=force"
        "&scope=activity:read_all"
    )

    print("\n=== STEP 1: AUTHORISE ===\n")
    print("Open this URL in your browser:\n")
    print(auth_url)
    print("\nAfter authorising, you will be redirected to a URL.")
    print("Copy and paste the FULL URL here (recommended), OR just the code.\n")

    # retry loop (one correction attempt only)
    for attempt in range(2):
        raw_input = input("Paste redirect URL or code: ").strip()
        code = extract_code(raw_input)

        if not code:
            print("\n❌ Could not find an auth code.")
            print("Make sure you copied the full redirect URL.\n")
            continue

        print("\nExchanging code for tokens...\n")

        data = exchange_token(client_id, client_secret, code)

        if "refresh_token" in data:
            refresh_token = data["refresh_token"]
            break

        print("❌ Token exchange failed.")
        print(data)

        if attempt == 0:
            print("\nTry again — paste the FULL redirect URL this time.\n")
        else:
            print("\nGiving up after 2 attempts.")
            return

    # Save credentials
    out = {
        "client_id": client_id,
        "client_secret": client_secret,
        "refresh_token": refresh_token
    }

    with open("strava_auth.txt", "w") as f:
        json.dump(out, f, indent=2)

    # Windows env vars
    if os.name == "nt":
        os.system(f'setx STRAVA_CLIENT_ID "{client_id}"')
        os.system(f'setx STRAVA_CLIENT_SECRET "{client_secret}"')
        os.system(f'setx STRAVA_REFRESH_TOKEN "{refresh_token}"')

    print("\n=== COMPLETE ===")
    print("Saved to: strava_auth.txt")

    print("\nIMPORTANT:")
    print("- Close ALL terminal sessions")
    print("- Reopen terminal before running dashboard\n")

    input("Press ENTER to exit...")
    os._exit(0)


if __name__ == "__main__":
    main()