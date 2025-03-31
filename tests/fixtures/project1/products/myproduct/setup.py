from meshroom.decorators import setup_consumer
from meshroom.model import Plug


@setup_consumer("events", format="ecs")
def setup_consumer_for_events():
    pass


@setup_consumer("stuff", title="Make magic happen", mode="pull", owns_both=True)
def setup_pull_consumer_for_stuff(plug: Plug):
    plug.set_secret("youpi", "42")
