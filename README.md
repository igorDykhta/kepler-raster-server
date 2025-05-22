# Kepler Raster Server

A raster tile server built on top of [TiTiler](https://github.com/developmentseed/titiler), providing terrain mesh and STAC mosaic capabilities.

> This project is an extension of [TiTiler](https://github.com/developmentseed/titiler) by Development Seed. All TiTiler licenses and attributions apply to this project.

## Features

- **Terrain Mesh Generation**: Generate quantized mesh terrain tiles for 3D visualization
- **STAC Mosaic Support**: Dynamic STAC API integration for tile serving

## Installation

### Local Development

1. Clone the repository:

```bash
git clone https://github.com/yourusername/kepler-raster-server.git
cd kepler-raster-server
```

2. Build and run with Docker:

```bash
# Enable Docker BuildKit for better caching
export DOCKER_BUILDKIT=1
docker-compose up --build titiler
```

The raster tile server will be available at `http://localhost:8000` and can be used to setup a raster tile layer in kepler.gl.

## API Endpoints

### Terrain Mesh

- `/mesh/tiles/{z}/{x}/{y}.terrain` - Get terrain mesh tiles
- `/mesh/tiles/{z}/{x}/{y}@{scale}x.terrain` - Get scaled terrain mesh tiles

### STAC Mosaic

- `/stac/mosaic/tiles/{z}/{x}/{y}.{format}` - Get mosaic tiles
- `/stac/mosaic/tiles/{z}/{x}/{y}@{scale}x.{format}` - Get scaled mosaic tiles

## Deployment

### AWS Lambda Deployment

Follow the [TiTiler AWS Lambda deployment guide](https://developmentseed.org/titiler/deployment/aws/lambda/) for serverless deployment. Note that you'll need enough concurency to support lambda instance per request. In kepler.gl it's at this moment the limit is 6 per server (or 12 when elevation meshes are enabled).

### Publishing to PyPI

To publish a new version to PyPI:

1. Update the version in `pyproject.toml`
2. Run the publish script:

```bash
./scripts/publish.sh
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

### Attribution

This project is built on top of [TiTiler](https://github.com/developmentseed/titiler) by Development Seed, which is also licensed under the MIT License. All TiTiler licenses and attributions apply to this project.

## Credits

- [TiTiler](https://github.com/developmentseed/titiler) by Development Seed - The base tile server implementation
- [Development Seed](https://developmentseed.org/) - For their excellent work on TiTiler and related geospatial tools
