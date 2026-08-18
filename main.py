from llm import LLM

STOP_INSTANCES = [
    "stop",
    "STOP",
    "Stop",
    "Bye",
    "BYE",
    "bye"
]

def main():
    while True:
        llm_instance = LLM()
        user_input = input("User: ")

        if user_input in STOP_INSTANCES:
            print("LLM: Goodbye!")
            break

        llm_instance.receive_chat_input(user_input)
        response = llm_instance.generate_response()
        print(f"LLM: {response}")

if __name__ == "__main__":
    main()