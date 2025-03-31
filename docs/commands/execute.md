# meshroom execute

!!! Usage
    **meshroom execute** [OPTIONS] TOPIC INSTANCE [DST_INSTANCE]

Execute an executor exposed by a Plug, either via the plug's source integration's `@trigger` hook, or by directly calling the destination integration's `@execute` hook.
* If the `DST_INSTANCE` is not set, the executor side is triggered by calling its `@execute` hook if defined
* If the `DST_INSTANCE` is set, the trigger side is triggered by calling its `@trigger` hook if defined

If no corresponding hook is defined on the underlying products, this command fails.

### Options

option | description
--- | ---
--mode [push\|pull] | Pick the plug that uses the given operation mode
-p, --param FIELD=VALUE | Pass arguments to the `@execute`/`@trigger` hooks
