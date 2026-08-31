"""Maps import packages onto the domain-first repo layout.

- ``platform_core``  <- platform/backend   (named to avoid shadowing stdlib ``platform``)
- ``apps.<tool>``    <- apps/<tool>        (new tools are auto-discovered; re-run
                                            ``pip install -e .`` after scaffolding one)
"""

from setuptools import find_packages, setup

packages = (
    ["platform_core"]
    + [f"platform_core.{p}" for p in find_packages("platform/backend")]
    + ["apps"]
    + [f"apps.{p}" for p in find_packages("apps")]
)

setup(
    packages=packages,
    package_dir={"platform_core": "platform/backend", "apps": "apps"},
)
