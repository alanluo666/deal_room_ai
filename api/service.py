import os

from dotenv import load_dotenv
from openai import OpenAI

from api.schemas import PredictionRequest

load_dotenv()


class OpenAIService:
    def __init__(self) -> None:
        self.api_key = os.getenv("OPENAI_API_KEY", "")
        self.model = os.getenv("OPENAI_MODEL", "gpt-5-mini")
        self.max_output_tokens = int(os.getenv("OPENAI_MAX_OUTPUT_TOKENS", "400"))
        self.client = OpenAI(api_key=self.api_key) if self.api_key else None

    def is_ready(self) -> bool:
        return self.client is not None

    def _extract_text(self, response) -> str:
        if getattr(response, "output_text", None):
            return response.output_text

        output_blocks = getattr(response, "output", []) or []
        text_parts: list[str] = []

        for block in output_blocks:
            contents = getattr(block, "content", []) or []
            for item in contents:
                text_value = getattr(item, "text", None)
                if text_value:
                    text_parts.append(text_value)

        return "\n".join(text_parts).strip()

    def run_prediction(self, request: PredictionRequest) -> str:
        if not self.client:
            raise RuntimeError("OPENAI_API_KEY is not set")

        instructions = (
            "You are a due diligence analyst for a private equity deal team. "
            "Respond concisely and focus on material findings."
        )

        if request.task == "risks":
            prompt = (
                "Review the following company material and identify the main due "
                f"diligence risks.\n\nDocument:\n{request.document_text}"
            )
        elif request.task == "qa" and request.question:
            prompt = (
                f"Answer this due diligence question based only on the document.\n"
                f"Question: {request.question}\n\nDocument:\n{request.document_text}"
            )
        else:
            prompt = (
                "Summarize the following company material for a private equity deal team.\n\n"
                f"Document:\n{request.document_text}"
            )

        response = self.client.responses.create(
            model=self.model,
            instructions=instructions,
            input=prompt,
            max_output_tokens=self.max_output_tokens,
        )
        return self._extract_text(response)


openai_service = OpenAIService()
