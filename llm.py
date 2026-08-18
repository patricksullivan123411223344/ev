from pydantic import BaseModel, Field
import ollama 
import json
import pathlib 

class LLM(BaseModel):
    model: str = Field(default="gemma3:1b", description="The model to use for the LLM")
    llm_input: str = Field(default="", min_length=1, description="The input text for the LLM from various input methods")
    host: str = Field(default="http://localhost:11434", description="The host URL for the LLM")

    def receive_chat_input(self, input_text: str) -> None:
        self.llm_input = input_text

    def generate_response(self) -> str:
        client = ollama.Client(host=self.host)

        response = client.generate(model = self.model, 
                                   prompt = self.llm_input)
        
        return response["response"]