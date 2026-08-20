from orchestrator import Orchestrator
from stt import STTClient

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
    stt_controller = STTClient("build/stt/ev_stt.exe")
    stt_controller.start
    
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