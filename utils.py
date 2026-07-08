import discord
from discord import app_commands


def is_allowed():
    async def predicate(interaction: discord.Interaction):
        # サーバー内のメンバーか確認
        if isinstance(interaction.user, discord.Member):
            # 管理者権限があるか確認
            if interaction.user.guild_permissions.administrator:
                return True

        # 許可されていない場合
        raise app_commands.CheckFailure(
            "このコマンドはサーバー管理者のみ使用できます。"
        )

    return app_commands.check(predicate)
