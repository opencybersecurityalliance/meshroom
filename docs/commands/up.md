# meshroom up

!!! Usage
    **meshroom up** [OPTIONS] [INSTANCE] [TARGET_INSTANCE] [TOPIC]
                   [[push|pull]]

Setup all declared Instances, a single Instance or a single Plug, depending on the optional parameters passed.
Instances and Plugs are setup according to their `@setup` hooks:
* Plugs in push mode leveraging two integrations with no `owns_both=True` hooks will setup the consumer first, then the producer
* Plugs in pull mode leveraging two integrations with no `owns_both=True` hooks will setup the prducer first, then the consumer
* Plugs having a `owns_both=True` hook set on one of their integrations will setup this sole integrations, since `owns_both=True` tells the hooked product is responsible for setting up the whole link without configuring anything explicit on the 3rd-party instance.
