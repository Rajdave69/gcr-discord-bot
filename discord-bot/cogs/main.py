import asyncio

import discord
from discord.ext import commands
from backend import connect_gcr, get_response, get_class_list, get_creds, embed_template, error_template, is_connected, \
    remove_response, disconnect_gcr
from discord import app_commands

class Main(commands.Cog):
    def __init__(self, client):
        self.client = client

    @commands.Cog.listener()
    async def on_ready(self):
        print("Cog: Main.py is ready")

        # await self.client.app_commands.sync()

    @app_commands.command(name="connect")
    async def connect(self, interaction):
        # await interaction.response.defer()
        if await is_connected(interaction.user.id):
            await interaction.response.send_message(embed=error_template("You already have a connected Google Classroom account."), ephemeral=True)
            return


        print("e")
        auth_url, state = await connect_gcr(interaction.user.id)
        print("f")

        embed = embed_template()
        embed.title = "Connect"
        embed.description = "Please click the link below to connect your Google Classroom account.\n " \
                            "**Do not send this to anyone else**"
        embed.add_field(name="Link", value=f"[Click Here]({auth_url})")
        await interaction.response.send_message(embed=embed, ephemeral=True)

        while True:
            response = await get_response(state)
            print(response)

            if response == "success":
                embed = embed_template()
                embed.title = "Success!"
                embed.description = "Your Google Classroom account has been successfully connected."
                await interaction.edit_original_response(embed=embed)

                await remove_response(state)
                break

            if response == "error":
                await interaction.response.edit(embed=error_template("An error occurred. Please try again."), ephemeral=True)

                await remove_response(state)
                break

            print("e")
            await asyncio.sleep(1)

        # await interaction.response.edit("test")


    @app_commands.command(name="disconnect")
    async def disconnect(self, interaction):
        if not await is_connected(interaction.user.id):
            await interaction.response.send_message(embed=error_template("You don't have a connected Google Classroom account."), ephemeral=True)
            return

        await disconnect_gcr(interaction.user.id)

        embed = embed_template()
        embed.title = "Success!"
        embed.description = "Your Google Classroom account has been successfully disconnected."
        await interaction.response.send_message(embed=embed, ephemeral=True)




async def setup(client):
    await client.add_cog(Main(client))