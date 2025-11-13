#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
법령 AI 어시스턴트 FastAPI 서버
"""

import os
import sys
import logging
from typing import List, Optional
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

# Law agent 모듈 임포트
from Law_agent import LawAgentConfig, LawKnowledgeBase, LawAgent

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# FastAPI 앱 생성
app = FastAPI(
    title="법령 AI 어시스턴트 API",
    description="민법 기반 법령 질의응답 시스템",
    version="1.0.0"
)

# CORS 설정 (React 프론트엔드 연결)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],  # React 개발 서버
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 요청/응답 모델
class QuestionRequest(BaseModel):
    question: str
    
class AnswerResponse(BaseModel):
    answer: str
    sources: List[str]
    articles: List[str]
    success: bool
    error: Optional[str] = None

# 전역 변수 (서버 시작 시 초기화)
law_agent: Optional[LawAgent] = None
knowledge_base: Optional[LawKnowledgeBase] = None

@app.on_event("startup")
async def startup_event():
    """서버 시작 시 법령 지식 베이스 초기화"""
    global law_agent, knowledge_base
    
    logger.info("🚀 법령 AI 서버 시작 중...")
    
    # API 키 확인
    api_key = os.environ.get('GEMINI_API_KEY')
    if not api_key:
        logger.error("❌ GEMINI_API_KEY 환경 변수가 설정되지 않았습니다.")
        raise RuntimeError("GEMINI_API_KEY가 필요합니다.")
    
    # 설정 초기화
    config = LawAgentConfig(
        model_name="gemini-2.0-flash-exp",
        chunk_size=800,
        chunk_overlap=200,
        top_k_results=7,
        temperature=0.1
    )
    
    # 법령 지식 베이스 생성
    knowledge_base = LawKnowledgeBase(config)
    
    # 법령 파일 경로 (backend 폴더 기준)
    base_dir = os.path.dirname(os.path.abspath(__file__))
    file_paths = [
    os.path.join(base_dir, "민법(법률)(제20432호)(20250131).pdf"),
    ]
    
    # 파일 존재 확인
    existing_files = [f for f in file_paths if os.path.exists(f)]
    if not existing_files:
        logger.error(f"❌ 법령 파일을 찾을 수 없습니다: {file_paths}")
        raise RuntimeError("법령 파일이 필요합니다.")
    
    # 지식 베이스 생성
    success = knowledge_base.create_knowledge_base(existing_files)
    
    if not success:
        logger.error("❌ 법령 지식 베이스 생성 실패")
        raise RuntimeError("지식 베이스 생성 실패")
    
    # 법령 에이전트 초기화
    law_agent = LawAgent(api_key, knowledge_base, config)
    
    logger.info("✅ 법령 AI 서버 준비 완료!")

@app.get("/")
async def root():
    """서버 상태 확인"""
    return {
        "message": "법령 AI 어시스턴트 API 서버",
        "status": "running",
        "version": "1.0.0"
    }

@app.get("/api/health")
async def health_check():
    """헬스 체크"""
    if law_agent is None or knowledge_base is None:
        raise HTTPException(status_code=503, detail="서버가 아직 준비되지 않았습니다.")
    
    return {
        "status": "healthy",
        "document_count": knowledge_base.document_count,
        "model": law_agent.config.model_name
    }

@app.post("/api/chat", response_model=AnswerResponse)
async def chat(request: QuestionRequest):
    """법령 질문에 답변"""
    if law_agent is None:
        raise HTTPException(status_code=503, detail="서버가 아직 준비되지 않았습니다.")
    
    try:
        logger.info(f"📩 질문 수신: {request.question}")
        
        # 답변 생성
        answer, sources, articles = law_agent.get_response(request.question)
        
        logger.info(f"✅ 답변 생성 완료")
        
        return AnswerResponse(
            answer=answer,
            sources=sources,
            articles=articles,
            success=True
        )
        
    except Exception as e:
        logger.error(f"❌ 오류 발생: {e}")
        return AnswerResponse(
            answer="",
            sources=[],
            articles=[],
            success=False,
            error=str(e)
        )

@app.post("/api/reset")
async def reset_conversation():
    """대화 히스토리 초기화"""
    if law_agent is None:
        raise HTTPException(status_code=503, detail="서버가 아직 준비되지 않았습니다.")
    
    law_agent.reset_history()
    logger.info("🔄 대화 히스토리 초기화됨")
    
    return {"message": "대화가 초기화되었습니다."}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "api_server:app",
        host="0.0.0.0",
        port=8000,
        reload=True  # 개발 중 자동 재시작
    )