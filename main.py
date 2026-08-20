from orchestrator import Orchestrator

STOP_INSTANCES = [
    "stop",
    "STOP",
    "Stop",
    "Bye",
    "BYE",
    "bye"
]

def main():
    main_llm_instance = Orchestrator()
    while True:
        user_input = input("User: ")

        if user_input in STOP_INSTANCES:
            print("LLM: Goodbye!")
            break

        main_llm_instance.receive_chat_input(user_input)
        try:
            response = main_llm_instance.handle_request()
        except Exception as error:
            response = f"I could not complete that request: {error}"
        print(f"LLM: {response}")

if __name__ == "__main__":
    main()