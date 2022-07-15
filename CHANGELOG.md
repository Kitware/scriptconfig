# Changelog

This changelog follows the specifications detailed in: [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).
This project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html), although we have not yet reached a `1.0.0` release.


## Version 0.6.2 - Unreleased


## Version 0.6.1 - Released 2022-07-14

### Changed
* Added type information
* Doc improvements


## Version 0.6.0 - Released 2022-06-09

### Added 
* `smartcast` can now disable splitting by specifying `allow_split=False`
* ### Broken: Added `required` as an option to `Value`.

* The `short_alias` keyword to `Value`, which allows single '-' prefix chars on
  the command line.

* The `port_argparse` method which takes an existing (simple) argparse CLI and
  attempts to make a scriptconfig version of it.

### Changed
* The `alias` keyword no expands a single argparse argument instead of making
  multiple of them.
* Make numpy optional


## Version 0.5.8 - Released 2021-05-19

### Added
* Can now specify alias for a Value as a `str | List[str]`.

### Changed
* Arguments can now be specified as both positional and keyword. The keyword
  variant will always take priority.

* Changed the way arguments are smart-casted when specified on the commandline

### Fixed

* Bug when setting a value to None via the command line


## Version 0.5.7 - 2020-08-26

### Added
* The `cmdline` argument of `Config` can now be the actual argument string used
  on the command line. This will be parsed with shlex and converted to an argv
  list.

### Fixes
* Fixed issue where `_read_argv` would try to smartcast items where the default
  class attribute had a `Value`. 


### Changed
* The Value object now has a side effect free `cast` method that is called by
  `update` when the default value is changed or when handling raw data outside
   of the Value object itself.


## Version 0.5.6 - Released

### Fixes
* Security fix, smartcast now uses `ast.literal_eval` instead of `eval`.


## Version 0.5.5 - Released

### Added
* Config objects can now have an "epilog" attribute. 


## [Version 0.5.4] - Released

### Added
* scfg.Value can now store a position attribute, which specifies it as a positional argument.
* scfg.Value now accepts `nargs` to handle argparse cases.


## [Version 0.5.3] - 2020-01-30


### Fixed
* calling `set(config)`
* `smartcast` now correctly casts things like `"[1,2,3,]"` to `[1, 2, 3]`


## [Version 0.5.2] - Released

### Added

* `Config.to_dict` to have a method consistent with pandas API

### Changed

* Loading from a config yaml file will ignore the special `__heredoc__` key. 
  This lets the user add multi-line documentation to their config files.


## [Version 0.5.1] - Released

### Fixed 
* Tests on windows


## [Version 0.5.0] - Released 2019-11-05

### Changed 
* Obtained public release approval, first public release.

### Removed
* Removed exposed internal functions from the top level API


## [Version 0.4.0]

### Changed
* Reworked load
* Separate out requirements

### Added
* Add docs

### Fixed
* fixed `cmdline` bugs


## [Version 0.3.0]

### Changed
* Rework imports


## [Version 0.0.1]

### Added
* Add `Config.argparse` and use it internally in load
* Initial implementation
