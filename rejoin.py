"""
Roblox Auto Rejoin Bot for Android
A tool to automatically rejoin Roblox games on Android devices
"""

import os
import requests
import json
import time
import asyncio
import aiohttp
from colorama import init, Fore, Style
import subprocess

# Initialize colorama for colored terminal output
init()

# Constants
MAX_PACKAGES_TO_CHECK = 4
SERVER_LINKS_FILE = 'server_links.txt'
ACCOUNTS_FILE = 'accounts.txt'

# Builtin shortcuts for easier refactoring
__name__ = __name__
int = int
input = input
len = len
Exception = Exception
bool = bool
open = open
print = print


def clear_screen():
    """Clear the console screen and display the banner"""
    os.system('clear')
    banner = "\n  _____ _             _   _               ____       _       _       \n |  ___| | ___   __ _| |_(_)_ __   __ _  |  _ \\ ___ (_) ___ (_)_ __  \n | |_  | |/ _ \\ / _` | __| | '_ \\ / _` | | |_) / _ \\| |/ _ \\| | '_ \\ \n |  _| | | (_) | (_| | |_| | | | | (_| | |  _ <  __/| | (_) | | | | |\n |_|   |_|\\___/ \\__,_|\\__|_|_| |_|\\__, | |_| \\_\\___|/ |\\___/|_|_| |_|\n                                  |___/           |__/               \n"
    print(Fore.BLUE + banner + Style.RESET_ALL)
    print(Fore.CYAN + 'Made by not.shiroo' + Style.RESET_ALL)


def detect_roblox_packages():
    """Detect installed Roblox packages on Android device"""
    detected_packages = []
    for variant in ['u', 'v', 'w', 'x']:
        package_name = f'com.roblox.clien{variant}'
        print(f'Checking for package: {package_name}')
        return_code = os.system(f"pm list packages | grep '{package_name}'")
        if return_code == 0:
            print(f'Found package: {package_name}')
            detected_packages.append(package_name)
        if len(detected_packages) >= MAX_PACKAGES_TO_CHECK:
            break
    return detected_packages


def is_process_running(package_name):
    """Check if a process is running by package name"""
    result = subprocess.run(f'pidof {package_name}', shell=True, stdout=subprocess.PIPE)
    return bool(result.stdout.strip())


def kill_all_roblox_processes():
    """Kill all Roblox processes on the device"""
    print('Killing all Roblox processes...')
    packages = detect_roblox_packages()
    for package_name in packages:
        os.system(f"su -c 'killall -9 {package_name}'")
    time.sleep(2)


def kill_roblox_process(package_name):
    """Kill a specific Roblox process"""
    print(f'Killing Roblox process for {package_name}...')
    os.system(f"su -c 'killall -9 {package_name}'")
    time.sleep(2)


def launch_game(package_name, game_link, num_packages):
    """Launch a Roblox game on Android device"""
    try:
        print(Fore.GREEN + 'Starting Game...' + Style.RESET_ALL)
        os.system(f'am start -n {package_name}/com.roblox.client.startup.ActivitySplash -d "{game_link}" > /dev/null 2>&1')
        time.sleep(15 if num_packages >= 6 else 5)
        print(Fore.GREEN + 'Joining Game...' + Style.RESET_ALL)
        os.system(f'am start -n {package_name}/com.roblox.client.ActivityProtocolLaunch -d "{game_link}" > /dev/null 2>&1')
        time.sleep(20)
    except Exception as error:
        print(Fore.RED + f'Error launching Roblox for {package_name}: {error}')


def format_game_link(user_input):
    """Convert user input to proper Roblox game link format"""
    if 'roblox.com' in user_input:
        return user_input
    elif user_input.isdigit():
        return f'roblox://placeID={user_input}'
    else:
        print(Fore.RED + 'Invalid input! Please enter a valid game ID or private server link.' + Style.RESET_ALL)
        return None


def save_server_links(server_links):
    """Save server links to file"""
    with open(SERVER_LINKS_FILE, 'w') as file:
        for (package_name, game_link) in server_links:
            file.write(f'{package_name},{game_link}\n')


def load_server_links():
    """Load server links from file"""
    server_links = []
    if os.path.exists(SERVER_LINKS_FILE):
        with open(SERVER_LINKS_FILE, 'r') as file:
            for line in file:
                (package_name, game_link) = line.strip().split(',', 1)
                server_links.append((package_name, game_link))
    return server_links


