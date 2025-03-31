from bs4 import BeautifulSoup
from pydantic import BaseModel, Field
import requests
from sekoia_automation.module import Module
from sekoia_automation.action import GenericAPIAction


class ExampleModuleConfiguration(BaseModel):
    """Configuration for the ExampleModule"""

    url: str = Field("api.example.com", description="The URL of the cloud instance")
    api_key: str = Field(secret=True, description="Some secret API key to mimic authentication to the cloud instance")


class ExampleModule(Module):
    """Sekoia.io automations shall belong to a module"""

    # A module shall declare a Pydantic model for its configuration
    configuration: ExampleModuleConfiguration


class ExampleAction(GenericAPIAction):
    """An Action is a python code calling 3rd-party APIs or services and returning data to Sekoia.io"""

    module: ExampleModule
    product_name: str

    def run(self, arguments) -> dict:
        """Here is demonstrated an Action that pull the 10 latest published vulnerabilities from https://www.cisa.gov/known-exploited-vulnerabilities-catalog"""

        doc = BeautifulSoup(requests.get("https://www.cisa.gov/known-exploited-vulnerabilities-catalog").text, "html.parser")
        vulnerabilities = []
        for a in doc.select("article h3 a"):
            try:
                url = a.get("href")
                vulnerabilities.append(
                    {
                        "url": url,
                        "cve": url.split("id=")[-1],
                        "name": a.parent.parent.select_one(".c-teaser__vuln-name").text.strip(),
                        "description": a.parent.parent.select_one(".c-teaser__vuln-name span").getText(separator="\n"),
                    }
                )
                if len(vulnerabilities) >= 10:
                    break
            except Exception as e:
                self.log(str(e))
        return {
            "items": vulnerabilities,
            "total": len(vulnerabilities),
        }


if __name__ == "__main__":
    module = ExampleModule()
    # You must register the action to the module
    module.register(ExampleAction, "example_action")
    module.run()
