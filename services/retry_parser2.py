from typing import Any, Dict
from pydantic import BaseModel, Field, ValidationError
from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from langchain.output_parsers.retry import RetryOutputParser


# -----------------------------
# 1. Pydantic 모델 정의
# -----------------------------
class Action(BaseModel):
    action: str = Field(..., description="The action name")
    action_input: str = Field(..., description="Input for the action")


# -----------------------------
# 2. 콜백 정의
# -----------------------------
class RetryTrackingCallback:
    """재시도 횟수와 LLM 호출을 추적하는 콜백"""

    def __init__(self):
        self.retries = 0
        self.llm_calls = []

    def on_retry(self, retry_number: int):
        print(f"[Retry Callback] 재시도 #{retry_number}")
        self.retries = retry_number

    def on_llm_call(self, prompt: str, completion: str):
        print(f"[LLM Call] prompt: {prompt}, completion: {completion}")
        self.llm_calls.append({"prompt": prompt, "completion": completion})


# -----------------------------
# 3. RetryOutputParser 확장
# -----------------------------
class RetryOutputParserWithCallback(RetryOutputParser):
    def __init__(
        self, parser, retry_chain, max_retries=2, callback: RetryTrackingCallback = None
    ):
        super().__init__(
            parser=parser, retry_chain=retry_chain, max_retries=max_retries
        )
        self.callback = callback

    def parse_with_prompt(self, completion: str, prompt_value) -> Dict[str, Any]:
        """파서 재시도 및 콜백 호출"""
        retries = 0
        try:
            result = self.parser.parse(completion)
            return {"result": result, "retries": retries, "success": True}
        except ValidationError as e:
            last_error = e

        for _ in range(self.max_retries):
            retries += 1
            if self.callback:
                self.callback.on_retry(retries)

            # LLM 호출
            completion = self.retry_chain.invoke(
                {"prompt": prompt_value.to_string(), "completion": completion}
            )
            if self.callback:
                self.callback.on_llm_call(prompt_value.to_string(), completion)

            try:
                result = self.parser.parse(completion)
                return {"result": result, "retries": retries, "success": True}
            except ValidationError as e:
                last_error = e
                continue

        # 모든 재시도 실패
        return {
            "result": None,
            "retries": retries,
            "success": False,
            "error": str(last_error),
        }


# -----------------------------
# 4. Parser, LLM, Prompt 준비
# -----------------------------
pydantic_parser = PydanticOutputParser(pydantic_object=Action)
callback_handler = RetryTrackingCallback()
llm = ChatOpenAI(temperature=0)  # deterministic

retry_parser = RetryOutputParserWithCallback(
    parser=pydantic_parser, retry_chain=llm, max_retries=2, callback=callback_handler
)

prompt = PromptTemplate(
    template="사용자 요청: {query}\n{format_instructions}",
    input_variables=["query"],
    partial_variables={
        "format_instructions": pydantic_parser.get_format_instructions()
    },
)

prompt_value = prompt.format_prompt(query="레오나르도 디카프리오 여자친구")

# -----------------------------
# 5. 일부러 잘못된 completion 전달 → 재시도 유도
# -----------------------------
bad_completion = "NOT_JSON_OUTPUT"

result_info = retry_parser.parse_with_prompt(bad_completion, prompt_value)

# -----------------------------
# 6. 결과 출력
# -----------------------------
print("최종 결과:", result_info["result"])
print("재시도 횟수:", result_info["retries"])
print("성공 여부:", result_info["success"])
print("LLM 호출 로그:", callback_handler.llm_calls)
