# meshroom configure

!!! Usage
    **meshroom configure** [OPTIONS] INSTANCE

Reconfigure an existing Instance, prompting for the settings and secrets declared by its Product definition.

### Options

option | description
---- | ----
-s, --read-secret TEXT | Read a one-line secret from stdin (can be supplied multiple times to read several secrets, one per line)
