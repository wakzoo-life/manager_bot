import os
import traceback

from discord import Message, Interaction, app_commands
from discord.ext import commands

from services import uploadService


class ZzalUpload(commands.GroupCog, name="업로드"):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.uploadService = uploadService.UploadService()

        self.bot.tree.add_command(app_commands.ContextMenu(name="짤방 이미지 업로드", callback=self.upload_zzal))
        self.bot.tree.add_command(app_commands.ContextMenu(name="~~시 이미지 업로드", callback=self.upload_time))
        self.bot.tree.add_command(app_commands.ContextMenu(name="백과사전 이미지 업로드", callback=self.upload_dict))

        if not os.path.exists("temp"):
            os.makedirs("temp")

        super().__init__()

    async def _upload(self, interaction: Interaction, message: Message, upload_type: uploadService.UploadType) -> None:
        try:
            [
                uploaded,
                error,
            ] = await self.uploadService.upload(upload_type, message.content, message.attachments)

            if uploaded > 0:
                if uploaded == 1:
                    await interaction.edit_original_response(content=f":tada: 파일을 업로드하는데 성공했습니다.")
                else:
                    multiple_msg = (
                        f":tada: {len(message.attachments)}개 중 {uploaded}개 파일을 업로드하는데 성공했습니다."
                    )

                    if error != "":
                        multiple_msg += f"\n\n{error}"

                    await interaction.edit_original_response(content=multiple_msg)
            else:
                await interaction.edit_original_response(content=f":warning: 업로드 중 문제가 발생했습니다.")
        except Exception as e:
            traceback.print_exc()
            await interaction.edit_original_response(content=f":warning: {e}")

    async def upload_zzal(self, interaction: Interaction, message: Message) -> None:
        if len(message.attachments) <= 0:
            await interaction.response.send_message(
                ":warning: 파일을 첨부한 뒤 업로드를 시도해 주세요.", ephemeral=True
            )
        elif len(message.content) <= 0:
            await interaction.response.send_message(
                ":warning: 짤 이름을 입력한 뒤 업로드를 시도해 주세요.", ephemeral=True
            )
        elif not message.content.startswith("name: "):
            await interaction.response.send_message(":warning: 짤 이름은 `name: `으로 시작해야 합니다.", ephemeral=True)
        elif "\n" in message.content:
            await interaction.response.send_message(":warning: 짤 이름은 한 줄로 입력해 주세요.", ephemeral=True)
        else:
            await interaction.response.defer(thinking=True)
            await self._upload(interaction, message, uploadService.UploadType.ZZAL)

    async def upload_time(self, interaction: Interaction, message: Message) -> None:
        if len(message.attachments) <= 0:
            await interaction.response.send_message(
                ":warning: 파일을 첨부한 뒤 업로드를 시도해 주세요.", ephemeral=True
            )
        elif len(message.content) <= 0:
            await interaction.response.send_message(
                ":warning: 시간 이름을 입력한 뒤 업로드를 시도해 주세요.", ephemeral=True
            )
        elif not message.content.startswith("time: "):
            await interaction.response.send_message(
                ":warning: 시간 이름은 `time: `으로 시작해야 합니다.", ephemeral=True
            )
        elif "\n" in message.content:
            await interaction.response.send_message(":warning: 시간 이름은 한 줄로 입력해 주세요.", ephemeral=True)
        else:
            await interaction.response.defer(thinking=True)
            await self._upload(interaction, message, uploadService.UploadType.TIME)

    async def upload_dict(self, interaction: Interaction, message: Message) -> None:
        if len(message.attachments) <= 0:
            await interaction.response.send_message(
                ":warning: 파일을 첨부한 뒤 업로드를 시도해 주세요.", ephemeral=True
            )
        elif len(message.content) <= 0:
            await interaction.response.send_message(
                ":warning: 단어 이름을 입력한 뒤 업로드를 시도해 주세요.", ephemeral=True
            )
        elif not message.content.startswith("name: "):
            await interaction.response.send_message(
                ":warning: 단어 이름은 `name: `으로 시작해야 합니다.", ephemeral=True
            )
        elif "\n" in message.content:
            await interaction.response.send_message(":warning: 단어 이름은 한 줄로 입력해 주세요.", ephemeral=True)
        else:
            await interaction.response.defer(thinking=True)
            await self._upload(interaction, message, uploadService.UploadType.DICT)


async def setup(bot: commands.Bot):
    await bot.add_cog(ZzalUpload(bot))
