"""AWS Lambda handler."""

import logging

from mangum import Mangum

from titiler.application.settings import ApiSettings

from kepler_raster_server import app

logging.getLogger("mangum.lifespan").setLevel(logging.ERROR)
logging.getLogger("mangum.http").setLevel(logging.ERROR)

api_settings = ApiSettings()

handler = Mangum(app, api_gateway_base_path=api_settings.root_path, lifespan="auto")
