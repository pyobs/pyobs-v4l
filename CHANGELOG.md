# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

Entries for releases before this file existed were generated from commit subjects.

## [2.1.0] - 2026-09-29

- Move v4lCamera to the BaseVideo frames() contract
- Deliver every frame to _set_image() instead of throttling in _capture()

## [2.0.0] - 2026-08-26

- Require stable pyobs-core>=2.0.0
- Gate auto-merge on the PR author, not the event actor
- Enable Dependabot auto-merge for patch/minor updates
- Camera driver/GUI split: fix capture/handle leaks, read race, sync open (#19)
- Remove upper bound on Python version
- pyrefly: exclude gui.py from type checking
- Add baseline test suite and CI (pytest, pyrefly), grouped Dependabot
- Upgrade uv.lock to clear open Dependabot alerts
- Require pyobs-core>=2.0.0.dev48
- Add dependabot.yml, targeting develop for PRs
- Run cv2/V4L2 camera calls through a background thread
- Add Sphinx documentation
- Rewrite README for uv-based install, config docs, and GUI
- remove `DEVELOPMENT.md` documentation file detailing the pyobs migration guide
- remove `pyobs-v4l` package and its dependencies
- added `gui.py` for V4L camera control with live preview and exposure management
- added `uv.lock` to track dependencies and Python compatibility for the project
- migrate to pyproject.toml with PEP 621, add support for pyobs 2.0 and Python 3.11, and configure GitHub Actions for Ruff and PyPI publishing
- added DEVELOPMENT.md with migration guide for pyobs 2.0

## [1.0.0] - 2024-06-05

- python 3.12
- added license
- added black and pre-commit to dev dependencies
- added .pre-commit-config.yaml
- running black
- added pyproject.toml
- removed self.closing in all Modules
- asyncio
- renamed IWebcam->IVideo and BaseWebcam->BaseVideo
- changed order
- initial commit
