# meshroom publish

!!! Usage
    **meshroom publish** [OPTIONS] [PRODUCT] [TARGET_PRODUCT] [TOPIC]
                        [[consumer|producer|trigger|executor]]

Publish a specific integration, a given product's integrations or all
integrations at once to their respective products official integrations catalog,
according to the `@publish` hook defined by their vendors.

### Options

option | description
--- | ---
-m, --mode [push\|pull] | Restrict to integrations of given operation mode
-f, --format TEXT | Restrict to integration conveying the given format
