# load .env variables
from v2enlib import config
from time import sleep

# DO NOT DELETE LINES ABOVE

from bot import BaoBai
from discord.ext import commands
import os, signal, discord


class Main:
    def on_press(self):
        if self.executing:
            os.kill(os.getpid(), signal.SIGINT)

    def __init__(self) -> None:
        # init terminating methods
        signal.signal(signal.SIGTERM, self.on_press)

        # init values
        self.executing = True
        self.main()

    def main(self):
        # init groups
        baobot = BaoBai()

        # init command groups
        client.tree.add_command(baobot.tree)


intents = discord.Intents.all()
client = commands.Bot(command_prefix="/", intents=intents)


# Bot events
@client.event
async def on_ready():
    Main()
    await client.tree.sync()
    await client.wait_until_ready()
    print(f"{client.user} is ready to serve!")


# bot commands
@client.tree.command(name="hello", description="A hello to you :3")
async def hello(ctx: discord.Interaction):
    await ctx.response.send_message(f"Hello, {ctx.user.mention}!", ephemeral=True)


if __name__ == "__main__":
    while True:
        try:
            client.run(config.discord.token)
        except Exception as e:
            w = os.get_terminal_size().columns
            print(f"{'-'*w}\n{e}\n{'-'*w}")
            sleep(10)