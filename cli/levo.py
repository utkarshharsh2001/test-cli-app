import click
import requests
import json
import os
from pathlib import Path
from typing import Optional

API_BASE_URL = "http://localhost:8000/api/v1"

@click.group()
def cli():
    """Levo CLI for OpenAPI schema management"""
    pass

@cli.command('import')
@click.option('--spec', required=True, type=click.Path(exists=True),
              help='OpenAPI schema file (JSON/YAML)')
@click.option('--application', required=True,
              help='Target application name')
@click.option('--service', help='Service name (optional)')
@click.option('--replace', is_flag=True, help='Replace existing schema')
def import_command(spec: str, application: str, service: Optional[str], replace: bool):
    """Import OpenAPI schema"""

    print(f"Importing {spec}...")

    spec_path = Path(spec)
    if spec_path.suffix.lower() not in ['.json', '.yaml', '.yml']:
        click.echo("Error: File must be JSON or YAML", err=True)
        return

    try:
        with open(spec_path, 'rb') as f:
            files = {'file': (spec_path.name, f)}
            data = {
                'application': application,
                'replace_existing': replace
            }
            if service:
                data['service'] = service

            response = requests.post(f"{API_BASE_URL}/schemas/upload", files=files, data=data)

            if response.status_code == 200:
                result = response.json()
                if result.get('success'):
                    print(f"Success! Version {result.get('version', '?')}")
                    if result.get('message'):
                        print(result['message'])
                else:
                    click.echo(f"Failed: {result.get('message', 'Unknown error')}", err=True)
            else:
                # TODO: better error handling here
                click.echo(f"HTTP {response.status_code}: {response.text}", err=True)

    except requests.ConnectionError:
        click.echo("Cannot connect to server (is it running?)", err=True)
    except FileNotFoundError:
        click.echo(f"File not found: {spec}", err=True)
    except Exception as e:
        click.echo(f"Unexpected error: {e}", err=True)

@cli.command()
@click.option('--application', required=True, help='Application to test')
@click.option('--service', help='Specific service')
@click.option('--version', type=int, help='Schema version')
def test(application: str, service: Optional[str], version: Optional[int]):
    """Test application schema"""

    print(f"Testing {application}...")

    try:
        if version:
            # TODO: implement version-specific testing
            print(f"Version-specific testing not implemented yet")
            return

        params = {'application': application}
        if service:
            params['service'] = service

        resp = requests.get(f"{API_BASE_URL}/schemas/latest", params=params)

        if resp.status_code != 200:
            if resp.status_code == 404:
                click.echo("No schema found", err=True)
            else:
                click.echo(f"API error: {resp.status_code}", err=True)
            return

        data = resp.json()
        schema_info = data.get('schema_info', {})

        print(f"Found schema v{schema_info.get('version', 'unknown')}")
        print(f"File: {schema_info.get('file_name', 'N/A')}")

        # Get actual schema content
        schema_id = schema_info.get('id')
        if schema_id:
            content_resp = requests.get(f"{API_BASE_URL}/schemas/{schema_id}/content")
            if content_resp.status_code == 200:
                content = content_resp.json().get('content', {})

                info = content.get('info', {})
                print(f"API: {info.get('title', 'Untitled')}")
                print(f"Version: {info.get('version', 'N/A')}")

                paths = content.get('paths', {})
                print(f"Endpoints: {len(paths)}")

                print("Schema validation OK")
            else:
                print("Warning: Could not fetch schema content")

    except requests.ConnectionError:
        click.echo("Connection failed", err=True)
    except KeyError as e:
        click.echo(f"Invalid response format: missing {e}", err=True)
    except Exception as e:
        click.echo(f"Error: {e}", err=True)

@cli.command('list')
@click.option('--application', help='Show versions for specific app')
@click.option('--service', help='Filter by service name')
def list_schemas(application: Optional[str], service: Optional[str] = None):
    """List schemas"""

    try:
        if application:
            params = {'application': application}
            if service:
                params['service'] = service
            resp = requests.get(f"{API_BASE_URL}/schemas/versions", params=params)

            if resp.status_code == 404:
                print(f"No schemas for '{application}'")
                return
            elif resp.status_code != 200:
                click.echo(f"Error {resp.status_code}", err=True)
                return

            versions = resp.json()
            print(f"Versions for {application}:")
            for v in versions:
                marker = "*" if v.get('is_latest') else " "
                print(f"  {marker} v{v.get('version')} - {v.get('file_name')} ({v.get('created_at', 'unknown')})")
        else:
            resp = requests.get(f"{API_BASE_URL}/applications")
            if resp.status_code == 200:
                apps = resp.json()
                print("Applications:")
                for app in apps:
                    desc = f" - {app.get('description')}" if app.get('description') else ""
                    print(f"  {app.get('name', 'unnamed')}{desc}")
            else:
                click.echo("Failed to fetch applications", err=True)

    except requests.ConnectionError:
        click.echo("Cannot connect to API", err=True)
    except Exception as e:
        print(f"Error: {e}")

if __name__ == '__main__':
    cli()
