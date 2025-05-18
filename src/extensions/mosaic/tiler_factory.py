import json
import os
import time
from dataclasses import dataclass
from typing import Any, Dict, Type, Optional, Literal

import rasterio
from cogeo_mosaic.errors import NoAssetFoundError
from fastapi import Depends, Path, Query
from morecantile import TileMatrixSet
from rio_tiler.constants import MAX_THREADS
from rio_tiler.models import ImageData
from rio_tiler.mosaic import mosaic_reader
from starlette.responses import Response
from titiler.core.dependencies import DefaultDependency
from titiler.core.factory import img_endpoint_params
from titiler.core.resources.enums import ImageType, OptionalHeader

from rio_tiler.mosaic.methods import PixelSelectionMethod

from titiler.mosaic.factory import MosaicTilerFactory


# This code is copied from marblecutter
#  https://github.com/mojodna/marblecutter/blob/master/marblecutter/stats.py
# License:
# Original work Copyright 2016 Stamen Design
# Modified work Copyright 2016-2017 Seth Fitzsimmons
# Modified work Copyright 2016 American Red Cross
# Modified work Copyright 2016-2017 Humanitarian OpenStreetMap Team
# Modified work Copyright 2017 Mapzen
class Timer(object):
    """Time a code block."""

    def __enter__(self):
        """Starts timer."""
        self.start = time.time()
        return self

    def __exit__(self, ty, val, tb):
        """Stops timer."""
        self.end = time.time()
        self.elapsed = self.end - self.start

    @property
    def from_start(self):
        """Return time elapsed from start."""
        return time.time() - self.start

# Dependencies for  MultiBandReader
@dataclass
class STACMosaicBackendParams(DefaultDependency):
    """Band names parameters."""

    query: str = Query(
        ...,
        title="STAC API Query",
        description="Query to send to STAC API.",
    )

    def __post_init__(self):
        """Post Init."""
        self.query = json.loads(self.query)
        #self.kwargs["query"] = json.loads(self.query)


