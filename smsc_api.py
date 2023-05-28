import asyncio
import random
from datetime import datetime

import aiohttp

from redis_manager import redis_manager
from settings import settings


class SMSCManager:
    def __init__(self, msg_queue: asyncio.Queue):
        self.msg_queue = msg_queue

    async def request_smsc(self, text: str) -> dict:
        if settings.mock_return_value:
            mock_id = str(random.randint(0, 100))
            created_at = datetime.now().timestamp()
            await redis_manager.add_sms_mailing(
                sms_id=mock_id,
                phones=settings.phone_numbers.split(","),
                text=text,
                created_at=created_at,
            )
            return {
                "id": 348,
                "cnt": 1,
                "cost": "4.1",
                "balance": "137.45",
                "mock": True,
            }
        data = {
            "login": settings.smsc_login,
            "psw": settings.smsc_password,
            "phones": settings.phone_numbers,
            "valid": settings.valid,
            "mes": text,
            "cost": 3,
        }
        async with aiohttp.ClientSession() as session:
            async with session.post("https://smsc.ru/rest/send/", json=data) as r:
                """
                {'balance': '83.6', 'cnt': 1, 'cost': '4.1', 'id': 14}
                """
                result = await r.json()
                created_at = datetime.now().timestamp()
                await redis_manager.add_sms_mailing(
                    sms_id=result["id"],
                    phones=settings.phone_numbers.split(","),
                    text=text,
                    created_at=created_at,
                )
                return result

    async def check_status(
        self,
        sms_id: str,
    ) -> str:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"https://smsc.ru/sys/status.php?login={settings.smsc_login}&psw={settings.smsc_password}"
                f"&phone={settings.phone_numbers}&id={sms_id}"
            ) as status:
                return await status.text()

    async def send_progres(self):
        while True:
            sms_ids = await redis_manager.list_sms_mailings()
            mailings = await redis_manager.get_sms_mailings(sms_ids)
            sms_progress = []
            for item in mailings:
                sms_progress.append(
                    {
                        "timestamp": item["created_at"],
                        "SMSText": item["text"],
                        "mailingId": item["sms_id"],
                        "totalSMSAmount": item["phones_count"],
                        "deliveredSMSAmount": 0,
                        "failedSMSAmount": 0,
                    }
                )
            data = {"msgType": "SMSMailingStatus", "SMSMailings": sms_progress}
            self.msg_queue.put_nowait(data)
            await asyncio.sleep(1)
