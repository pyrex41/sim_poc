"""Providers endpoint."""

from fastapi import APIRouter, Depends

from backend.prompt_parser_service.core.dependencies import get_llm_provider_registry

router = APIRouter()


@router.get("/providers")
async def list_providers(providers=Depends(get_llm_provider_registry)):
    data = []
    for name, provider in providers.items():
        data.append(
            {
                "id": name,
                "name": provider.__class__.__name__,
                "estimated_latency_ms": provider.get_estimated_latency(),
            }
        )
    return {"providers": data}

