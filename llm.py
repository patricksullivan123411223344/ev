import json
from pydantic import BaseModel, Field
from spotify import SPTSessionManager
from tools import SPOTIFY_TOOLS, RouteDecision
import ollama 

spotifyController = SPTSessionManager()

class LLM(BaseModel):
    model: str = Field(default="qwen3:8b", description="The model to use for the LLM")
    llm_input: str = Field(default="", min_length=1, description="The input text for the LLM from various input methods")
    host: str = Field(default="http://localhost:11434", description="The host URL for the LLM")

    sys_prompt: str = """
    You are an elite digital intelligence built for Patrick Sullivan. 
    Your tone is crisp, formal, and deeply loyal. 
    You anticipate needs, eliminate friction, and deliver precise, concise answers. 
    Speak with calm authority, minimal fluff, and absolute technical competence. 
    Address the user as "Sir" or "Patrick" as appropriate.
    """

    tool_domains: dict =  {
        "spotify": SPOTIFY_TOOLS
    }

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
                    )
                },
                {
                    "role": "user",
                    "content":self.llm_input
                }
            ],
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
                    {"role": "user", "content": self.llm_input}
        ]
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
        domain = self.choose_domain().domain

        if domain == "conversation":
            return self.generate_response()

        if domain not in self.tool_domains:
            return f"I cannot handle the {domain} capability yet."

        response = self.choose_tool(domain)
        tool_call = self.extract_tool_call(response)
        if tool_call is None:
            return response.message.content or "I could not determine an action for that request."

        tool_name, arguments = tool_call
        result = self.execute_tool(domain, tool_name, arguments)
        return str(result or f"Completed {tool_name}.")

    def receive_chat_input(self, input_text: str) -> None:
        self.llm_input = input_text

    def generate_response(self) -> str:
        client = ollama.Client(host=self.host)

        response = client.generate(model = self.model,
                                   prompt = self.llm_input,
                                   system=self.sys_prompt,
                                   think=False
                                )
        return response["response"]