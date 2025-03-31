# meshroom watch

!!! Usage
    **meshroom watch** [OPTIONS] TOPIC INSTANCE [DST_INSTANCE]

Inspect data flowing through a Plug or a Instance.

If `DST_INSTANCE` is passed, data flowing through the plug from `INSTANCE` to `DST_INSTANCE` on the `TOPIC` will be printed, one record per line.

If `DST_INSTANCE` is unset, every message flowing to the `INSTANCE` for topic `TOPIC` (whichever the source of it) will be printed.

### Options

option | description
--- | ---
--mode [push\|pull] | Restrict watch to plugs with the given operation mode
