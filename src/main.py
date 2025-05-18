from fastapi import FastAPI
from titiler.application.main import app

from rio_tiler.io import Reader

from titiler.core.factory import (
    TilerFactory
)

from src.extensions.terrain import terrainExtension

###############################################################################
# Quantized terrain mesh
terrain = TilerFactory(
    reader=Reader,
    router_prefix="/mesh",
    extensions=[
        terrainExtension(max_size=64)
    ],
)

app.include_router(
    terrain.router,
    prefix="/mesh",
    tags=["Quantized terrain mesh"],
)