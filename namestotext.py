import requests
import json

def get_access_token(client_id, client_secret):
    auth_response = requests.post(
        'https://eu.battle.net/oauth/token',
        data={'grant_type': 'client_credentials'},
        auth=(client_id, client_secret)
    )
    auth_response_data = auth_response.json()
    return auth_response_data['access_token']

def get_guild_roster(realm, guild_name, access_token):
    guild_roster_url = f'https://eu.api.blizzard.com/data/wow/guild/{realm}/{guild_name}/roster'
    params = {
        'namespace': 'profile-eu',  # EU namespace
        'locale': 'en_GB',          # English (Great Britain) locale
        'access_token': access_token
    }
    response = requests.get(guild_roster_url, params=params)
    return response.json()

def save_characters_to_file(realm, characters, file_name='guild_members.txt'):
    with open(file_name, 'w', encoding='utf-8') as file:  # Use UTF-8 encoding
        for character in characters:
            file.write(f"{realm}, {character['character']['name']}\n")
    print(f"Character names have been written to {file_name}")

def main():
    client_id = 'id'
    client_secret = 'scr'
    realm = input("Enter the realm name: ")
    guild_name = input("Enter the guild name: ")

    access_token = get_access_token(client_id, client_secret)
    roster_data = get_guild_roster(realm, guild_name, access_token)

    # Debugging: Print the entire response if 'members' key is missing
    if 'members' not in roster_data:
        print("Unexpected API response:")
        print(json.dumps(roster_data, indent=2))
        return

    characters = roster_data['members']
    save_characters_to_file(realm, characters)

if __name__ == "__main__":
    main()
