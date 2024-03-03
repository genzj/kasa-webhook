from enum import Enum
from typing import Optional

from fastapi import FastAPI
from kasa import SmartPlug
from pydantic import BaseModel

from logging import getLogger

L = getLogger(__name__)


class PlugOperation(Enum):
    ON = "on"
    OFF = "off"

    def is_on(self) -> bool:
        return self == PlugOperation.ON


class PlugAPIInput(BaseModel):
    operation: PlugOperation


class PlugAPIResponse(PlugAPIInput):
    success: bool
    error: Optional[str]


app = FastAPI()


@app.post("/plug/{plug_key}")
async def plug(plug_key: str, req: PlugAPIInput) -> PlugAPIResponse:
    operation = req.operation
    plug = SmartPlug("192.168.1.124")
    try:
        await plug.update()
        L.info("operate %s on %s", operation, plug)

        if operation.is_on():
            await plug.turn_on()
        else:
            await plug.turn_off()
        await plug.update()
        L.info("post-operation %s status: %s", operation, plug)
        new_state = plug.is_on
        return PlugAPIResponse(
            operation=operation, success=(new_state == operation.is_on()), error=""
        )
    except Exception as ex:
        L.exception("failed to execute %s on %s", operation, plug)
        return PlugAPIResponse(
            operation=operation, success=False, error=str(ex),
        )
