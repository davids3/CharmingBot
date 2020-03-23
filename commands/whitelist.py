from commands.base import Command
from helpers import *
import json
import urllib
import asyncio
import subprocess
from configstartup import config
from utils.embed_table import EmbedTable

WHITELIST_FILE = config['FILES'].get('Whitelist')
WHITELIST_CHANNEL = config['CHANNELS'].get('Whitelist')
SUB_ROLE_NAME = "Twitch Subscriber"
SUB_ROLE_ID = config['FILES'].get(SUB_ROLE_NAME)
SLEEP_INTERVAL = 10
WHITELIST_PATH = '/home/mchost/Spigot2/whitelist.json'

class Whitelist(Command):
    desc = "Commands for controlling Minecraft whitelist"
    roles_required = [SUB_ROLE_NAME]

class Add(Whitelist):
    desc = "Adds your Minecraft username to the bot"

    async def eval(self, username):
        api = MojangAPI()
        mc_user = api.getbyname(username)
        if mc_user is None:
            raise CommandFailure('Username does not exist!')
        
        # Open the JSON file or create a new dict to load
        try:
            with open(WHITELIST_FILE, 'r') as old:
                whitelist_dict = json.load(old)
        except FileNotFoundError:
            whitelist_dict = dict()

        if self.user in whitelist_dict:
            raise CommandFailure('Username for %s already exists! To update, please remove and re-add.' % self.name)
        
        mc_user['uuid'] = mc_user['id'][:8] + '-' + mc_user['id'][8:12] + '-' + mc_user['id'][12:16] + '-' + mc_user['id'][16:20] + '-' + mc_user['id'][20:]
        mc_user.pop('id')
        whitelist_dict[self.user] = mc_user
        
        with open(WHITELIST_FILE, 'w') as new:
            json.dump(whitelist_dict, new)

        update_whitelist_file()

        return "%s added as username for %s!" % (mc_user['name'], self.name)


class Remove(Whitelist):
    desc = "Removes your Minecraft username from the bot if it exists"

    async def eval(self):
        # Open the JSON file or create a new dict to load
        try:
            with open(WHITELIST_FILE, 'r') as old:
                whitelist_dict = json.load(old)
        except FileNotFoundError:
            raise CommandFailure('Whitelist is empty!')

        if self.user not in whitelist_dict:
            raise CommandFailure('No entry for %s in whitelist!' % self.name)

        mc_user = whitelist_dict.pop(self.user)

        with open(WHITELIST_FILE, 'w') as new:
            json.dump(whitelist_dict, new)

        update_whitelist_file()

        return "%s removed as username for %s!" % (mc_user['name'], self.name)

class List(Whitelist):
    desc = "Lists all Minecraft usernames in whitelist"

    async def eval(self):
        # Open the JSON file or create a new dict to load
        try:
            with open(WHITELIST_FILE, 'r') as old:
                whitelist_dict = json.load(old)
        except FileNotFoundError:
            raise CommandFailure('Whitelist is empty!')

        return EmbedTable(fields=['User', 'MC Name'],
                          table=[(self.from_id(user).name, mc_user['name']) for user, mc_user in whitelist_dict.items()],
                          colour=self.EMBED_COLOR,
                          title="Minecraft Whitelist")

class MojangAPI:
    def __init__(self):
        self.base_url = 'https://api.mojang.com'

    def getbyUUID(self, uuid):
        return self.request('/user/profiles/%s/names' % uuid)

    def getbyname(self, name):
        return self.request('/users/profiles/minecraft/%s' % name)

    def request(self, endpoint):
        """Make API request to Admin API and parse response JSON"""
        apiRequest = urllib.request.Request(url = self.base_url + endpoint)

        with urllib.request.urlopen(apiRequest) as apiResponse:
            res = apiResponse.read().decode('utf-8')
            if res == '':
                return None
            else:
                return json.loads(res)

def update_whitelist_file():
    try:
        with open(WHITELIST_FILE, 'r') as f:
            whitelist_dict = json.load(f)
        
        whitelist_list = []
        for id, mc_user in whitelist_dict.items():
            whitelist_list.append(mc_user)

        with open(WHITELIST_PATH, 'w+') as path:
            path.write(json.dumps(whitelist_list, indent=2))

    except FileNotFoundError:
        return

    try:
        subprocess.run(['screen', '-S', 'spigot2', '-X', 'stuff',  'whitelist reload\\r'])

    except:
        return

# async def check_whitelist(client, channel):
#     while(True):
#         await asyncio.sleep(SLEEP_INTERVAL)
        
#         # Open the JSON file, skip if it does not exist
#         try:
#             with open(WHITELIST_FILE, 'r') as old:
#                 whitelist_dict = json.load(old)
#         except FileNotFoundError:
#             continue

#         for user, mc_user in whitelist_dict.items():
#             # get list of role members by role name
#             for role in channel.server.roles:
#                 if role.name == SUB_ROLE_NAME:
#                     role_members = role.members
#                     break
            
#             # check user in list of role members
#             if user not in [member.id for member in role_members]:
#                 mc_user = whitelist_dict.pop(user)
#                 message = '%s is no longer a %s, removing from whitelist' % (mc_user['name'], SUB_ROLE_NAME)
#                 client.send_message(channel, message)
