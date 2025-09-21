from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from langchain.output_parsers.retry import RetryOutputParser
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field, ValidationError

# 1. Pydantic 모델 정의
class Action(BaseModel):
    action: str = Field(..., description="The action that the agent should take")
    action_input: str = Field(..., description="Input for the action")

# 2. 기본 출력 파서 설정: PydanticOutputParser
pydantic_parser = PydanticOutputParser(pydantic_object=Action)

# 3. Retry 출력 파서 설정: LLM + 기본 파서 + 최대 재시도 회수
llm = ChatOpenAI(temperature=0.0)  # deterministic하게
retry_parser = RetryOutputParser.from_llm(parser=pydantic_parser, llm=llm, max_retries=2)

# 4. PromptTemplate 구성: format-instructions 포함
prompt = PromptTemplate(
    template="You are a helpful assistant. Please output JSON matching the schema:\n"
             "{format_instructions}\n"
             "User query: {query}\n",
    input_variables=["query"],
    partial_variables={"format_instructions": pydantic_parser.get_format_instructions()},
)

# 5. 실행 함수 예
def run(query: str) -> Action:
    # 먼저 LLM으로 raw 출력 받기
    raw = llm.invoke({"messages": [{"role": "user", "content": prompt.format_prompt(query=query).to_string()}]})
    # raw에서 컴플리션 (string) 추출 — 예시는 LLM API의 반환 형태에 따라 조정 필요
    completion = raw.content if hasattr(raw, "content") else raw  # 단순화

    # prompt_value 준비 (RetryOutputParser이 재시도 시 prompt를 알아야 함)
    prompt_value = prompt.format_prompt(query=query)

    # 파싱 시도 (필요하면 재시도)
    try:
        result: Action = retry_parser.parse_with_prompt(completion=completion, prompt_value=prompt_value)
    except ValidationError as e:
        # 파싱 실패 시 로그 남기고 예외 재발생 또는 fallback
        print("Parsing failed even after retries:", e)
        raise

    return result

# 6. 사용 예
if __name__ == "__main__":
    query = "Search for the current girlfriend of Leonardo DiCaprio"
    action_obj = run(query)
    print("Result:", action_obj)
