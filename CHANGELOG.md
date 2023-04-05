# Changelog

This changelog follows the specifications detailed in: [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).
This project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html), although we have not yet reached a `1.0.0` release.


## Version 0.7.6 - Unreleased

### Added
* ubelt urepr registration
* Config objects can now be inherited 

### Changed

* Help no longer defaults to `<undocumented>`, instead it is just empty.
* Unwrapped values now try to infer if they are a flag.
* The `autocomplete` argument to `.cli` now default to auto


## Version 0.7.5 - Released 2023-03-25

### Changed
* Both `Config` and `DataConfig` now support the `.cli` classmethod and should
  now be the preferred way of creating a `sys.argv` aware instance.

### Fixed
* Issue when specifying `default` to `.cli` or `.load`.


## Version 0.7.4 - Released 2023-03-22

### Changed
* Reworked how the "port" functions work under the hood, and added a new one.
* The `default` and `__default__` class variables are now treated as aliases in Config.
* The `normalize` and `__post_init__` methods are now treated as aliases in Config and DataConfig.
* Deprecated `default` class attribute use `__default__` instead.
* Deprecated `normalize` method, use `__post_init__` instead.

### Fixed:
* Dataconfigs can now be instantiated with aliased kwargs

## Version 0.7.3 - Released 2023-02-15

### Added
* Add `autocomplete` arg for `argcomplete`.
* New `scriptconfig.modal` module with `ModalCLI` class for building modal CLIs
  from multiple scriptconfig objects.

### Fixed
* DataConfig can now define classmethods 


## Version 0.7.2 - Released 2023-02-02
### Added
* `parse_args` and `parse_known_args` methods to Config and DataConfig 

### Changed
* Experimental feature where the CLI can now accept `_` or `-` in sys.argv if `__fuzzy_hyphens__` exists and is truthy
* default, description, and epilog can now be specified with dunder __default__, __description__, and __epilog__ attributes
* Added `cmdline` argument to `DataConfig.cli`
 
### Fixed
* Bug where trying to get a non-existing value raised an AttributeError instead of a KeyError due to aliases
* Fixed issue where using setattr on a DataConfig using a known key did not set its dictionary value.
* Fixed DataConfig issue with aliases
* Issue where `args` contains a `PathLike` object. This is now detected and cast to a string for convenience.


## Version 0.7.1 - Released 2022-09-28

### Added

* Added basic support for groups and mutually exclusive groups by specifying an id in each value.


### Changed

* Options marked as isflag can now accept any type for the key/val style of
  argument. The flag style will still return a boolean.


## Version 0.7.0 - Released 2022-09-17

### Changed

* Flag variables are now accepted on the command line. Variables marked as `isflag` can be specified by either a flag `--varname` or as a key/value pair `--varname=True`.

* The config object now allows aliases to be used in setitem and getitem calls.
  This should be used sparingly.


## Version 0.6.5 - Released 2022-08-25

### Changed
* Config.load can now handle aliased input.

### Fixed
* Fixed bug where argparse attributes were sometimes dropped.


## Version 0.6.4 - Released 2022-08-02

### Changed
* Added a metaclass to DataConfig, which means calling the decorator is no longer necessary.


## Version 0.6.3 - Released 2022-07-22 

### Fixed
* Added workaround for issue with pickle-ability 

## Version 0.6.2 - Released 2022-07-14
### Added
* New method: `to_omegaconf`
* Experimental `dataconf` and `DataConfig`

### Changed
* Can now pass cmdline as a kwargs dict.
* Added support for `required=True` 

### Fixed
* Issue with custom parsers and tracking "explicitly given"


## Version 0.6.1 - Released 2022-06-09

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
