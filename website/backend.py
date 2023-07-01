import sys

import aiomysql
from google_auth_oauthlib.flow import InstalledAppFlow
from google.oauth2.credentials import Credentials
import configparser


# read ./data/config.ini
config = configparser.ConfigParser()
config.read('./data/config.ini')

# Get variables from config.ini

try:
    google_credentials: dict = eval(config.get('secret', 'google_credentials'))
    mysql_host = config.get('secret', 'mysql_host')
    mysql_port = config.getint('secret', 'mysql_port')
    mysql_user = config.get('secret', 'mysql_user')
    mysql_password = config.get('secret', 'mysql_password')
    mysql_database = config.get('secret', 'mysql_database')

    # log_level: str = config.get('main', 'log_level')


except Exception as err:
    print("Error reading the config.ini file. Error: " + str(err))
    sys.exit()



async def args_handler(args) -> str:
    if not args:
        return "no_args"

    elif args.get('error'):
        return "error"

    if not args.get('state') or not args.get('code') or not args.get('scope'):
        return "invalid_args"



    flow = InstalledAppFlow.from_client_config(
        google_credentials, args.get('scope'), redirect_uri='http://127.0.0.1:8000/')

    flow.fetch_token(code=args.get('code'))
    creds = flow.credentials
    creds = creds.to_json()

    await add_used_state(args.get('state'))

    pool = await aiomysql.create_pool(
        host='three.nodes.rajtech.me', port=3306, user='u134_GMK0k1OJIP', password='zPow0bEq!NYMXwSSOM==tMfd', db='s134_data')

    async with pool.acquire() as conn:
        async with conn.cursor() as cur:

            # Getting the user_id from the DB's `cache` table
            await cur.execute("SELECT data1 FROM cache WHERE cache_key = %s AND data2 = %s;", ('pending_auth_code', args.get('state')))

            row = await cur.fetchone()

            if not row:
                return "unauthorized_discord_user"
            user_id = row[0]

            # Adding the creds to the DB's `credentials` table
            await cur.execute("INSERT INTO credentials (user_id, creds) VALUES (%s, %s);", (user_id, creds))

            # Deleting the pending_auth_code from the DB's `cache` table
            await cur.execute("DELETE FROM cache WHERE cache_key = %s AND data2 = %s;", ('pending_auth_code', args.get('state')))

            await conn.commit()

    return "success"

async def get_used_states() -> list[str]:
    pool = await aiomysql.create_pool(
        host='three.nodes.rajtech.me', port=3306, user='u134_GMK0k1OJIP', password='zPow0bEq!NYMXwSSOM==tMfd', db='s134_data')

    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute("SELECT data1 FROM cache WHERE cache_key = 'used_state';")
            rows = await cur.fetchall()
            return [row[0] for row in rows]

async def add_used_state(state: str):
    pool = await aiomysql.create_pool(
        host='three.nodes.rajtech.me', port=3306, user='u134_GMK0k1OJIP', password='zPow0bEq!NYMXwSSOM==tMfd',
        db='s134_data')

    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute("INSERT IGNORE INTO cache (cache_key, data1) VALUES ('used_state', %s);", (state,))
            await conn.commit()

