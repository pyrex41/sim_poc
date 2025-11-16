"""Batch parse endpoint."""

from __future__ import annotations

import asyncio
from typing import Any, List

from fastapi import APIRouter, Depends, HTTPException, status

from backend.prompt_parser_service.api.v1.parse import process_parse_request
from backend.prompt_parser_service.core.dependencies import get_cache_manager, get_llm_provider_registry
from backend.prompt_parser_service.models.request import ParseRequest
from backend.prompt_parser_service.services.cache import CacheManager
from backend.prompt_parser_service.services.llm.base import LLMProvider

router = APIRouter()


@router.post("/parse/batch")
async def parse_batch(
    requests: List[ParseRequest],
    cache: CacheManager = Depends(get_cache_manager),
    llm_providers: dict[str, LLMProvider] = Depends(get_llm_provider_registry),
):
    if len(requests) > 10:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Batch size exceeds maximum of 10 prompts.",
        )

    async def _process(req: ParseRequest):
        return await process_parse_request(req, cache=cache, llm_providers=llm_providers)

    results = await asyncio.gather(*[_process(req) for req in requests], return_exceptions=True)
    formatted = []
    for req, result in zip(requests, results):
        if isinstance(result, Exception):
            formatted.append({"request": req, "status": "error", "error": str(result)})
        else:
            formatted.append({"request": req, "status": "success", "response": result})

    return {
        "status": "partial_success"
        if any(item["status"] == "error" for item in formatted)
        else "success",
        "results": formatted,
    }

