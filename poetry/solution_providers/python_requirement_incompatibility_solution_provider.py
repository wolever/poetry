import re

from typing import List

from crashtest.contracts.has_solutions_for_exception import HasSolutionsForException
from crashtest.contracts.solution import Solution


class PythonRequirementIncompatibilitySolutionProvider(HasSolutionsForException):
    def can_solve(self, exception):  # type: (Exception) -> bool
        from poetry.puzzle.exceptions import SolverProblemError

        if not isinstance(exception, SolverProblemError):
            return False

        m = re.match(
            "^The current project's Python requirement (.+) is not compatible "
            "with some of the required packages Python requirement",
            str(exception),
        )

        if not m:
            return False

        return True

    def get_solutions(self, exception):  # type: (Exception) -> List[Solution]
        from poetry.solutions.python_requirement_compatibility_solution import (
            PythonRequirementCompatibilitySolution,
        )

        return [PythonRequirementCompatibilitySolution(exception)]
