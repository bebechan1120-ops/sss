import discord
from discord.ext import commands
from discord import app_commands
import json
import os
import datetime

DATA_FILE = "ticket_config.json"


def load_config():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_config(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)


class TicketView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="🎫 チケット作成",
        style=discord.ButtonStyle.green,
        custom_id="create_ticket"
    )
    async def create_ticket(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):
        config = load_config()
        guild = interaction.guild

        if str(guild.id) not in config:
            return await interaction.response.send_message(
                "チケット設定がされていません。",
                ephemeral=True
            )

        data = config[str(guild.id)]

        category = guild.get_channel(data["category_id"])

        if category is None:
            return await interaction.response.send_message(
                "カテゴリーが見つかりません。",
                ephemeral=True
            )

        for ch in guild.text_channels:
            if ch.name == f"ticket-{interaction.user.id}":
                return await interaction.response.send_message(
                    "すでにチケットがあります。",
                    ephemeral=True
                )

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(
                view_channel=False
            ),
            interaction.user: discord.PermissionOverwrite(
                view_channel=True,
                send_messages=True
            )
        }

        role = guild.get_role(data["staff_role"])
        if role:
            overwrites[role] = discord.PermissionOverwrite(
                view_channel=True,
                send_messages=True
            )

        channel = await guild.create_text_channel(
            f"ticket-{interaction.user.name}",
            category=category,
            overwrites=overwrites
        )

        await channel.send(
            f"{interaction.user.mention} チケットが作成されました。",
            view=CloseTicketView()
        )

        await interaction.response.send_message(
            f"作成しました: {channel.mention}",
            ephemeral=True
        )
      class CloseTicketView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="🔒 チケットを閉じる",
        style=discord.ButtonStyle.red,
        custom_id="close_ticket"
    )
    async def close_ticket(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):
        config = load_config()
        guild = interaction.guild

        data = config.get(str(guild.id))

        if not data:
            return await interaction.response.send_message(
                "設定がありません。",
                ephemeral=True
            )

        log_channel = guild.get_channel(
            data["log_channel"]
        )

        embed = discord.Embed(
            title="🔒 チケット閉鎖",
            color=discord.Color.red(),
            timestamp=datetime.datetime.now(
                datetime.timezone.utc
            )
        )

        embed.add_field(
            name="チャンネル",
            value=interaction.channel.name,
            inline=False
        )

        embed.add_field(
            name="閉じた人",
            value=interaction.user.mention,
            inline=False
        )

        embed.add_field(
            name="時間",
            value=f"<t:{int(datetime.datetime.now().timestamp())}:F>",
            inline=False
        )

        if log_channel:
            await log_channel.send(
                embed=embed
            )

        await interaction.response.send_message(
            "チケットを閉じます。",
            ephemeral=True
        )

        await interaction.channel.delete()


class TicketCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot


    async def cog_load(self):
        self.bot.add_view(TicketView())
        self.bot.add_view(CloseTicketView())


    @app_commands.command(
        name="ticketpanel",
        description="チケットパネルを設置します"
    )
    @app_commands.describe(
        category="作成するカテゴリー",
        log="ログ送信チャンネル",
        staff_role="管理ロール"
    )
    async def ticket_panel(
        self,
        interaction: discord.Interaction,
        category: discord.CategoryChannel,
        log: discord.TextChannel,
        staff_role: discord.Role
    ):

        if not interaction.user.guild_permissions.administrator:
            return await interaction.response.send_message(
                "管理者のみ使用できます。",
                ephemeral=True
            )

        config = load_config()

        config[str(interaction.guild.id)] = {
            "category_id": category.id,
            "log_channel": log.id,
            "staff_role": staff_role.id
        }

        save_config(config)

        embed = discord.Embed(
            title="🎫 チケット",
            description="お問い合わせはこちらから",
            color=discord.Color.blue()
        )

        await interaction.channel.send(
            embed=embed,
            view=TicketView()
        )

        await interaction.response.send_message(
            "チケットパネルを作成しました。",
            ephemeral=True
        )
      async def setup(bot):
    await bot.add_cog(TicketCog(bot))
