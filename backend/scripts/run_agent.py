import asyncio

from app.services.agent import AgentRunner


async def main() -> None:
    runner = AgentRunner()

    total = 0
    while True:
        res = await runner.run_tick()
        print(
            f"tick: claimed={res.claimed} resolved={res.succeeded} "
            f"escalated={res.escalated} failed={res.failed}"
        )
        total += res.claimed
        if res.claimed == 0:
            break

    print(f"done: total_claimed={total}")


if __name__ == "__main__":
    asyncio.run(main())

