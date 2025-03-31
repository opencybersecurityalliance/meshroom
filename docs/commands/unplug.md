# meshroom unplug

!!! Usage
    **meshroom unplug** [OPTIONS] TOPIC SRC_INSTANCE DST_INSTANCE

Removes a plug between two instances.

!!! Note
   This doesn't unprovision the corresponding interop, it simply removes its declaration from the project.

### Options

option | description
--- | ---
--mode [push\|pull] | Restrict to the plug that uses the given operation mode
