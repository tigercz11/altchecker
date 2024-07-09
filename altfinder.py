import requests
import json
import sqlite3
import os
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import quote
from time import sleep, time
import hashlib
import base64

# Blizzard API credentials
CLIENT_ID = 'id'
CLIENT_SECRET = 'scr'


# Function to get access token for Blizzard API
def get_access_token():
    url = 'https://us.battle.net/oauth/token'
    data = {
        'grant_type': 'client_credentials',
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET,
    }
    response = requests.post(url, data=data)
    if response.status_code == 200:
        return response.json()['access_token']
    else:
        print(f"Failed to get access token: {response.status_code}, {response.text}")
        return None


# Function to fetch pet data for a character with retries on timeout
def fetch_pet_data(region, realm, character_name, access_token, timeout=5, retries=3):
    character_name_encoded = quote(character_name)
    base_url = f'https://{region}.api.blizzard.com/profile/wow/character/{realm}/{character_name_encoded}/collections/pets'
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Battlenet-Namespace': 'profile-eu',
    }

    for attempt in range(retries):
        try:
            response = requests.get(base_url, headers=headers, timeout=timeout)
            response.raise_for_status()
            full_data = response.json()
            pet_data = full_data.get("pets", [])
            pet_data_json = json.dumps(pet_data)
            pets_data_bytes = pet_data_json.encode('utf-8')
            sha256_hash = hashlib.sha256()
            sha256_hash.update(pets_data_bytes)
            petsback = sha256_hash.digest()
            pets_data = base64.b64encode(petsback).decode('utf-8')
            return character_name, realm, pets_data
        except requests.exceptions.HTTPError as http_err:
            if response.status_code == 404:
                print(f"Character {character_name} not found on realm {realm}.")
            else:
                print(f"HTTP error occurred: {http_err}")
            return character_name, realm, None
        except requests.exceptions.RequestException as err:
            print(f"Attempt {attempt + 1} - Request error occurred: {err}")
            if attempt < retries - 1:
                sleep(1)  # Wait for a moment before retrying
                continue
            else:
                return character_name, realm, None


# Function to initialize database
def initialize_database():
    if os.path.exists('blizzard_accounts.db'):
        os.remove('blizzard_accounts.db')
    conn = sqlite3.connect('blizzard_accounts.db')
    c = conn.cursor()

    # Create table for storing character pet data
    c.execute('''CREATE TABLE IF NOT EXISTS characters (
                 id INTEGER PRIMARY KEY,
                 account_id INTEGER,
                 character_name TEXT,
                 realm TEXT,
                 pet_data TEXT,
                 UNIQUE(character_name, realm)
                 )''')

    conn.commit()
    conn.close()


# Function to insert or update character data into database
def insert_or_update_character_data(account_id, character_name, realm, pet_data):
    conn = sqlite3.connect('blizzard_accounts.db')
    c = conn.cursor()

    # Check if character already exists
    c.execute('''SELECT id FROM characters WHERE character_name = ? AND realm = ?''', (character_name, realm))
    existing_character = c.fetchone()

    if existing_character:
        # Update existing character data
        c.execute('''UPDATE characters
                     SET account_id = ?, pet_data = ?
                     WHERE id = ?''', (account_id, json.dumps(pet_data), existing_character[0]))
    else:
        # Insert new character data
        c.execute('''INSERT INTO characters (account_id, character_name, realm, pet_data)
                     VALUES (?, ?, ?, ?)''', (account_id, character_name, realm, json.dumps(pet_data)))

    conn.commit()
    conn.close()


# Function to remove pet data after insertion
def remove_pet_data():
    conn = sqlite3.connect('blizzard_accounts.db')
    c = conn.cursor()

    # Update characters table to remove pet data
    c.execute('''UPDATE characters SET pet_data = NULL''')

    conn.commit()
    conn.close()


# Function to display accounts
def display_accounts():
    conn = sqlite3.connect('blizzard_accounts.db')
    c = conn.cursor()

    c.execute('''SELECT account_id, GROUP_CONCAT(character_name || ' (' || realm || ')', ', ') FROM characters
                 GROUP BY account_id''')

    accounts = c.fetchall()

    for idx, account in enumerate(accounts, 1):
        print(f"Account {idx}: ({account[1]})")

    conn.close()


# Function to check if pet data already exists in the database and return account_id
def check_existing_pet_data(pet_data):
    conn = sqlite3.connect('blizzard_accounts.db')
    c = conn.cursor()

    c.execute('''SELECT account_id, pet_data FROM characters''')
    existing_data = c.fetchall()

    for account_id, stored_pet_data in existing_data:
        if json.loads(stored_pet_data) == pet_data:
            conn.close()
            return account_id

    conn.close()
    return None


# Function to fetch next available account ID
def fetch_next_account_id():
    conn = sqlite3.connect('blizzard_accounts.db')
    c = conn.cursor()

    c.execute('''SELECT MAX(account_id) FROM characters''')
    max_account_id = c.fetchone()[0]

    conn.close()

    if max_account_id is None:
        return 1
    else:
        return max_account_id + 1


# Function to read character data from file
def read_character_data_from_file(file_path):
    characters = []
    with open(file_path, 'r', encoding='utf-8') as file:
        for line in file:
            line = line.strip()
            if line:
                try:
                    realm, character_name = map(str.strip, line.split(','))
                    characters.append((realm.replace(' ', '-').lower(), character_name.lower()))
                except ValueError:
                    print(f"Skipping malformed line: {line}")
    return characters


def main():
    initialize_database()

    # Read character data from names.txt
    file_path = 'names.txt'
    characters = read_character_data_from_file(file_path)
    region = 'eu'  # Assuming EU region based on your initial request

    access_token = get_access_token()
    if not access_token:
        return

    fetched_data = []

    # Use ThreadPoolExecutor to fetch pet data concurrently
    rate_limit_per_second = 70
    request_interval = 1 / rate_limit_per_second
    last_request_time = time()

    with ThreadPoolExecutor(max_workers=50) as executor:
        future_to_character = {}
        for realm, character_name in characters:
            current_time = time()
            time_since_last_request = current_time - last_request_time
            if time_since_last_request < request_interval:
                sleep(request_interval - time_since_last_request)
            last_request_time = time()

            future = executor.submit(fetch_pet_data, region, realm, character_name, access_token, timeout=5)
            future_to_character[future] = (realm, character_name)

        for future in future_to_character:
            character_name, realm, pet_data = future.result()
            if pet_data:
                fetched_data.append((character_name, realm, pet_data))

    # Process the fetched data
    for character_name, realm, pet_data in fetched_data:
        # Check if pet data already exists in the database
        existing_account_id = check_existing_pet_data(pet_data)
        if existing_account_id:
            print(f"Character {character_name} matches an existing account.")
            account_id = existing_account_id
        else:
            # Create a new account
            account_id = fetch_next_account_id()
            print(f"Creating a new account for character {character_name}.")

        # Insert or update character data into the database
        insert_or_update_character_data(account_id, character_name, realm, pet_data)

    # Remove pet data from all characters
    remove_pet_data()

    # Display accounts
    display_accounts()


if __name__ == '__main__':
    main()
