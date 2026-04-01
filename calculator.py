"""
Calculator module providing basic arithmetic operations.

This module contains a Calculator class that supports basic mathematical
operations including addition, subtraction, multiplication, and division.
It also provides functionality to evaluate simple arithmetic expressions.

Example:
    >>> calc = Calculator()
    >>> calc.add(2, 3)
    5
    >>> calc.calculate("2 + 3")
    5
"""

from typing import Union


Number = Union[int, float]


class Calculator:
    """
    A calculator class that performs basic arithmetic operations.

    This class provides methods for addition, subtraction, multiplication,
    and division, with proper error handling for edge cases like division by zero.

    Attributes:
        history (list): A list storing the history of calculations performed.
    """

    def __init__(self) -> None:
        """Initialize the Calculator with an empty history."""
        self.history: list[str] = []

    def add(self, a: Number, b: Number) -> Number:
        """
        Add two numbers together.

        Args:
            a: The first number.
            b: The second number.

        Returns:
            The sum of a and b.

        Example:
            >>> calc = Calculator()
            >>> calc.add(2, 3)
            5
        """
        result = a + b
        self._record_history(f"{a} + {b} = {result}")
        return result

    def subtract(self, a: Number, b: Number) -> Number:
        """
        Subtract the second number from the first.

        Args:
            a: The first number.
            b: The second number.

        Returns:
            The difference between a and b.

        Example:
            >>> calc = Calculator()
            >>> calc.subtract(5, 3)
            2
        """
        result = a - b
        self._record_history(f"{a} - {b} = {result}")
        return result

    def multiply(self, a: Number, b: Number) -> Number:
        """
        Multiply two numbers together.

        Args:
            a: The first number.
            b: The second number.

        Returns:
            The product of a and b.

        Example:
            >>> calc = Calculator()
            >>> calc.multiply(4, 3)
            12
        """
        result = a * b
        self._record_history(f"{a} * {b} = {result}")
        return result

    def divide(self, a: Number, b: Number) -> Number:
        """
        Divide the first number by the second.

        Args:
            a: The dividend.
            b: The divisor.

        Returns:
            The quotient of a divided by b.

        Raises:
            ZeroDivisionError: If the divisor (b) is zero.

        Example:
            >>> calc = Calculator()
            >>> calc.divide(10, 2)
            5.0
        """
        if b == 0:
            raise ZeroDivisionError("Cannot divide by zero")
        result = a / b
        self._record_history(f"{a} / {b} = {result}")
        return result

    def calculate(self, expression: str) -> Number:
        """
        Evaluate a simple arithmetic expression string.

        Supports basic operations: +, -, *, /

        Args:
            expression: A string containing a simple arithmetic expression
                (e.g., "2 + 3", "10 / 2").

        Returns:
            The result of the evaluated expression.

        Raises:
            ValueError: If the expression format is invalid or contains
                unsupported operations.
            ZeroDivisionError: If division by zero is attempted.

        Example:
            >>> calc = Calculator()
            >>> calc.calculate("2 + 3")
            5
            >>> calc.calculate("10 / 2")
            5.0
        """
        expression = expression.strip()

        # Parse the expression
        parts = expression.split()

        if len(parts) != 3:
            raise ValueError(
                f"Invalid expression format: '{expression}'. "
                "Expected format: 'number operator number' (e.g., '2 + 3')"
            )

        try:
            a = float(parts[0]) if '.' in parts[0] else int(parts[0])
            operator = parts[1]
            b = float(parts[2]) if '.' in parts[2] else int(parts[2])
        except ValueError as e:
            raise ValueError(
                f"Invalid number in expression: '{expression}'"
            ) from e

        # Perform the operation
        operations = {
            '+': self.add,
            '-': self.subtract,
            '*': self.multiply,
            '/': self.divide,
        }

        if operator not in operations:
            raise ValueError(
                f"Unsupported operator: '{operator}'. "
                f"Supported operators: {', '.join(operations.keys())}"
            )

        return operations[operator](a, b)

    def get_history(self) -> list[str]:
        """
        Get the history of all calculations performed.

        Returns:
            A list of strings representing the calculation history.

        Example:
            >>> calc = Calculator()
            >>> calc.add(2, 3)
            >>> calc.get_history()
            ['2 + 3 = 5']
        """
        return self.history.copy()

    def clear_history(self) -> None:
        """Clear the calculation history."""
        self.history.clear()

    def _record_history(self, entry: str) -> None:
        """
        Record a calculation in the history.

        Args:
            entry: The calculation entry to record.
        """
        self.history.append(entry)


if __name__ == "__main__":
    # Simple demonstration
    calc = Calculator()

    print("Basic Calculator Demo")
    print("=" * 30)

    # Basic operations
    print(f"2 + 3 = {calc.add(2, 3)}")
    print(f"10 - 4 = {calc.subtract(10, 4)}")
    print(f"5 * 6 = {calc.multiply(5, 6)}")
    print(f"20 / 4 = {calc.divide(20, 4)}")

    # Expression evaluation
    print("\nExpression Evaluation:")
    print(f"'8 / 2' = {calc.calculate('8 / 2')}")
    print(f"'7 * 3' = {calc.calculate('7 * 3')}")

    # Show history
    print("\nCalculation History:")
    for entry in calc.get_history():
        print(f"  {entry}")
