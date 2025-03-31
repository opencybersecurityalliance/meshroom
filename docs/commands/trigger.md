# meshroom trigger

!!! Usage
    **meshroom trigger** [OPTIONS] TOPIC INSTANCE [DST_INSTANCE]

Trigger an trigger exposed by a Plug, either by calling the trigger's `@trigger` hook or directly the executor's `@execute` hooks:
* If the `DST_INSTANCE` is not set, the executor side is triggered by calling its `@execute` hook if defined
* If the `DST_INSTANCE` is set, the trigger side is triggered by calling its `@trigger` hook if defined

If no corresponding hook is defined on the underlying products, this command fails.

### Options

option | description
--- | ---
--mode [push\|pull] | Pick the plug that uses the given operation mode
-p, --param FIELD=VALUE | Pass arguments to the `@execute`/`@trigger` hooks
