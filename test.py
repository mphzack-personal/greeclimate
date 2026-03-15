import asyncio
from greeclimate.cloud_discovery import CloudDiscovery

async def main():
    # Create discovery instance
    discovery = CloudDiscovery(
        username='your_email@example.com',
        password='your_password',
        server='Europe'
    )
    
    # Discover devices
    devices = await discovery.scan()
    
    # Create device instance
    device = await discovery.create_device(devices[0])
    await device.bind()
    
    # Control device
    await device.update_state()
    device.power = False
    await device.push_state_update()
    
    # Cleanup
    await device.close()
    await discovery.close()

asyncio.run(main())
