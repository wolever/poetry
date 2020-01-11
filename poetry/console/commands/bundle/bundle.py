from typing import Optional

from ..command import Command
from .venv import BundleVenvCommand


class BundleCommand(Command):

    name = "bundle"
    description = "Bundle the current project."

    commands = [BundleVenvCommand()]

    def handle(self):  # type: () -> Optional[int]
        return self.call("help", self._config.name)
