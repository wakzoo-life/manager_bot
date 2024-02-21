import os
import re
import traceback

from os.path import join
from plugins import google

from synology_api import filestation
from PIL import Image

from discord import Message, Interaction, app_commands
from discord.ext import commands

google_util = google.GoogleUtil()


class ZzalUpload(commands.GroupCog, name="업로드"):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.nasStation = filestation.FileStation(
            "192.168.0.135" if os.getenv("MODE") == "PRODUCTION" else "nas.wakzoo.life",
            "5000" if os.getenv("MODE") == "PRODUCTION" else "443",
            "manager",
            "4UwROwe5havL4eTO",
            secure=os.getenv("MODE") != "PRODUCTION",
            cert_verify=False,
            dsm_version=7,
            debug=True,
        )

        self.bot.tree.add_command(app_commands.ContextMenu(name="짤방 이미지 업로드", callback=self.upload_zzal))
        self.bot.tree.add_command(app_commands.ContextMenu(name="~~시 이미지 업로드", callback=self.upload_time))

        if not os.path.exists("temp"):
            os.makedirs("temp")

        super().__init__()

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

            try:
                worksheet = google_util.get_worksheet_by_index(
                    key="1hfW3FTo9cjuMW9Kxvfnrbc6p_HyEnyYeA38mKM7nrOE", index=1
                )
                worksheet_data = worksheet.get_all_records(empty2zero=True)
                resv_zzal_names = [x.get("이름") for x in worksheet_data]

                uploaded = []
                errors = []

                for files in message.attachments:
                    filename = files.filename

                    if not (
                        filename.endswith(".webp")
                        or filename.endswith(".gif")
                        or filename.endswith(".jpg")
                        or filename.endswith(".jpeg")
                        or filename.endswith(".png")
                    ):
                        await interaction.edit_original_response(
                            content=f":warning: `{filename}` 파일은 지원하지 않는 형식입니다."
                        )
                        return

                    zzal_name = message.content.split("name: ")[1]

                    if not zzal_name in resv_zzal_names:
                        await interaction.edit_original_response(
                            content=f":warning: `{zzal_name}` 시트에 등록되지 않은 짤 이름입니다. 등록 후 다시 시도해 주세요."
                        )
                        return

                    zzal_dict_name = (
                        zzal_name.replace(" ", "_")
                        .replace(":", "_")
                        .replace("?", "_")
                        .replace("!", "_")
                        .replace(".", "_")
                        .replace(",", "_")
                        .replace("'", "_")
                        .replace('"', "_")
                    )

                    row = resv_zzal_names.index(zzal_name)

                    await files.save(join("temp/", f"{message.author.id}_{filename}"))

                    if filename.endswith(".jpg") or filename.endswith(".png"):
                        converted_image = Image.open(join("temp/", f"{message.author.id}_{filename}"))
                        converted_image.save(
                            join("temp/", f"{message.author.id}_{re.sub(r'\.(jpg|png)$', '.webp', filename)}"), "webp"
                        )
                        converted_image.close()

                    upload_dest_path = f"/files/zzals/{zzal_dict_name}"

                    uploadRes = self.nasStation.upload_file(
                        dest_path=upload_dest_path,
                        file_path=join("temp/", f"{message.author.id}_{re.sub(r'\.(jpg|png)$', '.webp', filename)}"),
                        overwrite=True,
                    )

                    if uploadRes == "Upload Complete":
                        paths = [x for x in str(worksheet_data[row].get("이미지 경로 (NAS)")).split(",") if x != "0"]
                        paths.append(
                            f"{upload_dest_path}/{message.author.id}_{re.sub(r'\.(jpg|png)$', '.webp', filename)}"
                        )
                        uploaded.append(
                            {
                                "range": "B" + str(row + 2),
                                "values": [[",".join(paths)]],
                            }
                        )
                    else:
                        if len(message.attachments) == 1:
                            await interaction.edit_original_response(
                                content=f":warning: 업로드 중 문제가 발생했습니다.\n\n{uploadRes}"
                            )
                            return
                        else:
                            errors.append(f":warning: {filename} : 업로드 중 문제가 발생했습니다.\n\n{uploadRes}")

                    os.remove(join("temp/", f"{message.author.id}_{filename}"))
                    if filename.endswith(".jpg") or filename.endswith(".jpeg") or filename.endswith(".png"):
                        os.remove(
                            join("temp/", f"{message.author.id}_{re.sub(r'\.(jpg|jpeg|png)$', '.webp', filename)}")
                        )

                if len(uploaded) > 0:
                    worksheet.batch_update(uploaded)
                    if len(uploaded) == 1:
                        await interaction.edit_original_response(content=f":tada: 파일을 업로드하는데 성공했습니다.")
                        return

                    if len(errors) >= 1:
                        await interaction.edit_original_response(
                            content=f":tada: {len(message.attachments)}개 중 {len(uploaded)}개 파일을 업로드하는데 성공했습니다.\n\n{chr(10).join(errors)}"
                        )
                    else:
                        await interaction.edit_original_response(
                            content=f":tada: {len(message.attachments)}개 중 {len(uploaded)}개 파일을 업로드하는데 성공했습니다."
                        )
                else:
                    await interaction.edit_original_response(content=f":warning: 업로드 중 문제가 발생했습니다.")
            except:
                traceback.print_exc()
                await interaction.edit_original_response(content=":warning: 파일을 가져오는 중 오류가 발생했습니다.")

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

            try:
                worksheet = google_util.get_worksheet_by_index(
                    key="1hfW3FTo9cjuMW9Kxvfnrbc6p_HyEnyYeA38mKM7nrOE", index=2
                )
                worksheet_data = worksheet.get_all_records(empty2zero=True)
                resv_zzal_names = [x.get("이름") for x in worksheet_data]

                uploaded = []
                errors = []

                for files in message.attachments:
                    filename = files.filename

                    if not (
                        filename.endswith(".webp")
                        or filename.endswith(".gif")
                        or filename.endswith(".jpg")
                        or filename.endswith(".jpeg")
                        or filename.endswith(".png")
                    ):
                        await interaction.edit_original_response(
                            content=f":warning: `{filename}` 파일은 지원하지 않는 형식입니다."
                        )
                        return

                    zzal_name = message.content.split("time: ")[1]

                    if not zzal_name in resv_zzal_names:
                        await interaction.edit_original_response(
                            content=f":warning: `{zzal_name}` 시트에 등록되지 않은 짤 이름입니다. 등록 후 다시 시도해 주세요."
                        )
                        return

                    zzal_dict_name = (
                        zzal_name.replace(" ", "_")
                        .replace(":", "_")
                        .replace("?", "_")
                        .replace("!", "_")
                        .replace(".", "_")
                        .replace(",", "_")
                        .replace("'", "_")
                        .replace('"', "_")
                    )

                    row = resv_zzal_names.index(zzal_name)
                    member_dict_name = (
                        worksheet_data[row]
                        .get("인물")
                        .replace(" ", "_")
                        .replace(":", "_")
                        .replace("?", "_")
                        .replace("!", "_")
                        .replace(".", "_")
                        .replace(",", "_")
                        .replace("'", "_")
                        .replace('"', "_")
                    )

                    await files.save(join("temp/", f"{message.author.id}_{filename}"))

                    if filename.endswith(".jpg") or filename.endswith(".png"):
                        converted_image = Image.open(join("temp/", f"{message.author.id}_{filename}"))
                        converted_image.save(
                            join("temp/", f"{message.author.id}_{re.sub(r'\.(jpg|png)$', '.webp', filename)}"), "webp"
                        )
                        converted_image.close()

                    upload_dest_path = f"/files/plagueTimes/{member_dict_name}/{zzal_dict_name}"

                    uploadRes = self.nasStation.upload_file(
                        dest_path=upload_dest_path,
                        file_path=join("temp/", f"{message.author.id}_{re.sub(r'\.(jpg|png)$', '.webp', filename)}"),
                        overwrite=True,
                    )

                    if uploadRes == "Upload Complete":
                        paths = [x for x in str(worksheet_data[row].get("이미지 경로 (NAS)")).split(",") if x != "0"]
                        paths.append(
                            f"{upload_dest_path}/{message.author.id}_{re.sub(r'\.(jpg|png)$', '.webp', filename)}"
                        )
                        uploaded.append(
                            {
                                "range": "D" + str(row + 2),
                                "values": [[",".join(paths)]],
                            }
                        )
                    else:
                        if len(message.attachments) == 1:
                            await interaction.edit_original_response(
                                content=f":warning: 업로드 중 문제가 발생했습니다.\n\n{uploadRes}"
                            )
                            return
                        else:
                            errors.append(f":warning: {filename} : 업로드 중 문제가 발생했습니다.\n\n{uploadRes}")

                    os.remove(join("temp/", f"{message.author.id}_{filename}"))
                    if filename.endswith(".jpg") or filename.endswith(".jpeg") or filename.endswith(".png"):
                        os.remove(
                            join("temp/", f"{message.author.id}_{re.sub(r'\.(jpg|jpeg|png)$', '.webp', filename)}")
                        )

                if len(uploaded) > 0:
                    worksheet.batch_update(uploaded)
                    if len(uploaded) == 1:
                        await interaction.edit_original_response(content=f":tada: 파일을 업로드하는데 성공했습니다.")
                        return

                    if len(errors) >= 1:
                        await interaction.edit_original_response(
                            content=f":tada: {len(message.attachments)}개 중 {len(uploaded)}개 파일을 업로드하는데 성공했습니다.\n\n{chr(10).join(errors)}"
                        )
                    else:
                        await interaction.edit_original_response(
                            content=f":tada: {len(message.attachments)}개 중 {len(uploaded)}개 파일을 업로드하는데 성공했습니다."
                        )
                else:
                    await interaction.edit_original_response(content=f":warning: 업로드 중 문제가 발생했습니다.")
            except:
                traceback.print_exc()
                await interaction.edit_original_response(content=":warning: 파일을 가져오는 중 오류가 발생했습니다.")


async def setup(bot: commands.Bot):
    await bot.add_cog(ZzalUpload(bot))