def save_accounts(accounts):
    """Save account IDs to file"""
    with open(ACCOUNTS_FILE, 'w') as file:
        for (package_name, user_id) in accounts:
            file.write(f'{package_name},{user_id}\n')


def load_accounts():
    """Load account IDs from file"""
    accounts = []
    if os.path.exists(ACCOUNTS_FILE):
        with open(ACCOUNTS_FILE, 'r') as file:
            for line in file:
                (package_name, user_id) = line.strip().split(',', 1)
                accounts.append((package_name, user_id))
    return accounts


async def get_user_id_from_username(username):
    """Fetch user ID from Roblox API using username"""
    url = 'https://users.roblox.com/v1/usernames/users'
    payload = {'usernames': [username], 'excludeBannedUsers': True}
    headers = {'Content-Type': 'application/json'}
    async with aiohttp.ClientSession() as session:
        async with session.post(url, json=payload, headers=headers) as response:
            data = await response.json()
            if 'data' in data and len(data['data']) > 0:
                return data['data'][0]['id']
    return None


def get_username_from_id(user_id):
    """Fetch username from Roblox API using user ID"""
    try:
        url = f'https://users.roblox.com/v1/users/{user_id}'
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        return data.get('name', 'Unknown')
    except Exception as error:
        print(Fore.RED + f'Error getting username for user ID {user_id}: {error}')
        return None


def check_user_presence(user_id):
    """Check if a user is currently in-game or offline"""
    try:
        url = 'https://presence.roblox.com/v1/presence/users'
        headers = {'Content-Type': 'application/json'}
        payload = json.dumps({'userIds': [user_id]})
        with requests.Session() as session:
            response = session.post(url, headers=headers, data=payload, timeout=7)
        response.raise_for_status()
        data = response.json()
        presence_type = data['userPresences'][0]['userPresenceType']
        last_location = data['userPresences'][0].get('lastLocation', None)
        
        if last_location == 'Website':
            print(Fore.YELLOW + f'{user_id} is currently on the Website. Rejoin recommended.' + Style.RESET_ALL)
            presence_type = 0
        
        return (presence_type, last_location)
    except Exception as error:
        print(Fore.RED + f'Error checking online status for user {user_id}: {error}' + Style.RESET_ALL)
        return (None, None)


