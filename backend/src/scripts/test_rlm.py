import asyncio
from pathlib import Path

from backend.data_runtime.factory import create_file_runtime
from backend.rlm import (
    AnalysisTools,
    RLMConfig,
    RLMEngine,
    ToolRegistry,
)
from backend.services.agent import create_provider


async def main():
    data_path = Path("src/data/Sales_Product_Combined.csv")
    if not data_path.exists():
        raise FileNotFoundError(
            f"Example dataset not found at {data_path}"
        )

    runtime = create_file_runtime(str(data_path))
    await runtime.connect()

    try:
        tools = AnalysisTools(runtime)
        registry = ToolRegistry(tools)
        provider = create_provider()

        engine = RLMEngine(
            provider=provider,
            tool_registry=registry,
            config=RLMConfig(max_iterations=30),
        )

        async def on_step(step):
            print(f"\n[{step.iteration}] {step.type.value}")
            print(step.content)

        result = await engine.run(
            question=(
                "Explain graphs in python"
                # "What are the most sold product"
                # "How many sales order were created grouped on ORDERDATE"
                # "What are the most important "
                # "trends in this dataset?"
                # "Who is the prime minister of India"
            ),
            on_step=on_step,
        )

        print("\nFINAL ANSWER")
        print(result.answer)
    finally:
        await runtime.close()


if __name__ == "__main__":
    asyncio.run(main())
