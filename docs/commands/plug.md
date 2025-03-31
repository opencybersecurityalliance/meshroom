# meshroom plug

!!! Usage
    **meshroom plug** [OPTIONS] TOPIC SRC_INSTANCE DST_INSTANCE

Create a Plug between two instances. A compatible producer/consumer or trigger/executor pair of integrations must exist on the corresponding source and destination products for the given topic. Such mathcing integrations may be either:
* explicitly implemented as integrations with setup hooks having `own_both=False`
* explicitly implemented as an integration with a setup hook having `own_both=True` by one of the products
* implicitly defined via generic setup hooks on one or both products.

!!! Note
   This doesn't setup the corresponding interop to your real product instance yet, it simply add its declaration to the project, ready for a subsequent `meshroom up`.

### Options

option | description
--- | ---
--mode [push\|pull] | Force the given plug operation mode
