# meshroom add

!!! Usage
    **meshroom add** [OPTIONS] PRODUCT [NAME]


Add a new Instance to the mesh for a given Product.

You may optionnally specify a `[NAME]`. If not, the new Instance will get the same name as its Product.

The new instance's configuration will by saved to `products/<PRODUCT>/[NAME]/config.yml` in your meshroom project tree.

### Options

option | description
--- | ---
  -s, --read-secret TEXT | Read a one-line secret from stdin (can be supplied multiple times to read several secrets, one per line)
