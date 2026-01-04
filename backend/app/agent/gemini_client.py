"""Gemini API 클라이언트

Google Gemini API와 통신하여 Function Calling을 수행합니다.
"""
import json
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
import google.generativeai as genai
from google.generativeai.types import FunctionDeclaration, Tool, content_types

from app.config import get_settings


@dataclass
class FunctionCall:
    """LLM이 요청한 함수 호출 정보"""
    name: str
    args: Dict[str, Any]


@dataclass
class GeminiResponse:
    """Gemini API 응답"""
    text: Optional[str] = None
    function_calls: List[FunctionCall] = field(default_factory=list)
    finish_reason: str = "STOP"
    

class GeminiClient:
    """Gemini API 클라이언트
    
    Function Calling을 지원하는 Gemini 모델과 통신합니다.
    
    무료 티어 제한:
    - 5 RPM (분당 요청)
    - 25 RPD (일일 요청)
    """
    
    def __init__(self, api_key: Optional[str] = None):
        settings = get_settings()
        self.api_key = api_key or settings.gemini_api_key
        
        if not self.api_key:
            raise ValueError("Gemini API 키가 설정되지 않았습니다. GEMINI_API_KEY 환경변수를 설정하세요.")
        
        genai.configure(api_key=self.api_key)
        
        # 모델 초기화 (Gemini 2.5 Flash - 무료 티어)
        self.model_name = "gemini-2.0-flash"
        self.model = None
        self._tools = None
    
    def set_tools(self, tools: List[Dict[str, Any]]) -> None:
        """사용 가능한 Tool 설정
        
        MCP Gateway에서 가져온 Tool 목록을 Gemini 형식으로 변환
        
        Args:
            tools: [{"name": "mysql.query", "description": "...", "parameters": {...}}]
        """
        function_declarations = []
        
        for tool in tools:
            # Gemini FunctionDeclaration 형식으로 변환
            func_decl = FunctionDeclaration(
                name=tool["name"].replace(".", "_"),  # Gemini는 .을 허용하지 않음
                description=tool["description"],
                parameters=tool["parameters"],
            )
            function_declarations.append(func_decl)
        
        if function_declarations:
            self._tools = [Tool(function_declarations=function_declarations)]
        else:
            self._tools = None
        
        # 모델 재생성 (tools 적용)
        self.model = genai.GenerativeModel(
            model_name=self.model_name,
            tools=self._tools,
            system_instruction=self._get_system_prompt(),
        )
    
    def _get_system_prompt(self) -> str:
        """시스템 프롬프트"""
        return """당신은 데이터베이스 쿼리 전문 AI 어시스턴트입니다.

**핵심 원칙: 도구 우선 사용**
사용자가 데이터 조회를 요청하면, 불필요한 질문 없이 즉시 적절한 도구를 사용하여 데이터를 조회하세요.

**작업 순서:**
1. 사용자 요청 분석
2. 필요한 테이블 파악 (테이블명이 명확하면 바로 사용, 불명확하면 list_tables로 확인)
3. 테이블 구조 확인 필요 시 describe_table 사용
4. 즉시 SELECT 쿼리 실행
5. 결과를 한국어로 정리하여 응답

**예시:**
- "고객 목록 조회해줘" → 바로 `SELECT * FROM customers LIMIT 100` 실행
- "주문 목록 보여줘" → 바로 `SELECT * FROM orders LIMIT 100` 실행
- "매출 데이터" → 바로 관련 테이블 쿼리 실행

**금지사항:**
- "어떤 테이블을 조회할까요?" 같은 불필요한 질문 금지
- "쿼리를 실행할까요?" 같은 확인 요청 금지
- 사용자가 요청하면 바로 실행하세요

**안전 규칙:**
- SELECT 쿼리만 사용 (INSERT, UPDATE, DELETE 금지)
- LIMIT 절을 추가하여 대량 조회 방지 (기본 100개)
- 민감 정보는 마스킹하여 표시

사용 가능한 도구:
- mysql.query: SQL SELECT 쿼리 실행
- mysql.list_tables: 테이블 목록 조회
- mysql.describe_table: 테이블 구조 조회
"""
    
    async def generate(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
    ) -> GeminiResponse:
        """메시지 생성
        
        Args:
            messages: [{"role": "user", "content": "..."}, ...]
            temperature: 생성 온도 (0.0 ~ 1.0)
        
        Returns:
            GeminiResponse: 텍스트 또는 함수 호출 정보
        """
        if not self.model:
            # Tool 없이 기본 모델 생성
            self.model = genai.GenerativeModel(
                model_name=self.model_name,
                system_instruction=self._get_system_prompt(),
            )
        
        # Gemini 형식으로 메시지 변환
        gemini_messages = []
        for msg in messages:
            role = "user" if msg["role"] == "user" else "model"
            gemini_messages.append({
                "role": role,
                "parts": [msg["content"]],
            })
        
        # API 호출
        response = self.model.generate_content(
            gemini_messages,
            generation_config=genai.GenerationConfig(
                temperature=temperature,
            ),
        )
        
        return self._parse_response(response)
    
    async def generate_with_function_result(
        self,
        messages: List[Dict[str, str]],
        function_name: str,
        function_result: Any,
        temperature: float = 0.7,
    ) -> GeminiResponse:
        """함수 결과를 포함하여 메시지 생성
        
        Tool 호출 후 결과를 전달하여 최종 응답을 생성합니다.
        
        Args:
            messages: 이전 대화 내역
            function_name: 호출된 함수 이름
            function_result: 함수 실행 결과
            temperature: 생성 온도
        """
        if not self.model:
            raise ValueError("Tool이 설정되지 않았습니다. set_tools()를 먼저 호출하세요.")
        
        # 대화 시작
        chat = self.model.start_chat(history=[])
        
        # 이전 메시지들 전송 (마지막 메시지 제외)
        for msg in messages[:-1]:
            if msg["role"] == "user":
                chat.send_message(msg["content"])
        
        # 마지막 사용자 메시지로 함수 호출 요청
        last_user_msg = messages[-1]["content"] if messages else ""
        response = chat.send_message(last_user_msg)
        
        # 함수 결과 전송
        # Gemini API에서는 function response를 part로 전달
        function_response = content_types.to_content({
            "parts": [{
                "function_response": {
                    "name": function_name,
                    "response": {"result": function_result}
                }
            }]
        })
        
        # 최종 응답 생성
        final_response = chat.send_message(function_response)
        
        return self._parse_response(final_response)
    
    def _parse_response(self, response) -> GeminiResponse:
        """Gemini 응답 파싱"""
        result = GeminiResponse()
        
        if not response.candidates:
            return result
        
        candidate = response.candidates[0]
        result.finish_reason = str(candidate.finish_reason) if candidate.finish_reason else "STOP"
        
        # 응답 파트 처리
        for part in candidate.content.parts:
            # 텍스트 응답
            if hasattr(part, 'text') and part.text:
                result.text = part.text
            
            # 함수 호출
            if hasattr(part, 'function_call') and part.function_call:
                fc = part.function_call
                # 함수 이름 복원 (mysql_query → mysql.query)
                original_name = fc.name.replace("_", ".", 1) if "_" in fc.name else fc.name
                
                result.function_calls.append(FunctionCall(
                    name=original_name,
                    args=dict(fc.args) if fc.args else {},
                ))
        
        return result
    
    def convert_tool_name_for_gemini(self, name: str) -> str:
        """Tool 이름을 Gemini 호환 형식으로 변환
        
        mysql.query → mysql_query
        """
        return name.replace(".", "_")
    
    def restore_tool_name(self, name: str) -> str:
        """Gemini 형식 Tool 이름을 원래 형식으로 복원
        
        mysql_query → mysql.query
        """
        # 첫 번째 _ 만 .으로 변환
        if "_" in name:
            parts = name.split("_", 1)
            return f"{parts[0]}.{parts[1]}"
        return name
