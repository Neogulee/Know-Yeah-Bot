import discord
import requests
import json
from bs4 import BeautifulSoup
import re


token = open("token.txt", "r").readline()
prefix = '!'
colors = ["bronze", "silver", "gold", "platinum", "diamond", "ruby", "unranked"]
discord_colors = [0xad5600, 0x435f7a, 0xec9a00, 0x27e2a4, 0x00b4fc, 0xff0062, 0x2d2d2d]


class Command:
    def __init__(self, names, args, operation):
        self.__names = names
        self.__args = args
        self.__operation = operation

    def __str__(self):
        ret = "[ "
        for i in range(len(self.__names)):
            ret += self.__names[i]
            if i != len(self.__names) - 1:
                ret += '/'

        for arg in self.__args:
            ret += ' ' + '<' + arg + '>'
        return ret + " ]"

    def run(self, args):
        if len(args) < len(self.__args):
            return None
        if len(self.__args) == 0:
            return self.__operation()
        return self.__operation(args)

    @property
    def names(self):
        return self.__names


class CommandManager:
    def __init__(self):
        self.__commands = []

    def add_command(self, command):
        self.__commands += [command]

    def run(self, cmd, args):
        for command in self.__commands:
            for name in command.names:
                if name == cmd:
                    return command.run(args)
        return None

    def get_commands(self):
        ret = ""
        for i in range(len(self.__commands)):
            ret += str(self.__commands[i])
            if i != len(self.__commands) - 1:
                ret += ", "
        return ret, None


emoji_name2id = {}
client = discord.Client()
command_manager = CommandManager()


def init_command_manager():
    command_manager.add_command(Command(["명령어", "commands"], [], command_manager.get_commands))

    def problem_operation(args):
        number = args[0]
        if not number.isdigit():
            return None

        url = "https://solved.ac/search?query=%s" % number
        request = requests.get(url)
        bs_object = BeautifulSoup(request.text, "html.parser")

        problems = json.loads(str(bs_object.body.contents[1].contents[0]))["props"]["pageProps"]["result"]["problems"]
        if len(problems) == 0:
            return None

        problem = problems[0]
        level = problem["level"] - 1
        color_value = int(level / 5) if level >= 0 else 6
        tier = str(5 - level % 5) if level >= 0 else ''
        color = colors[color_value]
        emoji_name = "%s%s" % (color, tier)

        return (None, discord.Embed(title="%s번: %s <:%s:%d>" % (number, problem["title"], emoji_name, emoji_name2id[emoji_name]),
                                    description="https://www.acmicpc.net/problem/%s" % number,
                                    color=discord_colors[color_value]))

    command_manager.add_command(Command(["문제", "problem"], ["number"], problem_operation))

    def codeforces_notification():
        url = "https://codeforces.com/contests"
        html = requests.get(url)
        bs_object = BeautifulSoup(html.text, "html.parser")

        contests = bs_object.find(href=re.compile("/contests/")).contents
        if len(contests) == 0:
            return None

        title = contests[0]
        before_start = bs_object.find("span", class_="countdown").contents[0]
        return (title + '\n' + "Before Start: " + before_start), None
    command_manager.add_command(Command(["코포", "코드포스", "codeforces"], [], codeforces_notification))


init_command_manager()


@client.event
async def on_ready():
    print("Logged in as")
    print(client.user.name)
    print(client.user.id)
    print("----------------")

    emoji_list = client.emojis
    for emoji in emoji_list:
        emoji_name2id[emoji.name] = emoji.id


@client.event
async def on_message(message):
    if message.author == client.user or message.author.bot:
        return

    prefix_msg = message.content[0:len(prefix)]
    separated_msg = message.content[len(prefix):]
    if prefix_msg == prefix:  # prefixed commands
        if len(separated_msg) <= 0:
            return

        split_msg = separated_msg.split()
        cmd = split_msg[0]
        args = split_msg[1:]

        sending_msg = command_manager.run(cmd, args)
        if sending_msg is not None:
            msg, embed = sending_msg
            if msg is not None:
                await message.channel.send(msg)
            if embed is not None:
                await message.channel.send(embed=embed)

    else:  # prefixless commands
        for word in ["너구리", "Neogulee"]:
            if word in message.content:
                return

        archiving_words = ["대학원", "연구실", "랩", "머학원"]
        detected_word = None
        for word in archiving_words:
            if word in message.content:
                detected_word = word
                break

        if detected_word is not None:
            await message.channel.send("감지된 단어: {}\n```{}: {}```"
                                       .format(detected_word, message.author, message.content))
            return

        question_words = ["클린", "뉴비", "늅", "민초"]
        detected_word = None
        cnt = 0
        for word in question_words:
            if word in message.content:
                detected_word = word
                cnt += 1

        if detected_word is not None:
            await message.channel.send("?" * cnt)
            return

        agree_words = ["변태", "굇수"]
        detected_word = None
        for word in agree_words:
            if word in message.content:
                detected_word = word
                break

        if detected_word is not None:
            await message.channel.send("ㅇㅈ")
            return


client.run(token)
