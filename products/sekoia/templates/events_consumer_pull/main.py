import asyncio
from datetime import timedelta, datetime
from pydantic import BaseModel, Field
from sekoia_automation.module import Module
from sekoia_automation.aio.connector import AsyncConnector
from sekoia_automation.checkpoint import CheckpointDatetime


class ExampleModuleConfiguration(BaseModel):
    """Configuration for the ExampleModule"""

    url: str = Field("api.example.com", description="The URL of the cloud instance")
    api_key: str = Field(secret=True, description="Some secret API key to mimic authentication to the cloud instance")


class ExampleModule(Module):
    """Sekoia.io automations shall belong to a module"""

    # A module shall declare a Pydantic model for its configuration
    configuration: ExampleModuleConfiguration


class ExampleConnectorConfiguration(BaseModel):
    """Configuration for the ExampleConnector"""

    frequency: int = Field(2, description="The frequency in seconds to pull the events")
    message: str = Field(default="hello", description="Whatever message you want to forward")


class ExampleConnector(AsyncConnector):
    """A connector is a daemon that pulls data from a source and pushes it to an intake"""

    module: ExampleModule
    configuration: ExampleConnectorConfiguration

    product_name: str

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

        # TODO: Initialize any required checkpoint
        self.last_event_date = CheckpointDatetime(
            path=self.data_path,
            start_at=timedelta(days=7),
            ignore_older_than=timedelta(days=7),
        )

    async def async_run(self) -> None:  # pragma: no cover
        """Here is demonstrated an asyncio connector that pushes dummy data every :frequency seconds"""

        # TODO: Rewrite with your own pull logic
        while self.running:
            # You may use the push_data_to_intakes facility to push events to the intakes endpoint
            await self.push_data_to_intakes(
                [
                    {
                        "@timestamp": datetime.utcnow().isoformat(),
                        "host": {"name": "example.com"},
                        "message": self.configuration.message,
                    }
                ]
            )
            await asyncio.sleep(self.configuration.frequency)
            self.last_event_date.offset = datetime.utcnow()

    def run(self) -> None:  # pragma: no cover
        loop = asyncio.get_event_loop()
        loop.run_until_complete(self.async_run())


if __name__ == "__main__":
    module = ExampleModule()
    # You must register the connector to the module
    module.register(ExampleConnector, "example_connector")
    module.run()
