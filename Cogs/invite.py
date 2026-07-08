import discord
from discord.ext import commands
from discord import app_commands
import json
import os


DATA_FILE = "invite_data.json"


def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)


class InviteView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="🔗 専用の招待リンク作成",
        style=discord.ButtonStyle.green,
        custom_id="create_invite"
    )
    async def create_invite(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):

        data = load_data()

        user_id = str(interaction.user.id)

        channel = interaction.channel

        invite = await channel.create_invite(
            max_age=0,
            max_uses=0,
            unique=True,
            reason=f"{interaction.user} 専用リンク"
        )

        if user_id not in data:
            data[user_id] = {
                "invite_count": 0,
                "invite_code": invite.code
            }
        else:
            data[user_id]["invite_code"] = invite.code

        save_data(data)

        await interaction.response.send_message(
            f"🔗 あなた専用招待リンク\n{invite.url}",
            ephemeral=True
        )


    @discord.ui.button(
        label="📊 自分の招待数を見る",
        style=discord.ButtonStyle.blurple,
        custom_id="check_invite"
    )
    async def check_invite(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):

        data = load_data()

        count = data.get(
            str(interaction.user.id),
            {}
        ).get(
            "invite_count",
            0
        )

        await interaction.response.send_message(
            f"📊 あなたの招待数\n\n{count}人",
            ephemeral=True
        )
class InviteCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.invites = {}


    async def cog_load(self):
        self.bot.add_view(InviteView())


    async def get_invites(self, guild):
        invites = await guild.invites()

        result = {}

        for invite in invites:
            result[invite.code] = invite.uses

        return result


    @commands.Cog.listener()
    async def on_ready(self):
        for guild in self.bot.guilds:
            self.invites[guild.id] = await self.get_invites(guild)


    @commands.Cog.listener()
    async def on_member_join(self, member):

        guild = member.guild

        before = self.invites.get(
            guild.id,
            {}
        )

        after = await self.get_invites(guild)

        used_invite = None

        for code, uses in after.items():
            if uses > before.get(code, 0):
                used_invite = code
                break


        self.invites[guild.id] = after


        if used_invite is None:
            return


        data = load_data()


        for user_id, info in data.items():

            if info.get("invite_code") == used_invite:

                if user_id not in data:
                    data[user_id] = {}

                data[user_id]["invite_count"] = (
                    data[user_id].get(
                        "invite_count",
                        0
                    ) + 1
                )

       save_data(data)

       break
 

@app_commands.command(
        name="招待パネル作成",
        description="招待パネルを作成します"
    )
    @app_commands.describe(
        message="パネルに表示する文章"
    )
    async def invite_panel(
        self,
        interaction: discord.Interaction,
        message: str
    ):

        if not interaction.user.guild_permissions.administrator:
            return await interaction.response.send_message(
                "管理者のみ使用できます。",
                ephemeral=True
            )

        embed = discord.Embed(
            title="🎁 招待システム",
            description=message,
            color=discord.Color.blue()
        )

        embed.set_footer(
            text="Developer @anzy1m"
        )

        await interaction.channel.send(
            embed=embed,
            view=InviteView()
        )

        await interaction.response.send_message(
            "招待パネルを作成しました。",
            ephemeral=True
        )


    @app_commands.command(
        name="招待ランキング",
        description="招待数ランキングを表示します"
    )
    async def invite_rank(
        self,
        interaction: discord.Interaction
    ):

        if not interaction.user.guild_permissions.administrator:
            return await interaction.response.send_message(
                "管理者のみ使用できます。",
                ephemeral=True
            )

        data = load_data()

        ranking = sorted(
            data.items(),
            key=lambda x: x[1].get(
                "invite_count",
                0
            ),
            reverse=True
        )


        embed = discord.Embed(
            title="🏆 招待ランキング",
            color=discord.Color.gold()
        )


        if not ranking:
            embed.description = "データがありません。"

        else:
            text = ""

            for i, (user_id, info) in enumerate(
                ranking[:10],
                start=1
            ):
                user = interaction.guild.get_member(
                    int(user_id)
                )

                name = (
                    user.mention
                    if user
                    else user_id
                )

                text += (
                    f"**{i}位** {name}\n"
                    f"招待数: {info.get('invite_count',0)}人\n\n"
                )

            embed.description = text


        await interaction.response.send_message(
            embed=embed
        )


async def setup(bot):
    await bot.add_cog(InviteCog(bot))
