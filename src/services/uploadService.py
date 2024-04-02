import os
import re
from os.path import join

from enum import Enum
from typing import List

from discord import Attachment
from PIL import Image
from synology_api import filestation

from src.plugins import sheet, filestation


class UploadType(Enum):
    ZZAL = 1  # 짤 업로드, 시트 번호 1
    TIME = 2  # ~~시 업로드, 시트 번호 2
    DICT = 3  # 백과사전 이미지 업로드, 시트 번호 3


class UploadService:
    def __init__(self):
        self.google_util = sheet.SheetPlugin()
        self.nasStation = filestation.FileStationPlugin().getFileStation()

    async def upload(self, type: UploadType, message: str, files: List[Attachment]) -> tuple[int, List[str]]:
        worksheet = self.google_util.get_worksheet_by_index(
            key="1hfW3FTo9cjuMW9Kxvfnrbc6p_HyEnyYeA38mKM7nrOE", index=type
        )

        worksheet_data = worksheet.get_all_records(empty2zero=True, head=2 if type == UploadType.DICT else 1)
        resv_zzal_names = [x.get("이름") for x in worksheet_data]

        uploaded = 0
        errors = []

        for file in files:
            filename = file.filename

            if not (
                filename.endswith(".webp")
                or filename.endswith(".gif")
                or filename.endswith(".jpg")
                or filename.endswith(".jpeg")
                or filename.endswith(".png")
            ):
                _error_msg = f"`{filename}` 파일은 지원하지 않는 형식입니다."

                if len(files) == 1:
                    raise Exception(_error_msg)
                else:
                    errors.append(_error_msg)
                    continue

            zzal_name = (
                message.content.split("time: ")[1] if type == UploadType.TIME else message.content.split("name: ")[1]
            )

            member_dict_name = (
                (
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
                if type == UploadType.TIME
                else None
            )

            if not zzal_name in resv_zzal_names:
                _error_msg = f"`{zzal_name}` 시트에 등록되지 않은 짤 이름입니다. 등록 후 다시 시도해 주세요."

                if len(files) == 1:
                    raise Exception(_error_msg)
                else:
                    errors.append(_error_msg)
                    continue

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

            await file.save(join("temp/", f"{message.author.id}_{filename}"))

            if filename.endswith(".jpg") or filename.endswith(".png"):
                converted_image = Image.open(join("temp/", f"{message.author.id}_{filename}"))
                converted_image.save(
                    join("temp/", f"{message.author.id}_{re.sub(r'\.(jpg|png)$', '.webp', filename)}"), "webp"
                )
                converted_image.close()

            upload_dest_path = (
                f"/files/zzals/{zzal_dict_name}"
                if type == UploadType.ZZAL
                else (
                    f"/files/plagueTimes/{member_dict_name}/{zzal_dict_name}"
                    if type == UploadType.TIME
                    else f"/files/dictionary/{zzal_dict_name}"
                )
            )

            uploadRes = self.nasStation.upload_file(
                dest_path=upload_dest_path,
                file_path=join("temp/", f"{message.author.id}_{re.sub(r'\.(jpg|png)$', '.webp', filename)}"),
                overwrite=True,
            )

            if uploadRes == "Upload Complete":
                uploaded += 1
            else:
                _error_msg = f"업로드 중 문제가 발생했습니다.\n\n{uploadRes}"

                if len(files) == 1:
                    raise Exception(_error_msg)
                else:
                    errors.append(_error_msg)
                    continue

            os.remove(join("temp/", f"{message.author.id}_{filename}"))

            if filename.endswith(".jpg") or filename.endswith(".jpeg") or filename.endswith(".png"):
                os.remove(join("temp/", f"{message.author.id}_{re.sub(r'\.(jpg|jpeg|png)$', '.webp', filename)}"))

        if uploaded > 0:
            if uploaded == 1:
                return (1, [])

            if len(errors) >= 1:
                return (uploaded, chr(10).join(errors))
            else:
                return (uploaded, [])
        else:
            raise Exception(f"업로드 중 문제가 발생했습니다.")
