"""
Simple Calculator
A basic command-line calculator demonstrating OmniSolve's incremental continuation.
"""


def add(a, b):
    """Add two numbers."""
    return a + b


def subtract(a, b):
    """Subtract b from a."""
    return a - b


def multiply(a, b):
    """Multiply two numbers."""
    return a * b


def divide(a, b):
    """Divide a by b."""
    if b == 0:
        raise ValueError("Cannot divide by zero")
    return a / b


def get_number(prompt):
    """Get a valid number from user input."""
    while True:
        try:
            return float(input(prompt))
        except ValueError:
            print("Invalid input. Please enter a valid number.")


def display_menu():
    """Display the calculator menu."""
    print("\n" + "=" * 40)
    print("Simple Calculator")
    print("=" * 40)
    print("1. Add")
    print("2. Subtract")
    print("3. Multiply")
    print("4. Divide")
    print("5. Quit")
    print("=" * 40)


def main():
    """Main calculator loop."""
    print("Welcome to Simple Calculator!")
    
    while True:
        display_menu()
        
        choice = input("\nChoose operation (1-5): ")
        
        if choice == '5':
            print("Thank you for using Simple Calculator. Goodbye!")
            break
        
        if choice not in ['1', '2', '3', '4']:
            print("Invalid choice. Please select 1-5.")
            continue
        
        # Get numbers from user
        try:
            num1 = get_number("Enter first number: ")
            num2 = get_number("Enter second number: ")
        except KeyboardInterrupt:
            print("\n\nOperation cancelled.")
            continue
        
        # Perform calculation
        try:
            if choice == '1':
                result = add(num1, num2)
                operation = "+"
            elif choice == '2':
                result = subtract(num1, num2)
                operation = "-"
            elif choice == '3':
                result = multiply(num1, num2)
                operation = "*"
            elif choice == '4':
                result = divide(num1, num2)
                operation = "/"
            
            print(f"\nResult: {num1} {operation} {num2} = {result}")
        
        except ValueError as e:
            print(f"\nError: {e}")
        except Exception as e:
            print(f"\nUnexpected error: {e}")


if __name__ == "__main__":
    main()
