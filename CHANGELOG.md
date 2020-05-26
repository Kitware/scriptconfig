# Changelog

This changelog follows the specifications detailed in: [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).
This project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html), although we have not yet reached a `1.0.0` release.


## Version 0.5.6 - Unreleased

### Fixes
* Security fix, smartcast now uses `ast.literal_eval` instead of `eval`.


## Version 0.5.5 - Unreleased

### Added
* Config objects can now have an "epilog" attribute. 


## [Version 0.5.4] - 

### Added
* scfg.Value can now store a position attribute, which specifies it as a positional argument.
* scfg.Value now accepts `nargs` to handle argparse cases.


## [Version 0.5.3] - 2020-01-30


### Fixed
* calling `set(config)`
* `smartcast` now correctly casts things like `"[1,2,3,]"` to `[1, 2, 3]`


## [Version 0.5.2] - Unreleased

### Added

* `Config.to_dict` to have a method consistent with pandas API

### Changed

* Loading from a config yaml file will ignore the special `__heredoc__` key. 
  This lets the user add multi-line documentation to their config files.


## [Version 0.5.1] - Unreleased

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

## Version 0.5.6 - Unreleased

## Version 0.5.7 - Unreleased
