import os
import json
import base64

from google.oauth2.service_account import Credentials
from googleapiclient.discovery import Resource, build
from gspread import Client, Worksheet, authorize


class GoogleUtil:
    def __init__(self):
        self._credentials = Credentials.from_service_account_info(
            json.loads(base64.b64decode(os.getenv("GOOGLE_CREDENTIALS"))),
            scopes=["https://www.googleapis.com/auth/spreadsheets"],
        )

    def _get_gspread_client(self) -> Client:
        client = authorize(credentials=self._credentials)
        return client

    def get_worksheet_by_index(self, key: str, index: int) -> Worksheet:
        client = self._get_gspread_client()
        spreadsheet = client.open_by_key(key=key)

        return spreadsheet.get_worksheet(index or 1)

    def get_spreads(self) -> Resource:
        return build("sheets", "v4", credentials=self._credentials)
