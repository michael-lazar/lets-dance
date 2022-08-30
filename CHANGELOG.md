# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## Unreleased

### Added

- Added `LICENSE.md` file.

## v0.1.1 (2022-06-21)

### Changed

- Fixed unicode encoding error when publishing boards.
- Replaced `Authorization` header with `Spring-Signature`.

## v0.1.0 (2022-06-20)

This release mostly implements the Spring '83 spec revision 1, dated 2022-06-16.

### Added

- Added `CHANGELOG.md` file to track versions.

### Changed

- Fixed typo in `tools/manage publish_board` command.
- Switch from `<meta>` tag to `<time>` tag for the last modified date.
- Set the difficulty factor to a constant value of `0`.
- Updated valid public key pattern to `83e(0[1-9]|1[0-2])(\d\d)`.
- Tweaks to the index page CSS and layout.

## v0.0.1 (2022-06-15)

This release mostly implements the original Spring '83 spec dated 2022-06-09.
