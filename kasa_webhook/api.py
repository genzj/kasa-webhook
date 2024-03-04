from asyncio import gather
from enum import Enum
from functools import lru_cache
from logging import getLogger
from typing import Annotated, Optional
from datetime import datetime

from fastapi import Depends, FastAPI, HTTPException
from kasa import SmartPlug
from pydantic import BaseModel

from .setting import ApiSettings, PlugSetting

L = getLogger(__name__)


@lru_cache
def get_api_setting() -> ApiSettings:
    settings = ApiSettings()  # type: ignore[CallArg]
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


PlugNameMap = Annotated[dict[str, PlugSetting], Depends(get_plug_name_map)]
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


class PingResponse(BaseModel):
    healthy: bool = True
    timestamp: float


class DeepPingResponse(PingResponse):
    plug_count: int
    online_plug_host: list[str]
    offline_plug_host: list[str]
    offline_reason: list[str]


@app.get("/ping")
async def ping() -> PingResponse:
    return PingResponse(timestamp=datetime.utcnow().timestamp())


@app.get("/deepping")
async def deepping(plugs: PlugNameMap) -> DeepPingResponse:
    async def ping_plug(plug: SmartPlug) -> SmartPlug:
        await plug.update()
        return plug

    all_plugs = tuple(plugs.values())
    online_devices: list[PlugSetting] = []
    offline_devices: list[PlugSetting] = []
    discovery_exceptions: list[BaseException] = []
    for idx, plug in enumerate(
        await gather(
            *[ping_plug(SmartPlug(host=plug.host)) for plug in all_plugs],
            return_exceptions=True
        )
    ):
        if isinstance(plug, SmartPlug):
            online_devices.append(all_plugs[idx])
        else:
            offline_devices.append(all_plugs[idx])
            discovery_exceptions.append(plug)

    return DeepPingResponse(
        timestamp=datetime.utcnow().timestamp(),
        plug_count=len(plugs.items()),
        online_plug_host=[plug.host for plug in online_devices],
        offline_plug_host=[plug.host for plug in offline_devices],
        offline_reason=list(map(str, discovery_exceptions)),
    )
