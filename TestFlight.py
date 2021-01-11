from mavsdk import System

import asyncio


async def run():
    drone = System()
    await drone.connect(system_address="udp://:14540")
    
    print('Waiting for drone to connect...')
    async for state in drone.core.connection_state():
        if state.is_connected:
            print(f"Drone Discovered with UUID: {state.uuid}")
            break
        
        
    print_altitude_task = asyncio.ensure_future(print_altitude(drone))
    print_flight_mode_task = asyncio.ensure_future(print_flight_mode(drone))

    running_tasks = [print_altitude_task, print_flight_mode_task]
    termination_task = asyncio.ensure_future(observe_is_in_air(drone, running_tasks))
    
    print("--Arming")
    await drone.action.arm()
    
    print("Taking off..")
    await drone.action.takeoff()
    
    await asyncio.sleep(10)
    
    print("Landing...")
    await drone.action.land()
    
    await termination_task
    
    
async def print_altitude(drone):
    previous_altitude = None
    
    async for position in drone.telemetry.position():
        altitude = round(position.relative_altitude_m)
        if altitude != previous_altitude:
            previous_altitude = altitude
            print(f"Altitude: {altitude}")
            
            
async def print_flight_mode(drone):
    async for flight_mode in drone.telemetry.flight_mode():
        if flight_mode is not previous_flight_mode:
            previous_flight_mode = flight_mode
            print(f"Flight mode: {flight_mode}")
            
async def observe_is_in_air(drone, running_tasks):
    async for is_in_air in drone.telemetry.in_air():
        
        if is_in_air:
            was_in_air = is_in_air
        
        if was_in_air and not is_in_air:
            for task in running_tasks:
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
            await asyncio.get_event_loop().shutdown_asyncgens()
            return

if __name__ == "__main__":
    asyncio.get_event_loop().run_until_complete(run())
        
        
        
        
        
    