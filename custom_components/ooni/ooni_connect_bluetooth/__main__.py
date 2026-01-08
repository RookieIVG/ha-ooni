import anyio
import sys
import asyncclick as click
from bleak import (
    BleakClient,
    BleakScanner,
)
from bleak.backends.characteristic import BleakGATTCharacteristic
from bleak.backends.device import BLEDevice
from bleak.backends.scanner import AdvertisementData
from bleak.uuids import uuidstr_to_str

from .const import MainService, ManufacturerData
from .exceptions import DecodeError
from .packets import (
    PacketNotify,
)
from .services import Characteristic, NotifyCharacteristic


@click.group()
async def cli():
    pass


def main():
    try:
        cli()
    except KeyboardInterrupt:
        pass

@cli.command()
@click.option("--host", default="0.0.0.0", help="Host to bind the server to")
@click.option("--port", default=8000, help="Port to bind the server to")
async def webserver(host: str, port: int):
    """Start the web server for monitoring the thermometer"""
    import uvicorn
    from .webserver import app
    
    click.echo(f"Starting webserver on http://{host}:{port}")
    config = uvicorn.Config(app, host=host, port=port, log_level="info")
    server = uvicorn.Server(config)
    await server.serve()


@cli.command()
async def scan():
    click.echo("Scanning for devices")

    devices = set()

    def detected(device: BLEDevice, advertisement: AdvertisementData):
        if device not in devices:
            if device.name != "Ooni_DT_Hub":
                return
            print("Address: ", device.address)
            print("advertisement received:", advertisement)
            print("*Advertisement uuid: ", advertisement.service_uuids)
            # if MainService.uuid not in advertisement.service_uuids:
            #     return
            devices.add(device)

        click.echo(f"Device: {device}")
        for service in advertisement.service_uuids:
            click.echo(f" - Service: {service} {uuidstr_to_str(service)}")
        click.echo(f" - Data: {advertisement.service_data}")
        click.echo(f" - Manu: {advertisement.manufacturer_data}")

        if data := advertisement.manufacturer_data.get(ManufacturerData.company):
            decoded = ManufacturerData.decode(data)
            click.echo(f" -     : {decoded}")

        click.echo(f" - RSSI: {advertisement.rssi}")
        click.echo()
        sys.exit(0)

    # async with BleakScanner(detected, service_uuids=[MainService.uuid]):
    async with BleakScanner(detected):
        await anyio.sleep_forever()

@cli.group(chain=True)
@click.argument("address")
@click.option("--code", default="")
@click.pass_context
async def connect(ctx: click.Context, address: str, code: str):
    click.echo(f"Connecting to: {address} ...", nl=False)
    client = await ctx.with_async_resource(BleakClient(address, timeout=20))
    ctx.obj = client
    click.echo(" Done")

    def notify_data(char_specifier: BleakGATTCharacteristic, data: bytearray):
        try:
            packet_data = NotifyCharacteristic.decode(data)
            packet = PacketNotify.decode(packet_data)
            click.echo(f"battery={packet.battery}, ambient_a={packet.ambient_a}, ambient_b={packet.ambient_b}, probe_p1={packet.probe_p1}, probe_p2={packet.probe_p2}")
        except DecodeError as exc:
            click.echo(f"Failed to decode: {data.hex()} with error {exc}")

    await client.start_notify(MainService.notify.uuid, notify_data)

@connect.command()
@click.pass_obj
async def list(client: BleakClient):
    for service in client.services:
        click.echo(f"Service: {service}")

        async def read_print(char: BleakGATTCharacteristic):
            parser = Characteristic.registry.get(char.uuid)
            if "read" in char.properties:
                data = await client.read_gatt_char(char.uuid)
            else:
                data = None
            click.echo(f" -  {char}")
            click.echo(f" -  {char.properties}")
            if data is not None and parser:
                click.echo(f" -  Data: {parser.decode(data)}")

        async with anyio.create_task_group() as tg:
            for char in service.characteristics:
                tg.start_soon(read_print, char)


@connect.command()
async def wait():
    click.echo("Waiting")
    await anyio.sleep_forever()



if __name__ == "__main__":
    main()
