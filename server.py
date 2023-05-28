import asyncio

from fastapi import FastAPI, Form, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse

from broker import ConnectionManager
from pd_models import Message
from redis_manager import redis_manager
from smsc_api import SMSCManager

app = FastAPI()

msg_queue = asyncio.Queue()
connection_manager = ConnectionManager(msg_queue=msg_queue)
smsc_manager = SMSCManager(msg_queue=msg_queue)


@app.on_event("startup")
async def startup_event():
    asyncio.create_task(connection_manager.run())
    asyncio.create_task(smsc_manager.send_progres())


@app.on_event("shutdown")
async def shutdown_event():
    await redis_manager.close()


@app.get("/")
async def get():
    return FileResponse("front/index.html", media_type="text/html")


@app.post("/send/")
async def send_sms(text: str = Form(...)):
    text_data = Message(text=text)
    # {'id': 348, 'cnt': 1, 'cost': '4.1', 'balance': '137.45'}
    response = await smsc_manager.request_smsc(text=text_data.text)
    sms_id = response["id"]
    print(f"Sending SMS result: {response=}  {sms_id=}")
    return {"status": "Message sent"}


@app.websocket("/ws/")
async def websocket_endpoint(websocket: WebSocket):
    await connection_manager.connect(websocket)
    try:
        while True:
            msg = await websocket.receive_text()
            print(msg)
    except WebSocketDisconnect:
        connection_manager.disconnect(websocket)
