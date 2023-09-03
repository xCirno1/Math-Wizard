# Math Wizard
Welcome to Math Wizard, a project designed to ensure precise and accurate mathematical calculations. This is an independent project, which eliminates the need for any additional libraries. Our primary goal is to provide users with an easy-to-use platform for solving math problems. We highly welcome your feedback, suggestions, and contributions, so please don't hesitate to create issues or pull requests.

## Installation
Currently, Math Wizard is not available on PyPI (*yet). To get started, simply clone the project by running the following command: `git clone https://github.com/xCirno1/Math-Wizard`

## Basic Example
- - - -
* #### As a calculator
```python
import solver

# Let's try to calculate triangle area with a height of 5
# and base length of 10
answer = solver.solve("1/2 * 10 * 5")
print(answer)  # Prints 25
```
* #### As a math solver
```python
import solver

answer = solver.solve("4x + 3 = 19")
print(answer.x)  # Prints 4
```

## Features
- Parsing problems and equations
- Safe calculation without the usage of `eval` or `exec`
- Basic arithmetics calculation (PEMDAS problem)
- Solving linear algebra (1 variable)

## How it works
Math Wizard operates by accepting problems and equations as strings and using its own algorithm to solve them. Here's a breakdown of the process:
1. Math Wizard receives the problem or equation as a string.
2. It parses the string character by character, identifying the type of each character (operator, digit, etc.).
3. Once the parsing phase is complete, Math Wizard determines the problem's identity, such as the number of variables or whether it's an equation.
4. It then categorizes the problem type, whether it falls under Basic PEMDAS, Quadratic Equation, or other categories.
5. Using specific functions bound to each problem type, Math Wizard proceeds to solve the problem.


_Note: This project is currently on development and should not be used in production environments._
