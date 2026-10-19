from app.probing.celery_app import celery_app
from app.geo_gap.groq_provider import (
    generate_response as generate_groq_response,
    DEFAULT_MODEL as GROQ_DEFAULT_MODEL,
)
from app.probing.openrouter_provider import (
    generate_response as generate_openrouter_response,
    DEFAULT_MODEL as OPENROUTER_DEFAULT_MODEL,
)
from app.probing.provider_errors import ProviderRetryableError
from app.geo_gap.response_schema import LLMResponse
from app.geo_gap.response_store import append_response
from datetime import datetime, timezone
import os
from uuid import uuid4

from app.geo_gap.query_templates import build_queries
from app.probing.task_manifest import save_task_manifest

@celery_app.task(bind=True, max_retries=3)
def probe_prompt(
    self,
    prompt_record: dict,
    provider: str = "groq",
    model: str = GROQ_DEFAULT_MODEL,
    output_filename: str = "celery_probe_responses.jsonl",
    run_id: str = "",
):
    """Run one LLM probing request through the selected provider."""

    prompt = prompt_record["prompt"]

    try:
        if provider == "groq":
            response_text = generate_groq_response(prompt, model=model)

        elif provider == "openrouter":
            if model == GROQ_DEFAULT_MODEL:
                model = OPENROUTER_DEFAULT_MODEL

            response_text = generate_openrouter_response(prompt, model=model)

        else:
            raise ValueError(f"Unsupported provider: {provider}")

    except ProviderRetryableError as exc:
        # Prefer the provider's Retry-After delay. Otherwise use
        # exponential delays of 2, 4, and 8 seconds.
        countdown = exc.retry_after
        if countdown is None:
            countdown = min(60, 2 ** (self.request.retries + 1))

        print(
            f"Retryable {provider} failure for "
            f"{prompt_record.get('query_id')}: {exc}. "
            f"Retry {self.request.retries + 1}/"
            f"{self.max_retries} in {countdown} seconds."
        )

        raise self.retry(
            exc=exc,
            countdown=countdown,
        )

    response = LLMResponse(
        provider=provider,
        model=model,
        category=prompt_record.get("category", ""),
        query_id=prompt_record.get("query_id", ""),
        intent=prompt_record.get("intent", ""),
        prompt=prompt,
        response_text=response_text,
        product_mentions=[],
        prompt_id=prompt_record.get("prompt_id"),
        base_query_id=prompt_record.get("base_query_id"),
        persona=prompt_record.get("persona"),
        target_brands=prompt_record.get("target_brands", []),
        comparison_brands=prompt_record.get("comparison_brands"),
        run_id=run_id,
        timestamp_utc=datetime.now(timezone.utc).isoformat(),
    )

    output_path = append_response(
    response,
    output_filename,
    deduplicate=True,
    )

    return {
        "prompt_id": prompt_record.get("prompt_id"),
        "query_id": prompt_record.get("query_id"),
        "provider": provider,
        "model": model,
        "response_text": response_text,
        "saved_to": str(output_path),
    }

@celery_app.task(name="app.probing.tasks.dispatch_batch")
def dispatch_batch():
    """Queue a capped batch of prompts across configured providers."""

    category = os.getenv("GEO_GAP_CATEGORY", "All_Beauty")
    prompt_cap = max(
        1,
        int(os.getenv("GEO_GAP_PROMPT_CAP", "5")),
    )

    providers = [
        provider.strip().lower()
        for provider in os.getenv(
            "GEO_GAP_PROVIDERS",
            "groq,openrouter",
        ).split(",")
        if provider.strip()
    ]

    allowed_providers = {"groq", "openrouter"}
    if not providers or any(
        provider not in allowed_providers
        for provider in providers
    ):
        raise ValueError("Providers must be groq and/or openrouter.")

    queries = build_queries(category)[:prompt_cap]
    timestamp = datetime.now(timezone.utc)
    run_id = f"scheduled_{category}_{timestamp:%Y%m%dT%H%M%SZ}_{uuid4().hex[:8]}"
    manifest_filename = f"{run_id}_manifest.json"

    task_records = []

    for query in queries:
        for provider in providers:
            model = (
                GROQ_DEFAULT_MODEL
                if provider == "groq"
                else OPENROUTER_DEFAULT_MODEL
            )

            result = probe_prompt.apply_async(
                args=[query],
                kwargs={
                    "provider": provider,
                    "model": model,
                    "output_filename": (
                        f"{run_id}_{provider}_responses.jsonl"
                    ),
                    "run_id": run_id,
                },
            )

            task_records.append({
                "task_id": result.id,
                "prompt_id": query.get("prompt_id"),
                "query_id": query.get("query_id"),
                "category": query.get("category", category),
                "provider": provider,
                "model": model,
                "output_file": f"{run_id}_{provider}_responses.jsonl",
                "run_id": run_id,
            })
            save_task_manifest(task_records, manifest_filename)

    return {
        "run_id": run_id,
        "prompt_count": len(queries),
        "provider_count": len(providers),
        "task_count": len(task_records),
        "manifest": manifest_filename,
    }