def main_menu():
    """Main menu and control flow"""
    clear_screen()
    input(Fore.GREEN + 'Press Enter to continue...' + Style.RESET_ALL)
    
    while True:
        choice = input(Fore.GREEN + 'Choose setup:\n1. Start Auto Rejoin\n2. Set User IDs for Each Package\n3. Same Game ID or Private Server Link\n4. Clear userid/gamelink\nEnter choice: ' + Style.RESET_ALL)
        
        if choice == '1':
            # Start Auto Rejoin
            server_links = load_server_links()
            accounts = load_accounts()
            
            if not accounts:
                print(Fore.RED + 'No user IDs set up yet! Please set them up before proceeding.' + Style.RESET_ALL)
                continue
            elif not server_links:
                print(Fore.RED + 'No game ID or private server link set up yet! Please set them up before proceeding.' + Style.RESET_ALL)
                continue
            
            rejoin_interval = int(input('Enter the force rejoin/kill Roblox interval in minutes: ')) * 60
            print('Killing Roblox processes...')
            kill_all_roblox_processes()
            print(Fore.YELLOW + 'Waiting for 5 seconds before starting the rejoin process...' + Style.RESET_ALL)
            time.sleep(5)
            
            num_packages = len(server_links)
            for (package_name, game_link) in server_links:
                launch_game(package_name, game_link, num_packages)
            
            last_reset_time = time.time()
            while True:
                current_time = time.time()
                
                for (package_name, user_id) in accounts:
                    # Convert username to ID if needed
                    if not user_id.isdigit():
                        print(f'Retrieving user ID for username: {user_id}...')
                        user_id = asyncio.run(get_user_id_from_username(user_id))
                        if user_id is None:
                            print(Fore.RED + 'Failed to retrieve user ID. Please enter the user ID manually.' + Style.RESET_ALL)
                            user_id = input('Enter the user ID: ')
                    
                    username = get_username_from_id(user_id) or user_id
                    (presence_type, last_location) = check_user_presence(user_id)
                    
                    if presence_type == 2:
                        print(Fore.GREEN + f'{username} ({user_id}) is currently in-game.' + Style.RESET_ALL)
                    elif not is_process_running(package_name):
                        print(Fore.RED + f'{package_name} process has crashed. Relaunching...' + Style.RESET_ALL)
                        kill_roblox_process(package_name)
                        time.sleep(2)
                        launch_game(package_name, game_link, num_packages)
                    elif last_location == 'Website':
                        print(Fore.RED + f'{username} ({user_id}) is on the website or has been inactive. Rejoining...' + Style.RESET_ALL)
                        kill_roblox_process(package_name)
                        time.sleep(2)
                        launch_game(package_name, game_link, num_packages)
                    else:
                        print(Fore.YELLOW + f'{username} ({user_id}) is not in-game but was recently active.' + Style.RESET_ALL)
                    
                    time.sleep(5)
                
                time.sleep(120)
                
                # Force rejoin/kill based on interval
                if current_time - last_reset_time >= rejoin_interval:
                    print('Force killing Roblox processes due to time limit.')
                    kill_all_roblox_processes()
                    last_reset_time = current_time
                    print(Fore.YELLOW + 'Waiting for 5 seconds before starting the rejoin process...' + Style.RESET_ALL)
                    time.sleep(5)
                    for (package_name, game_link) in server_links:
                        launch_game(package_name, game_link, num_packages)
        
        elif choice == '2':
            # Set User IDs for Each Package
            accounts = []
            packages = detect_roblox_packages()
            for package_name in packages:
                user_input = input(f'Enter the user ID or username for {package_name}: ')
                user_id = None
                
                if user_input.isdigit():
                    user_id = user_input
                else:
                    print(f'Retrieving user ID for username: {user_input}...')
                    user_id = asyncio.run(get_user_id_from_username(user_input))
                    if user_id is None:
                        print(Fore.RED + 'Failed to retrieve user ID. Please enter the user ID manually.' + Style.RESET_ALL)
                        user_id = input('Enter the user ID: ')
                
                accounts.append((package_name, user_id))
                print(f'Set {package_name} to user ID: {user_id}')
            
            save_accounts(accounts)
            print(Fore.GREEN + 'User IDs saved!' + Style.RESET_ALL)
        
        elif choice == '3':
            # Same Game ID or Private Server Link
            game_link_input = input('Enter the game ID or private server link: ')
            formatted_link = format_game_link(game_link_input)
            
            if formatted_link:
                packages = detect_roblox_packages()
                server_links = [(package_name, formatted_link) for package_name in packages]
                save_server_links(server_links)
                print(Fore.GREEN + 'Game ID or private server link saved successfully!' + Style.RESET_ALL)
        
        elif choice == '4':
            # Clear userid/gamelink
            clear_choice = input(Fore.GREEN + 'What do you want to clear?\n1. Clear User IDs\n2. Clear Server Links\n3. Clear Both\nEnter choice: ' + Style.RESET_ALL)
            
            if clear_choice == '1':
                if os.path.exists(ACCOUNTS_FILE):
                    os.remove(ACCOUNTS_FILE)
                    print(Fore.GREEN + 'User IDs cleared successfully!' + Style.RESET_ALL)
                else:
                    print(Fore.YELLOW + f"No such file: '{ACCOUNTS_FILE}' found to clear." + Style.RESET_ALL)
            
            elif clear_choice == '2':
                if os.path.exists(SERVER_LINKS_FILE):
                    os.remove(SERVER_LINKS_FILE)
                    print(Fore.GREEN + 'Server links cleared successfully!' + Style.RESET_ALL)
                else:
                    print(Fore.YELLOW + f"No such file: '{SERVER_LINKS_FILE}' found to clear." + Style.RESET_ALL)
            
            elif clear_choice == '3':
                if os.path.exists(ACCOUNTS_FILE):
                    os.remove(ACCOUNTS_FILE)
                    print(Fore.GREEN + 'User IDs cleared successfully!' + Style.RESET_ALL)
                else:
                    print(Fore.YELLOW + f"No such file: '{ACCOUNTS_FILE}' found to clear." + Style.RESET_ALL)
                
                if os.path.exists(SERVER_LINKS_FILE):
                    os.remove(SERVER_LINKS_FILE)
                    print(Fore.GREEN + 'Server links cleared successfully!' + Style.RESET_ALL)
                else:
                    print(Fore.YELLOW + f"No such file: '{SERVER_LINKS_FILE}' found to clear." + Style.RESET_ALL)


if __name__ == '__main__':
    main_menu()
