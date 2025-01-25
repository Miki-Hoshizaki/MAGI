from magi import CodeGenerator

def main():
    # Create code generator instance
    generator = CodeGenerator()
    
    # Example programming question
    question = "Write a function to calculate the nth number in the Fibonacci sequence"
    
    # Generate code
    success, code, feedback = generator.generate_code(question)
    
    if success:
        print("\n=== Generation Successful ===")
        print("Generated code:")
        print(code)
    else:
        print("\n=== Generation Failed ===")
        print("Feedback:")
        for feedback_item in feedback:
            print(f"- {feedback_item}")

if __name__ == "__main__":
    main()