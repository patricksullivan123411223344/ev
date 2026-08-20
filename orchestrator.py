import json
from pydantic import BaseModel, Field
from spotify import SPTSessionManager
from tools import SPOTIFY_TOOLS, RouteDecision
from llm_state import ActionRecord, ChatHistory
import ollama 

spotifyController = SPTSessionManager()

class Orchestrator(BaseModel):
    model: str = Field(default="qwen3:8b", description="The model to use for the LLM")
    llm_input: str = Field(default="", min_length=1, description="The input text for the LLM from various input methods")
    host: str = Field(default="http://localhost:11434", description="The host URL for the LLM")

    sys_prompt: str = """
    You are EV, Patrick's personal local AI assistant.
    Speak naturally, casually, and concisely. Match Patrick's tone without copying it excessively.
    You may use humor, slang, and occasional profanity when it fits naturally. Do not explain common phrases, jokes, or casual language unless Patrick asks.

    Act like a sharp, technically capable collaborator. Not a corporate assistant, customer-service bot, military computer, or overly agreeable servent.
    Do not constantly address Patrick as "sir". Use Patrick rarely and only when natural.

    Base recommendations on Patrick's actual projects, current context, and implemented capabilities. Never invent teams, budgets, organizational resources, infrastructure, or requirements.
    When suggesting what to build next, recommend the smallest useful next step unless Patrick asks for a larger plan. 

    Be direct and honest. Challenge weak ideas when necessary, acknowledge uncertainty, and never fabricate completed actions or available capabilities. 
    """

    tool_domains: dict =  {
        "spotify": SPOTIFY_TOOLS
    }

    last_action: ActionRecord | None = None
    chat_history: list[ChatHistory] = Field(default_factory=list)
    max_chat_messages: int = 20
    history_aware_domains: set = {"spotify"}
    def choose_domain(self) -> RouteDecision: 
        client = ollama.Client(host=self.host)

        domain_context = """
        spotify:
            Music playback and Spotify control.
        
        system:
            Local computer and application control.

        conversation:
            Questions, discussion, explanations, brainstorming, and requests that do not require changing an external system.
        """
        response = client.chat(
            model=self.model,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Classify the users request into exactly one "
                        "available capability domain. \n\n"
                        f"{domain_context}"
                        "Use the previous successful action only "
                        "when the current request clearly refers to it. \n"
                        f"Previous action: {self.get_last_action_context()}"
                    )
                },
                {
                    "role": "user",
                    "content":self.llm_input
                }
            ],
            think=False,
            format=RouteDecision.model_json_schema()
        )
        return RouteDecision.model_validate_json(
            response.message.content
        )

    def get_tool_schemas(self, domain: str):
        registry = self.tool_domains[domain]

        return [
            {
                "type": "function",
                "function": {
                    "name": name,
                    "description": tool["description"],
                    "parameters": tool["args_model"].model_json_schema()
                }
            }
            for name, tool in registry.items()
        ]

    def choose_tool(self, domain: str):
        client = ollama.Client(host=self.host)
        tools = self.get_tool_schemas(domain)
        messages= [
                    { "role": "system", "content": self.sys_prompt},
        ]

        if domain in self.history_aware_domains:
            messages.extend(
                message.model_dump()
                for message in self.chat_history[-10:]
            )

        messages.append({"role": "user", "content": self.llm_input},)
        response = client.chat(
            model=self.model, 
            messages=messages,
            tools=tools,
            think=False
        )
        return response 

    def extract_tool_call(self, response):
        tool_calls = getattr(response.message, "tool_calls", None) or []
        if not tool_calls:
            return None

        tool_call = tool_calls[0]
        function = tool_call.function
        name = function.name
        arguments = function.arguments
        if isinstance(arguments, str):
            arguments = json.loads(arguments)
        if hasattr(arguments, "model_dump"):
            arguments = arguments.model_dump()
        return name, arguments

    def execute_tool(
            self,
            domain: str,
            tool_name: str,
            arguments: dict
    ):
        registry = self.tool_domains[domain]
        tool = registry[tool_name]

        validated_args = tool["args_model"](**arguments) 
        function = getattr(spotifyController, tool["function"])

        return function(
            **validated_args.model_dump()
        )

    def handle_request(self) -> str:
        self.store_chat_message("user", self.llm_input)

        domain = self.choose_domain().domain

        if domain == "conversation":
            response_text = self.generate_response()
            self.store_chat_message("assistant", response_text)
            return response_text

        if domain not in self.tool_domains:
            return f"I cannot handle the {domain} capability yet."

        response = self.choose_tool(domain)
        tool_call = self.extract_tool_call(response)
        if tool_call is None:
            final_text = response.message.content or "I could not determine an action for that request."
            self.store_chat_message("assistant", final_text)
            return final_text

        tool_name, arguments = tool_call
        result = self.execute_tool(domain, tool_name, arguments)
        self.last_action = ActionRecord(
            user_input=self.llm_input,
            domain=domain,
            tool_name=tool_name,
            arguments=arguments,
            result=str(result) if result is not None else None,
        )

        final_text = str(result or f"Completed {tool_name}.")
        self.store_chat_message("assistant", final_text)
        return final_text

    def get_last_action_context(self) -> str:
        if self.last_action is None:
            return "No previous tool action is available."

        return self.last_action.model_dump_json()

    def store_chat_message(self, role: str, content: str) -> None:
        self.chat_history.append(
            ChatHistory(role=role, content=content)
        )
        self.chat_history = self.chat_history[-self.max_chat_messages:]

    def receive_chat_input(self, input_text: str) -> None:
        self.llm_input = input_text

    def generate_response(self) -> str:
        client = ollama.Client(host=self.host)
        messages = [
            {"role": "system", "content": self.sys_prompt},
            *[
                message.model_dump()
                for message in self.chat_history
            ],
            {"role": "user", "content": self.llm_input}
        ]
        response = client.chat(
            model=self.model,
            messages=messages,
            think=False
        )
        return response.message.content