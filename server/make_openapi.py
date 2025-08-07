"""Generate OpenAPI spec without starting server."""

import json
from pathlib import Path

import click


@click.command()
@click.option('--output', help='Output file path', default='/tmp/openapi.json')
def main(output: str) -> None:
  """Generate OpenAPI spec to file."""
  try:
    # Import the FastAPI app
    from server.app import app

    # Generate OpenAPI spec
    openapi_spec = app.openapi()

    # Write to file
    output_path = Path(output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w') as f:
      json.dump(openapi_spec, f, indent=2)

    print(f'OpenAPI spec written to {output}')

  except Exception as e:
    print(f'Error generating OpenAPI spec: {e}')
    raise


if __name__ == '__main__':
  main()
