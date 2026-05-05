from openai import OpenAI

from api.config import settings
from api.errors import OpenAINotConfiguredError
from api.schemas import PredictionRequest


class OpenAIService:
    def __init__(self) -> None:
        self.api_key = settings.OPENAI_API_KEY
        self.model = settings.OPENAI_MODEL
        self.max_output_tokens = settings.OPENAI_MAX_OUTPUT_TOKENS
        # Two independent gates: the kill switch AND the credential. Both must
        # be present for any OpenAI client to be constructed at startup.
        self.client = (
            OpenAI(api_key=self.api_key)
            if (self.api_key and settings.ENABLE_LLM_CALLS)
            else None
        )

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
            raise OpenAINotConfiguredError()

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

    def run_rag(self, *, prompt: str, instructions: str | None = None) -> str:
        """Grounded Q&A inference.

        Callers are expected to build ``prompt`` from retrieved context and
        include an explicit instruction to answer only from that context. This
        method deliberately does not massage the prompt further.
        """
        if not self.client:
            raise OpenAINotConfiguredError()

        instr = instructions or (
            "You are a due diligence analyst answering questions about "
            "specific company documents. Answer only from the provided "
            "context. If the context does not contain the answer, say so "
            "explicitly. Do not invent facts or citations."
        )

        response = self.client.responses.create(
            model=self.model,
            instructions=instr,
            input=prompt,
            max_output_tokens=self.max_output_tokens,
        )
        return self._extract_text(response)


openai_service = OpenAIService()
