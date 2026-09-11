import asyncio

from backend.data_runtime.factory import create_file_runtime
from backend.data_runtime.profiling.profiler import DatasetProfiler


async def main():
    runtime = create_file_runtime(
        "src/data/example.csv"
    )

    await runtime.connect()

    try:
        print("\n=== SCHEMA ===")

        schema = await runtime.schema()
        print(schema)
        print("\n=== SAMPLE ===")
        sample = await runtime.sample(5)
        for row in sample.rows:
            print(row)

        print("\n=== QUERY ===")
        result = await runtime.query(
            """
            SELECT *
            FROM data
            LIMIT 5
            """
        )

        print(result)
        print("\n=== PROFILE ===")

        profiler = DatasetProfiler(runtime)
        profile = await profiler.profile()

        print(profile)

    finally:
        await runtime.close()


if __name__ == "__main__":
    asyncio.run(main())
