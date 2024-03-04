from enum import Enum
from functools import lru_cache
from logging import getLogger
from typing import Annotated, Optional

from fastapi import Depends, FastAPI, HTTPException
from kasa import SmartPlug
from pydantic import BaseModel

from .setting import ApiSettings, PlugSetting

L = getLogger(__name__)


@lru_cache
def get_api_setting() -> ApiSettings:
    settings = ApiSettings()  # type: ignore[CallIssue]
    L.info("loaded API settings %r", settings)
    return settings


def get_plug_name_map(
    settings: Annotated[ApiSettings, Depends(get_api_setting)]
) -> dict[str, PlugSetting]:
    return {plug.name: plug for plug in settings.plugs}


def get_plug_key_map(
    settings: Annotated[ApiSettings, Depends(get_api_setting)],
    plug_map: Annotated[dict[str, PlugSetting], Depends(get_plug_name_map)],
) -> dict[str, PlugSetting]:
    return {
        key: plug_map[name] for key, name in settings.keys.items() if name in plug_map
    }


PlugKeyMap = Annotated[dict[str, PlugSetting], Depends(get_plug_key_map)]


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
async def plug(
    plug_key_map: PlugKeyMap, plug_key: str, req: PlugAPIInput
) -> PlugAPIResponse:
    operation = req.operation
    if plug_key not in plug_key_map:
        raise HTTPException(status_code=404)
    plug_config = plug_key_map[plug_key]
    L.info("operate %s on key %s (plug_config %s)", operation, plug_key, plug_config)
    plug = SmartPlug(plug_config.host)
    try:
        await plug.update()
        L.info("pre-operate %s: %s", operation, plug)

        if operation.is_on():
            await plug.turn_on()
        else:
            await plug.turn_off()
        await plug.update()
        L.info("post-operation %s: %s", operation, plug)
        new_state = plug.is_on
        return PlugAPIResponse(
            operation=operation, success=(new_state == operation.is_on()), error=""
        )
    except Exception as ex:
        L.exception("failed to execute %s on %s", operation, plug)
        return PlugAPIResponse(
            operation=operation,
            success=False,
            error=str(ex),
        )
