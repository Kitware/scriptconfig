# Changelog

This changelog follows the specifications detailed in: [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).
This project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html), although we have not yet reached a `1.0.0` release.


## Version 0.9.0 - Unreleased

### Added
* SubConfig support for nested Config/DataConfig trees with selector-aware CLI parsing and nested overrides.

### Changed
* Replace OrderedDict usage with standard dicts across the codebase.
* Move type annotations into implementation modules and remove stub files.
* Remove `scfg_isinstance` autoreload checks and use standard `isinstance`.
* Normalize Config/DataConfig defaults at class creation to ensure Value/SubConfig metadata is present.

### Fixed
* Corner case for BooleanFlagOrKeyValAction, only smartcast if type is not specified
* BooleanFlagOrKeyValAction will now error if you use it with positional arguments to prevent unintended usage.
* Resolve mypy typing issues in config, modal, and argparse helpers.
* Config inheritance now uses python class MRO composition rules (i.e. new defaults do not overwrite previous ones). This change is backwards incompatible, but is likely not externally used.


## Version 0.8.4 - Released 2025-10-10

### Added

* Add expose Value help property
* Added scriptconfig CLI that helps generate templates
* Modal register can now take command, alias, and group as an argument to control behavior for different modals.
* Modals can now handle opaque CLIs

### Changed
* Loaded YAML configs can now contain top level dunder or dotted keys that are
  ignored by the strict parser, which can be useful for YAML anchors.
* Config load can now use JSON or YAML.
* Can now specify `--config` as raw YAML / JSON text
* Added an internal diagnostics module.
* When specifying modal CLI attributes, the name of the class attribute is the
  default the command name for the modal CLI unless __command__ is specified.
* Modal CLIs now print the deepest usage on errors

### Fixed
* dump with json mode now works.
* help and text markup is now disabled, which prevents rendering issues when `rich_argparse` is versus isn't installed.
* Fix issue with type "smartcast:v1" not being respected
* Issue with nested modals where they did not correctly show errors when given submodals with no commands
* Disabled version handling in modal, which was causing issues, might cause different issues now.


## Version 0.8.2 - Released 2025-03-06

### Added

* The "type" of a `Value` can now be set to "smartcast:legacy" for explicit old behavior or "smartcast:v1" for the new candidate behavior.

### Changed

* The `Value` class can now take `default` as a keyword argument for better
  interoperability with argparse. We may remove the `value` keyword in the
  future in favor of this.

* The `smartcast` `allow_split` now works, and defaults to "auto", which will prepare us for a backwards incompatible change to remove the auto string split behavior.

### Fixed

* Fix issue with internal argparse change in CPython#125355


### Added
* Add experimental new method `DataConfig.cls_from_argparse` which dynamically
  creates a scriptconfig object from an existing argparse object. Some advanced
  argparse options may not be supported.


## Version 0.8.1 - Released 2024-10-18

### Added

* New convenience arguments to `.cli`
* Support for 3.13


## Version 0.8.0 - Released 2024-08-14

### Add
* Add experimental new flag `__allow_newattr__` which relaxes the constraint
  that you can't add keys on the fly.

### Removed

* Remove 3.6 and 3.7 support


### Fix:
* Fixed the `define` method.
* Initial implementation of `port_from_click`


## Version 0.7.15 - Released 2024-05-13

### Added
* Allow special options to be passed to cli

## Version 0.7.14 - Released 2024-04-15

### Changed
* Better error messages when parsing argv
* Add a docstring to `DataConfig`


## Version 0.7.13 - Released 2024-03-19

### Fixed
* Fix issue caused by a CPython patch https://github.com/python/cpython/pull/115674


## Version 0.7.12 - Released 2024-03-19

### Fixed
* Fixed issue of porting to argparse when object contained non-wrapped default values.

### Changed
* `scfg.Flag` no longer errors if isflag is set to a truthy value.
* Rename `port_argparse` as `port_from_argparse` (old method still exists as an alias, but will be deprecated).


## Version 0.7.11 - Released 2023-11-16

### Added
* New `port_to_argparse` method that will generate text for a nearly equivalent
  argparse version of the config object.

* Can now set `isflag='counter'` to get a variable that will increment on
  multiple specifications of the flag.

* Added `__allow_abbrev__` control option.

### Changed
* Quality of life updates to ModalConfig, autocomplete flag, 
* Modified ubelt repr to be more executable
* Added `util` submodule. 

### Fixed
* The `.cli` classmethod no longer causes `__post_init__` to be called twice.


## Version 0.7.10 - Released 2023-07-09

### Changed
* Reduced import time
* Better handling of nested modal CLIs


## Version 0.7.9 - Released 2023-06-05

### Added
* New alternate (more concise) syntax for declaring Modal CLIs


### Changed
* Change `ModalCLI.run` to `ModalCLI.main`


## Version 0.7.8 - Released 2023-05-08

### Changed

* Autogenerate DataConfig `__init__` docstrings

* Added `__dir__` to DataConfig.

* DataConfig `__setattr__` only forwards to the config for keys that are not
  prefixed with underscores. (i.e. the user can now use underscore prefixed
  attributes on DataConfig instances without modifying the config dictionary
  itself).


### Fixed

* Issue on Python 3.9 where staticmethods would be added to the DataConfig defaults.


## Version 0.7.7 - Released 2023-04-10

### Added
* Convenience class: Flag

### Changed
* Help formatting no longer displays redundant fuzzy hyphen options 
* `Config.__fuzzy_hyphens__` now defaults to True
* `Config.cli` now defaults to `strict=True`.
* Add `tag` field to `Value`.


## Version 0.7.6 - Released 2023-04-04

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
