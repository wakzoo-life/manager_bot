from os import getenv
from dotenv import load_dotenv
from synology_api.filestation import FileStation


@staticmethod
def getSynologyHost() -> dict:
    host = getenv("SYNOLOGY_HOST")

    return {
        "ip_address": host.split("@")[1].split(":")[0],
        "port": host.split("@")[1].split(":")[1],
        "username": host.split("//")[1].split(":")[0],
        "password": host.split("//")[1].split(":")[1].split("@")[0],
        "secure": getenv("MODE").upper() != "PRODUCTION",
        "cert_verify": False,
        "dsm_version": 7,
        "debug": True,
    }


class FileStationPlugin:
    def __init__(self) -> None:
        load_dotenv()

        host = getSynologyHost()

        self._filestation = FileStation(
            ip_address=host["ip_address"],
            port=host["port"],
            username=host["username"],
            password=host["password"],
            secure=host["secure"] or False,
            cert_verify=host["cert_verify"] or False,
            dsm_version=host["dsm_version"] or 7,
            debug=host["debug"] or False,
        )

    def getFileStation(self) -> FileStation:
        return self._filestation
