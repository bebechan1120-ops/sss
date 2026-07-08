import discord
from discord.ext import commands
from discord import app_commands
import os
import traceback

TOKEN = os.getenv("TOKEN")

intents = discord.Intents.all()
bot = commands.Bot(
    command_prefix="$",
    intents=intents,
    help_command=None
)

async def setup_hook():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    cogs_dir = os.path.join(base_dir, "Cogs")

    print(f"[INFO] Cogs dir: {cogs_dir}")

    if not os.path.exists(cogs_dir):
        print("[ERROR] Cogsフォルダが存在しません")
        return

    for file in os.listdir(cogs_dir):
        if file.endswith(".py") and not file.startswith("_"):
            ext = f"Cogs.{file[:-3]}"
            try:
                await bot.load_extension(ext)
                print(f"[OK] Loaded Cog: {ext}")
            except Exception as e:
                print(f"[NG] Failed Cog: {ext}")
                traceback.print_exc()

    await bot.tree.sync()
    print("[INFO] Slash commands synced")

bot.setup_hook = setup_hook

@bot.event
async def on_ready():
    guild_count = len(bot.guilds)
    member_count = sum(g.member_count or 0 for g in bot.guilds)

    await bot.change_presence(
        activity=discord.Game(
            name=f"{guild_count}サーバー / {member_count}人"
        )
    )

    print("===================================")
    print(f"Bot logged in as {bot.user}")
    print(f"Servers: {guild_count}")
    print(f"Members: {member_count}")
    print("===================================")

@bot.tree.error
async def on_app_command_error(
    interaction: discord.Interaction,
    error: app_commands.AppCommandError
):
    print(error)
    traceback.print_exc()

if __name__ == "__main__":
    bot.run(TOKEN)
