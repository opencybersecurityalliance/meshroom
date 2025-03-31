# meshroom produce

!!! Usage
    **meshroom produce** [OPTIONS] TOPIC INSTANCE [DST_INSTANCE]

  Produce data through a Plug, either using the plug producer's `@produce` hook or directly calling the plug's consumer's `@produce` hook.

### Options

option | description
--- | ---
--mode [push\|pull] | Pick the plug with given operation mode
