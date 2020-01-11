import sys

from typing import Optional

from cleo import argument
from cleo import option

from poetry.utils._compat import Path

from ..command import Command


class BundleVenvCommand(Command):

    name = "venv"
    description = "Bundle the current project into a virtual environment"

    arguments = [
        argument("path", "The path to the virtual environment to bundle into."),
    ]

    options = [
        option(
            "python",
            "p",
            "The Python executable to use to create the virtual environment. "
            "Defaults to the current Python executable",
            flag=False,
            value_required=True,
        ),
    ]

    def handle(self):  # type: () -> Optional[int]
        from poetry.puzzle.provider import Indicator

        path = Path(self.argument("path"))
        executable = self.option("python")
        message = "Bundling <c1>{}</c1> (<b>{}</b>) into <c2>{}</c2>".format(
            self.poetry.package.pretty_name, self.poetry.package.pretty_version, path
        )
        if not self.io.is_verbose() and self.io.output.supports_ansi():
            indicator = Indicator(self._io, "{message} <debug>({elapsed:2s})</debug>")
            with indicator.auto(
                message, message.replace("Bundling", "<comment>Bundled</comment>")
            ):
                return self.bundle(path, executable=executable)

        self.line(message)

        return self.bundle(path, executable=executable)

    def bundle(self, path, executable=None):  # type: (Path, Optional[str]) -> int
        from poetry.installation.installer import Installer
        from poetry.io.null_io import NullIO
        from poetry.masonry.builders.wheel import WheelBuilder
        from poetry.semver.version import Version
        from poetry.utils.env import EnvManager
        from poetry.utils.env import SystemEnv
        from poetry.utils.env import VirtualEnv
        from poetry.utils.helpers import temporary_directory

        manager = EnvManager(self.poetry)
        if executable is not None:
            executable, python_version = manager.get_executable_info(executable)
        else:
            version_info = SystemEnv(Path(sys.prefix)).get_version_info()
            python_version = Version(*version_info[:3])

        if path.exists():
            if self.io.is_verbose() or not self.io.output.supports_ansi():
                self.line(
                    "  - Removing existing virtual environment <c2>{}</c2>".format(path)
                )

            manager.remove_venv(str(path))

        if self.io.is_verbose() or not self.io.output.supports_ansi():
            self.line(
                "  - Creating a virtual environment using Python <b>{}</b> in <c2>{}</c2>".format(
                    python_version, path
                )
            )

        manager.build_venv(str(path), executable=executable)
        env = VirtualEnv(path)

        if self.io.is_verbose() or not self.io.output.supports_ansi():
            self.line("  - Installing dependencies")

        installer = Installer(
            NullIO(), env, self.poetry.package, self.poetry.locker, self.poetry.pool
        )

        return_code = installer.run()
        if return_code:
            return return_code

        if self.io.is_verbose() or not self.io.output.supports_ansi():
            self.line(
                "  - Installing <c1>{}</c1> (<b>{}</b>)".format(
                    self.poetry.package.pretty_name, self.poetry.package.pretty_version
                )
            )

        # Build a wheel of the project in a temporary directory
        # and install it in the newly create virtual environment
        with temporary_directory() as directory:
            wheel_name = WheelBuilder.make_in(
                self.poetry, env, NullIO(), directory=Path(directory)
            )
            wheel = Path(directory).joinpath(wheel_name)
            package = self.poetry.package.clone()
            package.source_type = "file"
            package.source_url = wheel
            installer.installer.install(package)

        return 0
