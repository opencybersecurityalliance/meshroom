from meshroom.decorators import setup_consumer
from meshroom.model import Integration, Plug, Instance


@setup_consumer("events", order="first")
def setup_events_consumer(integration: Integration, plug: Plug, instance: Instance):
    # TODO
    #
    # Write here the setup code to create a {{name}} consumer receiving events
    #
    # You may use plug.get_secret(...) to retrieve secrets setup on the plug
    # and instance.get_secret(...) to retrieve secrets setup on your {{name}} instance
    #
    # You may also use plug.src_settings and plug.dst_settings to retrieve settings
    # set by the user when `meshroom plug` was called
    print("Not implemented yet, do nothing !")
