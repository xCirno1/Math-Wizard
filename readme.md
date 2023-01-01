# Math Wizard
This project was made to ensure that your calculations are precise and correct. The project is independent; it doesn't require any additional libraries. The goal is to create an easy-to-use program that solves math problems accurately. The project is open to any advice and requests (so please feel free to create issues or pull requests).




## Installation
The project is not available on pypi yet. To clone the project, run `git clone https://github.com/xCirno1/Math-Wizard`.


## Basic Example
```python
import solver

# Let's try to calculate triangle area with a height of 5
#  and base length of 10
problem = "1/2 * 10 * 5"

answer = solver.solve(problem)
print(answer)  # Prints 25
```

## Features
- Parsing problems and equations
- Basic calculation (PEMDAS problem)


## How it works
1. Math Wizard received the problem/equation as a string.
2. It parses the string per character, and decide what type the character is (operator, digit, etc).
3. After the parsing section finishes, it then sees the problem's identity. (How many variables? Is it an equation?, and so on...)
4. It decides the problem type (Basic PEMDAS, Quadratic Equation, etc)
5. It solves the problem using specific functions, divided according to its type.




_Note: This is a development project, do not use on production._
