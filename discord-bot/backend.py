import configparser
import time
import discord
import logging
import sys
from discord.ext import commands
from colorlog import ColoredFormatter
import aiomysql
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

import os.path

# Loading config.ini
config = configparser.ConfigParser()

try:
    config.read('data/config.ini')
except Exception as e:
    print("Error reading the config.ini file. Error: " + str(e))
    sys.exit()


# Initializing the logger
def colorlogger(name='gcr-bot'):
    # disabler loggers
    for logger in logging.Logger.manager.loggerDict:
        logging.getLogger(logger).disabled = True
    logger = logging.getLogger(name)
    stream = logging.StreamHandler()
    log_format = "%(reset)s%(log_color)s%(levelname)-8s%(reset)s | %(log_color)s%(message)s"
    stream.setFormatter(ColoredFormatter(log_format))
    logger.addHandler(stream)
    return logger  # Return the logger


log = colorlogger()

try:
    discord_token: str = config.get('secret', 'discord_token')
    google_credentials: dict = eval(config.get('secret', 'google_credentials'))
    mysql_host = config.get('secret', 'mysql_host')
    mysql_port = config.getint('secret', 'mysql_port')
    mysql_user = config.get('secret', 'mysql_user')
    mysql_password = config.get('secret', 'mysql_password')
    mysql_database = config.get('secret', 'mysql_database')


    log_level: str = config.get('main', 'log_level')
    owner_ids = config.get('main', 'owner_ids').strip().split(',')
    owner_guilds = config.get('main', 'owner_guilds').strip().split(',')
    backup_interval: int = config.getint('main', 'backup_interval')
    status_interval: int = config.getint('main', 'status_interval')

    embed_footer: str = config.get('discord', 'embed_footer')
    embed_color: int = int(config.get('discord', 'embed_color'), base=16)
    embed_title: str = config.get('discord', 'embed_title')
    embed_url: str = config.get('discord', 'embed_url')


except Exception as err:
    log.critical("Error reading the config.ini file. Error: " + str(err))
    sys.exit()

if log_level.upper() in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]:
    log.setLevel(log_level.upper())
else:
    log.warning(f"Invalid log level {log_level}. Defaulting to INFO.")
    log.setLevel("INFO")

owner_ids = tuple([int(i) for i in owner_ids])
log.debug(owner_ids)

owner_guilds = tuple([int(i) for i in owner_guilds])
log.debug(owner_guilds)

client = commands.Bot(help_command=None, command_prefix="!", intents=discord.Intents.none())  # Setting prefix

"""
async def log(level, category, msg, *args):
    # Db Structure - type, msg, category, timestamp, level
    # categories = ["command", "listener", "backend", "etc"]
    current_time = int(time.time())
    if level.upper() not in ["INFO", "DEBUG", "WARNING", "ERROR", "CRITICAL"]:
        level = "INFO"

    # join msg and args into one string
    if args:
        msg %= args
    msg.replace('"', "")

    # This code logs the message using the correct level's logger based on the level parameter
    match level.upper():
        case "DEBUG":
            log.debug(msg)
        case "INFO":
            log.info(msg)
        case "WARNING":
            log.warning(msg)
        case "ERROR":
            log.error(msg)
        case "CRITICAL":
            log.critical(msg)

    if category not in ["command", "notification", "listener", "backend", "etc"]:
        category = "etc"

    db = sqlite3.connect('./data/data.db')
    cursor = db.cursor()

    cursor.execute('INSERT INTO logs VALUES (?, ?, ?, ?)', (current_time, level, category, msg))
    db.commit()
"""

_embed_template = discord.Embed(
    title="Error!",
    color=embed_color,
    url=embed_url
)
_embed_template.set_footer(text=embed_footer)

embed_template = lambda: _embed_template.copy()
SCOPES = ['https://www.googleapis.com/auth/classroom.courses.readonly',
          'https://www.googleapis.com/auth/classroom.coursework.me.readonly',
          ]  # todo


def error_template(description: str) -> discord.Embed:
    _error_template = discord.Embed(
        title="Error!",
        description=description,
        color=0xff0000,
        url=embed_url
    )
    _error_template.set_footer(text=embed_footer)

    return _error_template.copy()


async def get_creds(user_id: int):
    log.debug("get creds")

    # check for creds in data.db
    pool = await aiomysql.create_pool(
        host=mysql_host, port=mysql_port, user=mysql_user, password=mysql_password, db=mysql_database)

    async with pool.acquire() as db:
        async with db.cursor() as cursor:
            await cursor.execute('SELECT * FROM credentials WHERE user_id = %s;', (user_id,))
            row = await cursor.fetchone()
            log.debug(row)
            if row is not None:
                creds = Credentials.from_authorized_user_info(eval(row[1]), SCOPES)
                if creds.expired and creds.refresh_token:
                    creds.refresh(Request())
                return creds
            else:
                return None


async def connect_gcr(user_id):
    print("E")
    flow = InstalledAppFlow.from_client_config(google_credentials, SCOPES,
                                               redirect_uri='http://127.0.0.1:8000/')

    auth_url, state = flow.authorization_url(prompt='consent')

    pool = await aiomysql.create_pool(
        host='three.nodes.rajtech.me', port=3306, user='u134_GMK0k1OJIP', password='zPow0bEq!NYMXwSSOM==tMfd', db='s134_data'
    )
