import os
import re
from os.path import join

from enum import Enum
from typing import List

from discord import Attachment, Message
from PIL import Image
from synology_api import filestation

from plugins import sheet, filestation


class UploadType(Enum):
    ZZAL = 1  # 짤 업로드, 시트 번호 1
    TIME = 2  # ~~시 업로드, 시트 번호 2
    DICT = 3  # 백과사전 이미지 업로드, 시트 번호 3


class UploadService:
    def __init__(self):
        self.google_util = sheet.SheetPlugin()
        self.nasStation = filestation.FileStationPlugin().getFileStation()

    async def upload(self, type: UploadType, message: Message) -> tuple[int, str]:
        # 데이터 시트 Open
        worksheet = self.google_util.get_worksheet_by_index(
            key="1hfW3FTo9cjuMW9Kxvfnrbc6p_HyEnyYeA38mKM7nrOE", index=type.value
        )

        worksheet_data = worksheet.get_all_records(empty2zero=True)

        # 짤 이름만 골라서 Get
        resv_zzal_names = [x.get("이름") for x in worksheet_data]

        uploaded = 0
        errors = []

        for file in message.attachments:
            # 2024-04-09 FIX: 대문자 확장자에서 오류 나는 문제 수정
            filename = file.filename.lower()

            if not (
                filename.endswith(".webp")
                or filename.endswith(".gif")
                or filename.endswith(".jpg")
                or filename.endswith(".jpeg")
                or filename.endswith(".png")
            ):
                _error_msg = f"`{filename}` 파일은 지원하지 않는 형식입니다."

                if len(message.attachments) == 1:
                    raise Exception(_error_msg)
                else:
                    errors.append(_error_msg)
                    continue

            # 업로드 하는 짤 이름 GET (YAML 타입)
            zzal_name = (
                message.content.split("time: ")[1] if type == UploadType.TIME else message.content.split("name: ")[1]
            )

            # 2024-04-09 FIX: 시트에 등록되어 있는 짤인지 확인하기 (~~ is not in list 문제 수정)
            if not zzal_name in resv_zzal_names:
                _error_msg = f"`{zzal_name}` 시트에 등록되지 않은 짤 이름입니다. 등록 후 다시 시도해 주세요."

                if len(message.attachments) == 1:
                    raise Exception(_error_msg)
                else:
                    errors.append(_error_msg)
                    continue

            # 등록되어 있다면 어느 row에 있는지 GET
            row = resv_zzal_names.index(zzal_name)

            # ~~시 - 인물 이름 Formatting
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

            # 짤 이미지 이름 Formatting
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

            # 임시 폴더에 저장
            await file.save(join("temp/", f"{message.author.id}_{filename}"))

            # 파일이 jpg/jpeg/png라면
            if filename.endswith(".jpg") or filename.endswith(".jpeg") or filename.endswith(".png"):
                converted_image = Image.open(join("temp/", f"{message.author.id}_{filename}"))
                converted_image.save(
                    join("temp/", f"{message.author.id}_{re.sub(r'\.(jpg|jpeg|png)$', '.webp', filename)}"), "webp"
                )
                converted_image.close()

            # 업로드할 폴더 지정
            upload_dest_path = (
                f"/files/zzals/{zzal_dict_name}"
                if type == UploadType.ZZAL
                else (
                    f"/files/plagueTimes/{member_dict_name}/{zzal_dict_name}"
                    if type == UploadType.TIME
                    else f"/files/dictionary/{zzal_dict_name}"
                )
            )

            # 업로드 처리
            uploadRes = self.nasStation.upload_file(
                dest_path=upload_dest_path,
                file_path=join("temp/", f"{message.author.id}_{re.sub(r'\.(jpg|jpeg|png)$', '.webp', filename)}"),
                overwrite=True,
            )

            if uploadRes == "Upload Complete":
                uploaded += 1
            else:
                _error_msg = f"업로드 중 문제가 발생했습니다.\n\n{uploadRes}"

                if len(message.attachments) == 1:
                    raise Exception(_error_msg)
                else:
                    errors.append(_error_msg)
                    continue

            # 임시 파일 정리
            os.remove(join("temp/", f"{message.author.id}_{filename}"))

            if filename.endswith(".jpg") or filename.endswith(".jpeg") or filename.endswith(".png"):
                os.remove(join("temp/", f"{message.author.id}_{re.sub(r'\.(jpg|jpeg|png)$', '.webp', filename)}"))

        if uploaded > 0:
            if uploaded == 1:
                return (1, "")

            if len(errors) >= 1:
                return (uploaded, chr(10).join(errors))
            else:
                return (uploaded, "")
        else:
            raise Exception(f"업로드 중 문제가 발생했습니다.")