class STACMosaicTilerFactory(MosaicTilerFactory):
    """Subclass of MosaicTilerFactory to pass query to DynamicStacBackend

    For now, a subclass of MosaicTilerFactory is required (instead of using
    MosaicTilerFactory directly) because there's no way to pass user-provided
    arguments to the MosaicBackend. The DynamicStacBackend requires a query
    argument to be passed to its constructor, and that query isn't known until
    runtime.
    """

    mosaic_dependency: Type[DefaultDependency] = STACMosaicBackendParams

    ############################################################################
    # /tiles
    ############################################################################
    def tile(self):  # noqa: C901
        """Register /tiles endpoints."""

        #@self.router.get(r"/tiles/{z}/{x}/{y}", **img_endpoint_params)
        @self.router.get(r"/tiles/{z}/{x}/{y}.{format}", **img_endpoint_params)
        #@self.router.get(r"/tiles/{z}/{x}/{y}@{scale}x", **img_endpoint_params)
        @self.router.get(r"/tiles/{z}/{x}/{y}@{scale}x.{format}", **img_endpoint_params)
        #@self.router.get(r"/tiles/{TileMatrixSetId}/{z}/{x}/{y}", **img_endpoint_params)
        @self.router.get(
            r"/tiles/{TileMatrixSetId}/{z}/{x}/{y}.{format}", **img_endpoint_params
        )
        #@self.router.get(
        #    r"/tiles/{TileMatrixSetId}/{z}/{x}/{y}@{scale}x", **img_endpoint_params
        #)
        @self.router.get(
            r"/tiles/{TileMatrixSetId}/{z}/{x}/{y}@{scale}x.{format}",
            **img_endpoint_params,
        )
        # pylint:disable=unused-variable
        def tile(
            z: int = Path(..., ge=0, le=30, description="Mercator tiles's zoom level"),
            x: int = Path(..., description="Mercator tiles's column"),
            y: int = Path(..., description="Mercator tiles's row"),
            # tms: TileMatrixSet = Depends(self.supported_tms),
            #scale: Optional[int] = Path(gt=0, lt=4, description="Tile size scale. 1=256x256, 2=512x512..."),
            format: ImageType = Path(description="Type of the item, default is 'terrain'"),
            
            src_path=Depends(self.path_dependency),
            layer_params=Depends(self.layer_dependency),
            dataset_params=Depends(self.dataset_dependency),
            render_params=Depends(self.render_dependency),
            reader_params=Depends(self.reader_dependency),
            backend_params=Depends(self.backend_dependency),
            mosaic_params=Depends(self.mosaic_dependency),
            colormap=Depends(self.colormap_dependency),
            pixel_selection: PixelSelectionMethod = Query(
                PixelSelectionMethod.first, description="Pixel selection method."
            ),
            env=Depends(self.environment_dependency),
            # kwargs: Dict = Depends(self.additional_dependency),
        ):
            # pylint:disable=unused-argument
            """Create map tile from a COG."""
            timings = []
            headers: Dict[str, str] = {}

            tilesize = 1 * 256 # scale * 256

            threads = int(os.getenv("MOSAIC_CONCURRENCY", MAX_THREADS))
            with Timer() as t:
                with rasterio.Env(**env): #(**self.gdal_config):
                    with self.backend( # .reader
                        src_path,
                        reader=self.dataset_reader,
                        #reader_options=self.reader_options.as_dict(),
                        reader_options=reader_params.as_dict(),
                        **backend_params.as_dict(),
                        **mosaic_params.as_dict() # **mosaic_params.kwargs,
                    ) as mosaic_source:
                        # Normally this block would just call `mosaic_source.tile`
                        # However we copy the definition of `tile()` so that we
                        # can separately time how long it takes to make the STAC
                        # API query and how long it takes to fetch the actual
                        # image data
                        # tile implementation copied from
                        # https://github.com/developmentseed/cogeo-mosaic/blob/0e5828e0a907cef535ff07000b0936fa91933f6e/cogeo_mosaic/backends/base.py#L142-L157

                        mosaic_assets = mosaic_source.assets_for_tile(x, y, z)
                        if not mosaic_assets:
                            raise NoAssetFoundError(
                                f"No assets found for tile {z}-{x}-{y}"
                            )

                        mosaic_read = t.from_start
                        timings.append(("mosaicread", round(mosaic_read * 1000, 2)))

                        def _reader(
                            asset: str, x: int, y: int, z: int, **kwargs: Any
                        ) -> ImageData:
                            """Helper function called on each asset within mosaic_reader

                            In this case, this is the value of self.dataset_reader above
                            passed to `reader`, which is STACReader
                            """
                            with mosaic_source.reader(
                                asset, **mosaic_source.reader_options
                            ) as stac_dataset:
                                return stac_dataset.tile(x, y, z, **kwargs)
                            
                        print('--- Before mosaic_reader')
                        print(PixelSelectionMethod.first)

                        data, _ = mosaic_reader(
                            mosaic_assets,
                            _reader,
                            x,
                            y,
                            z,
                            #pixel_selection=PixelSelectionMethod.first, #pixel_selection.method(),
                            tilesize=tilesize,
                            threads=threads,
                            **layer_params.as_dict(),
                            **dataset_params.as_dict(),
                            #**kwargs,
                        )

                        print('--- After mosaic_reader')

            timings.append(("dataread", round((t.elapsed - mosaic_read) * 1000, 2)))

            # format = 'npy'
            if not format:
                format = ImageType.jpeg if data.mask.all() else ImageType.png

            with Timer() as t:
                print('--- Before post_process')
                print(render_params)

                image = data.post_process(
                    in_range=render_params.rescale, # rescale_range,
                    color_formula=render_params.color_formula,
                )
            timings.append(("postprocess", round(t.elapsed * 1000, 2)))

            with Timer() as t:
                content = image.render(
                    # add_mask=render_params.add_mask, # return_mask,
                    img_format=format.driver,
                    colormap=colormap,
                    **format.profile,
                    **render_params.as_dict(),
                )
            timings.append(("format", round(t.elapsed * 1000, 2)))

            if OptionalHeader.server_timing in self.optional_headers:
                headers["Server-Timing"] = ", ".join(
                    [f"{name};dur={time}" for (name, time) in timings]
                )

            if OptionalHeader.x_assets in self.optional_headers:
                headers["X-Assets"] = ",".join(data.assets)

            return Response(content, media_type=format.mediatype, headers=headers)
