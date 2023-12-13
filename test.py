import asyncio


async def fetch_data():
    print("Start fetching")
    await asyncio.sleep(2)  # Simuliert eine IO-Aufgabe
    print("Done fetching")
    return {'data': 123}


async def print_numbers():
    for i in range(10):
        print(i)
        await asyncio.sleep(1)


async def main():
    # Starte beide Coroutinen
    task1 = asyncio.create_task(fetch_data())
    task2 = asyncio.create_task(print_numbers())

    # Warte bis beide Aufgaben abgeschlossen sind
    await task1
    await task2


# Starte den Event-Loop
asyncio.run(main())
