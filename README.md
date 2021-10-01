# experimentlib

A library of various useful tools for handling laboratory data. This library split off the `experimentserver` project as there was significant overlap between internal functions to record data to a database, and tools necessary to read that data for analysis. Additionally, some components have broader application, such as logging and YAML file handling.

## Noteworthy Modules

### `experimentlib.data.*`

Tools for handling units, gas concentrations and humidity calculations.

### `experimentlib.file.*`

General file handling tools including fetching git hashes for directories and adding paths to the PATH environment variable.

#### `experimentlib.file.yaml`

Tools for loading YAML files with extended syntax through custom constructors:
* `!env` generates a node from environment variables
* `!envreq` as above but raises `` when the variable is not defined
* `!format` generates a formatted string with the following fields available by default
    * `{date}` date string (YYYYMMDD)
    * `{time}` time string (HHMMSS)
    * `{time}` date + time string (YYYYMMDD_HHMMSS)
    * `{timestamp}` integer UNIX epoch timestamp 
    * `{env_*}` environment variables [[0](#sec_footnote)]
    * `{path_user}` path to user home directory (expended from `~`)
    * `{path_temp}` path to temporary directory
    * `{system_hostname}` system fully qualified host name
    * `{system_username}` username
* `!include` reads the specified YAML file and generates a nested node [[0](#sec_footnote)].

### `experimentlib.logging.*`

Sane-default logging setup with additional handlers to push records to InfluxDB (v1.8 or v2) and Pushover.

New logging levels are defined:
* `META` logging events relevant to the logging setup.
* `LOCK` lock acquisition/release debugging
* `TRACE` detailed or verbose debug logging
* `COMM` for external I/O and communication

#### `experimentlib.logging.classes`

Base classes for objects that can use integrated logging.

### `experimentlib.util.*`

Various utility modules.

#### `experimentlib.util.javascript`

A lightweight and naive parser for extracting lists and dictionaries from Javascript code.

---

[<a name="sec_footnote">0</a>]: These methods may present a security risk when passed user-defined strings. While include paths can be restricted through use of the `ExtendedLoader.factory` method, note that sensitive environment variables may be exposed through `{env_*}` entries in formatted strings. In some cases this is necessary to load API keys and the like for logging or other functions and thus it is not restricted.
