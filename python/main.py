"""WenForge Python Sidecar - AI写作引擎

FastAPI server that handles LLM generation requests.
Communicates with the Electron frontend via HTTP.
"""

import os
import sys
import logging
from contextlib import asynccontextmanager

# Ensure the python directory is on sys.path for direct module access
_python_dir = os.path.dirname(os.path.abspath(__file__))
if _python_dir not in sys.path:
    sys.path.insert(0, _python_dir)

from pathlib import Path
from fastapi import FastAPI, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from providers import OpenAIProvider, ClaudeProvider, LocalProvider, DeepSeekProvider
from config import get_config, update_config
from auto_writer import AutoWriter
from innovation import IdeaGenerator, InnovationScorer, IdeaComposer
from storage import ensure_dirs, load_settings, save_settings, list_projects, create_project, list_chapters, read_chapter, save_chapter, create_chapter, delete_chapter
from pipeline.api_routes import router as pipeline_router
from fact_engine.api_routes import router as fact_router

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("wenforge")

# Paths for serving the built frontend
_dist_dir = Path(_python_dir).parent / "dist"
_bootstrap_file = Path(_python_dir) / "bootstrap.js"


# Provider registry
_providers = {
    "openai": OpenAIProvider(),
    "claude": ClaudeProvider(),
    "deepseek": DeepSeekProvider(),
    "local": LocalProvider(),
}


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("=" * 50)
    logger.info("WenForge AI Engine starting...")
    logger.info("=" * 50)
    ensure_dirs()
    yield
    logger.info("WenForge AI Engine shutting down.")


app = FastAPI(title="WenForge AI Engine", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(pipeline_router)
app.include_router(fact_router)


# ---- Request/Response Models ----

class GenerateRequest(BaseModel):
    prompt: str
    context: str = ""
    model: str = ""
    provider: str = ""
    temperature: float = 0.7
    max_tokens: int = 4096


class ContinueRequest(BaseModel):
    text: str
    style: str = ""
    instruction: str = ""
    temperature: float = 0.8
    max_tokens: int = 2048


class ConfigureRequest(BaseModel):
    openai_key: str = ""
    openai_model: str = ""
    claude_key: str = ""
    claude_model: str = ""
    deepseek_key: str = ""
    deepseek_model: str = ""
    deepseek_endpoint: str = ""
    writing_model: str = ""
    polishing_model: str = ""
    local_endpoint: str = ""
    local_model: str = ""


class AutoOutlineRequest(BaseModel):
    genre: str = "玄幻"
    premise: str = ""
    protagonist: str = ""
    style: str = "流畅直白"
    total_chapters: int = 10
    chapter_length: str = "medium"


class AutoChapterRequest(BaseModel):
    outline: dict = {}
    chapter_index: int = 1
    chapter_outline: str = ""
    previous_summaries: list[str] = []
    config: dict = {}


class GenerateResponse(BaseModel):
    text: str
    token_count: int = 0
    cost: float = 0.0
    model: str = ""


class HealthResponse(BaseModel):
    status: str
    version: str = "0.1.0"


# ---- API Endpoints ----

@app.api_route("/api/health", methods=["GET", "POST"], response_model=HealthResponse)
async def health():
    return HealthResponse(status="ok")


@app.post("/api/configure")
async def configure(req: ConfigureRequest):
    """Update configuration from frontend settings."""
    data = {}
    if req.openai_key or req.openai_model:
        data["openai"] = {"api_key": req.openai_key, "model": req.openai_model}
    if req.claude_key or req.claude_model:
        data["claude"] = {"api_key": req.claude_key, "model": req.claude_model}
    if req.deepseek_key or req.deepseek_model:
        deepseek = {"api_key": req.deepseek_key, "model": req.deepseek_model}
        if req.deepseek_endpoint:
            deepseek["endpoint"] = req.deepseek_endpoint
        data["deepseek"] = deepseek
    if req.local_endpoint or req.local_model:
        data["local"] = {"endpoint": req.local_endpoint, "model": req.local_model}
    if req.writing_model:
        data["writing_model"] = req.writing_model
    if req.polishing_model:
        data["polishing_model"] = req.polishing_model

    update_config(data)
    logger.info(f"Configuration updated: {list(data.keys())}")
    return {"status": "ok"}


@app.post("/api/generate", response_model=GenerateResponse)
async def generate(req: GenerateRequest):
    """Generate text from a prompt."""
    cfg = get_config()

    # Determine which provider and model to use
    provider_name = req.provider or _detect_provider(req.model, cfg)
    model = req.model or _get_default_model(provider_name, cfg)

    provider = _providers.get(provider_name)
    if not provider:
        raise HTTPException(status_code=400, detail=f"Unknown provider: {provider_name}")

    # Check if provider has API key configured
    if provider_name == "openai" and not cfg.openai.api_key:
        raise HTTPException(status_code=400, detail="OpenAI API Key 未配置，请在设置中填写")
    if provider_name == "claude" and not cfg.claude.api_key:
        raise HTTPException(status_code=400, detail="Claude API Key 未配置，请在设置中填写")
    if provider_name == "deepseek" and not cfg.deepseek.api_key:
        raise HTTPException(status_code=400, detail="DeepSeek API Key 未配置，请在设置中填写")

    # Build messages
    messages = []
    if req.context:
        messages.append({"role": "user", "content": f"以下是当前的写作上下文：\n{req.context}"})
        messages.append({"role": "assistant", "content": "好的，我理解了上下文。"})

    system_prompt = (
        "你是一位专业的中国网络文学作家助手。请根据要求创作网文内容。\n"
        "要求：\n"
        "1. 使用地道的中文网文风格，自然流畅\n"
        "2. 避免使用AI常见的表达方式（如'值得注意的是''然而'等）\n"
        "3. 对话要生动自然，符合人物性格\n"
        "4. 描写要细致但不拖沓\n"
        "5. 注意段落节奏，长短句结合"
    )

    messages.append({"role": "user", "content": req.prompt})

    logger.info(f"Generating with {provider_name}/{model} (temp={req.temperature})")

    try:
        result = provider.generate(
            type('Params', (), {
                'messages': messages,
                'temperature': req.temperature,
                'max_tokens': req.max_tokens,
                'model': model,
                'system': system_prompt,
            })()
        )

        logger.info(f"Generated {result.token_count} tokens, cost=${result.cost:.4f}")
        return GenerateResponse(
            text=result.text,
            token_count=result.token_count,
            cost=result.cost,
            model=result.model,
        )
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Generation error: {error_msg}")
        raise HTTPException(status_code=500, detail=f"生成失败: {error_msg}")


@app.post("/api/continue", response_model=GenerateResponse)
async def continue_writing(req: ContinueRequest):
    """Continue writing from existing text."""
    cfg = get_config()

    # Use writing model (economical) for continuation
    provider_name, model = _parse_model_route(cfg.writing_model)
    provider = _providers.get(provider_name)

    if not provider:
        raise HTTPException(status_code=400, detail=f"Unknown provider: {provider_name}")

    if provider_name == "openai" and not cfg.openai.api_key:
        raise HTTPException(status_code=400, detail="OpenAI API Key 未配置")
    if provider_name == "claude" and not cfg.claude.api_key:
        raise HTTPException(status_code=400, detail="Claude API Key 未配置")
    if provider_name == "deepseek" and not cfg.deepseek.api_key:
        raise HTTPException(status_code=400, detail="DeepSeek API Key 未配置")
    # Truncate context if too long
    context = req.text
    if len(context) > 6000:
        context = context[-6000:]

    style_hint = ""
    if req.style:
        style_hint = f"\n注意保持以下风格特征：{req.style}"

    instruction = req.instruction or "请根据以上内容，自然地续写下一段，保持风格一致"

    system_prompt = (
        "你是一位专业的中国网络文学作家。请根据前文内容自然续写。\n"
        "要求：\n"
        "1. 保持与前文风格一致\n"
        "2. 情节发展合理自然\n"
        "3. 语言流畅，符合网文风格\n"
        "4. 避免AI常见表达方式\n"
        "5. 注意人物性格和关系的一致性"
    )

    messages = [
        {"role": "user", "content": f"以下是当前小说内容：\n\n{context}\n\n{instruction}{style_hint}"}
    ]

    logger.info(f"Continuing with {provider_name}/{model}")

    try:
        result = provider.generate(
            type('Params', (), {
                'messages': messages,
                'temperature': req.temperature,
                'max_tokens': req.max_tokens,
                'model': model,
                'system': system_prompt,
            })()
        )

        logger.info(f"Generated {result.token_count} tokens")
        return GenerateResponse(
            text=result.text,
            token_count=result.token_count,
            cost=result.cost,
            model=result.model,
        )
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Continue error: {error_msg}")
        raise HTTPException(status_code=500, detail=f"续写失败: {error_msg}")


@app.post("/api/auto/outline")
async def auto_outline(req: AutoOutlineRequest):
    """Step 1: Generate story outline from user config."""
    cfg = get_config()
    provider_name, model = _parse_model_route(cfg.writing_model)
    provider = _providers.get(provider_name)

    if not provider:
        raise HTTPException(status_code=400, detail="无可用的 AI 模型，请先在设置中配置 API Key")

    # Check API keys for each provider type
    if provider_name == "openai" and not cfg.openai.api_key:
        raise HTTPException(status_code=400, detail="OpenAI API Key 未配置，请在设置中填写")
    if provider_name == "claude" and not cfg.claude.api_key:
        raise HTTPException(status_code=400, detail="Claude API Key 未配置，请在设置中填写")
    if provider_name == "deepseek" and not cfg.deepseek.api_key:
        raise HTTPException(status_code=400, detail="DeepSeek API Key 未配置，请在设置中填写")

    writer = AutoWriter(provider, model)
    try:
        logger.info(f"开始生成大纲 ({req.total_chapters}章, {req.genre}/{req.style})")
        outline = writer.generate_outline({
            "genre": req.genre,
            "premise": req.premise,
            "protagonist": req.protagonist,
            "style": req.style,
            "total_chapters": req.total_chapters,
            "chapter_length": req.chapter_length,
        })
        logger.info(f"大纲生成完成: {outline.get('title', '')}")
        return {"outline": outline, "success": True}
    except Exception as e:
        logger.error(f"大纲生成失败: {e}")
        raise HTTPException(status_code=500, detail=f"大纲生成失败: {str(e)}")


@app.post("/api/auto/chapter")
async def auto_chapter(req: AutoChapterRequest):
    """Step 2: Generate a single chapter based on outline."""
    cfg = get_config()
    provider_name, model = _parse_model_route(cfg.writing_model)
    provider = _providers.get(provider_name)

    if not provider:
        raise HTTPException(status_code=400, detail="无可用的 AI 模型")
    if provider_name == "openai" and not cfg.openai.api_key:
        raise HTTPException(status_code=400, detail="OpenAI API Key 未配置")
    if provider_name == "claude" and not cfg.claude.api_key:
        raise HTTPException(status_code=400, detail="Claude API Key 未配置")
    if provider_name == "deepseek" and not cfg.deepseek.api_key:
        raise HTTPException(status_code=400, detail="DeepSeek API Key 未配置")

    writer = AutoWriter(provider, model)
    try:
        logger.info(f"开始生成第 {req.chapter_index} 章")
        text = writer.generate_chapter(
            outline=dict(req.outline),
            index=req.chapter_index,
            chapter_outline=req.chapter_outline,
            prev_summaries=list(req.previous_summaries),
            config=dict(req.config),
        )
        logger.info(f"第 {req.chapter_index} 章生成完成 ({len(text)} 字)")
        # Extract title from first non-empty line
        lines = text.strip().split('\n')
        title = ''
        remaining = text.strip()
        for i, line in enumerate(lines):
            stripped = line.strip()
            if stripped:
                title = stripped
                remaining = '\n'.join(lines[i+1:]).strip()
                break
        return {"text": remaining or text, "title": title, "success": True}
    except Exception as e:
        logger.error(f"第 {req.chapter_index} 章生成失败: {e}")
        raise HTTPException(status_code=500, detail=f"第 {req.chapter_index} 章生成失败: {str(e)}")


# ── Innovation API (创新思路库) ──────────────────────────────────


class InnovationGenerateRequest(BaseModel):
    idea_type: str = ""
    genre: str = "玄幻"
    style: str = "流畅直白"
    keywords: list[str] = []
    avoid_patterns: list[str] = []
    count: int = 3
    provider_override: str = ""
    model_override: str = ""


class InnovationExpandRequest(BaseModel):
    idea: dict = {}


class InnovationComposeRequest(BaseModel):
    ideas: list[dict] = []
    genre: str = "玄幻"
    style: str = "流畅直白"


class InnovationScoreRequest(BaseModel):
    ideas: list[dict] = []


@app.post("/api/innovation/generate")
async def innovation_generate(req: InnovationGenerateRequest):
    """Generate innovation ideas across five dimensions."""
    cfg = get_config()
    provider_name = req.provider_override or "claude"
    model = req.model_override or "claude-haiku-3-5-20251022"

    # Fallback: detect from configured writing model
    if not req.provider_override:
        provider_name, model = _parse_model_route(cfg.writing_model)

    provider = _providers.get(provider_name)
    if not provider:
        raise HTTPException(400, f"Unknown provider: {provider_name}")

    if provider_name in ("openai", "claude", "deepseek") and not getattr(getattr(cfg, provider_name), "api_key", None):
        raise HTTPException(400, f"{provider_name} API Key not configured")

    generator = IdeaGenerator(provider, model)
    try:
        logger.info(f"Generating innovation ideas: type={req.idea_type or 'all'}, genre={req.genre}")
        result = generator.generate(
            idea_type=req.idea_type or None,
            genre=req.genre,
            style=req.style,
            keywords=req.keywords,
            avoid_patterns=req.avoid_patterns,
            count=req.count,
        )
        return {"ideas": result, "success": True}
    except Exception as e:
        logger.error(f"Innovation generate failed: {e}")
        raise HTTPException(500, f"Innovation generation failed: {str(e)}")


@app.post("/api/innovation/expand")
async def innovation_expand(req: InnovationExpandRequest):
    """Expand an idea into full story outline."""
    cfg = get_config()
    provider_name, model = _parse_model_route(cfg.writing_model)
    provider = _providers.get(provider_name)
    if not provider:
        raise HTTPException(400, "No AI model available")

    if provider_name in ("openai", "claude", "deepseek") and not getattr(getattr(cfg, provider_name), "api_key", None):
        raise HTTPException(400, f"{provider_name} API Key not configured")

    composer = IdeaComposer(provider, model)
    try:
        logger.info(f"Expanding idea: {req.idea.get('title', 'unknown')}")
        outline = composer.expand(req.idea)
        return {"outline": outline, "success": True}
    except Exception as e:
        logger.error(f"Expand failed: {e}")
        raise HTTPException(500, f"Expand failed: {str(e)}")


@app.post("/api/innovation/compose")
async def innovation_compose(req: InnovationComposeRequest):
    """Compose multiple ideas into a unified story framework."""
    cfg = get_config()
    provider_name, model = _parse_model_route(cfg.writing_model)
    provider = _providers.get(provider_name)
    if not provider:
        raise HTTPException(400, "No AI model available")

    if provider_name in ("openai", "claude", "deepseek") and not getattr(getattr(cfg, provider_name), "api_key", None):
        raise HTTPException(400, f"{provider_name} API Key not configured")

    composer = IdeaComposer(provider, model)
    try:
        logger.info(f"Composing {len(req.ideas)} ideas into story framework")
        framework = composer.compose(req.ideas, genre=req.genre, style=req.style)
        return {"framework": framework, "success": True}
    except Exception as e:
        logger.error(f"Compose failed: {e}")
        raise HTTPException(500, f"Compose failed: {str(e)}")


@app.post("/api/innovation/score")
async def innovation_score(req: InnovationScoreRequest):
    """Score innovation ideas."""
    cfg = get_config()
    provider_name, model = _parse_model_route(cfg.writing_model)
    provider = _providers.get(provider_name)
    if not provider:
        raise HTTPException(400, "No AI model available")

    if provider_name in ("openai", "claude", "deepseek") and not getattr(getattr(cfg, provider_name), "api_key", None):
        raise HTTPException(400, f"{provider_name} API Key not configured")

    scorer = InnovationScorer(provider, model)
    try:
        logger.info(f"Scoring {len(req.ideas)} ideas")
        scored = scorer.batch_score(req.ideas)
        return {"ideas": scored, "success": True}
    except Exception as e:
        logger.error(f"Scoring failed: {e}")
        raise HTTPException(500, f"Scoring failed: {str(e)}")


# ---- Storage API (replaces Electron IPC) ----

@app.get("/api/storage/settings")
async def api_load_settings():
    return load_settings()


@app.post("/api/storage/settings")
async def api_save_settings(settings: dict = Body(...)):
    ok = save_settings(settings)
    return {"ok": ok}


@app.get("/api/storage/projects")
async def api_list_projects():
    return list_projects()


@app.post("/api/storage/projects")
async def api_create_project(data: dict = Body(...)):
    return create_project(data.get("title", ""), data.get("author", ""), data.get("genre", ""))


@app.get("/api/storage/projects/{name}/chapters")
async def api_list_chapters(name: str):
    return list_chapters(name)


@app.post("/api/storage/projects/{name}/chapters")
async def api_create_chapter(name: str, data: dict = Body(...)):
    return create_chapter(name, data.get("title", ""))


@app.get("/api/storage/projects/{name}/chapters/{file:path}")
async def api_read_chapter(name: str, file: str):
    return read_chapter(name, file)


@app.put("/api/storage/projects/{name}/chapters/{file:path}")
async def api_save_chapter(name: str, file: str, data: dict = Body(...)):
    ok = save_chapter(name, file, data.get("content", ""))
    return {"ok": ok}


@app.delete("/api/storage/projects/{name}/chapters/{file:path}")
async def api_delete_chapter(name: str, file: str):
    ok = delete_chapter(name, file)
    return {"ok": ok}


# ---- Serve Built Frontend ----

@app.get("/bootstrap.js")
async def serve_bootstrap():
    """Serve the browser-side polyfill for window.wenforge."""
    if _bootstrap_file.exists():
        return FileResponse(str(_bootstrap_file), media_type="application/javascript")
    return HTMLResponse("/* bootstrap not found */", status_code=404)


@app.get("/assets/{file_path:path}")
async def serve_assets(file_path: str):
    """Serve built frontend assets (JS, CSS, etc.)."""
    asset = _dist_dir / "assets" / file_path
    if asset.exists():
        return FileResponse(str(asset))
    raise HTTPException(status_code=404, detail="Asset not found")


@app.get("/")
async def serve_index():
    """Serve main HTML with bootstrap.js injected."""
    index_path = _dist_dir / "index.html"
    if not index_path.exists():
        return HTMLResponse(
            "<h1>Frontend not built. Run: npm run build</h1>",
            status_code=404,
        )
    html = index_path.read_text("utf-8")
    bootstrap_script = '</head><script src="/bootstrap.js"></script>'
    html = html.replace("</head>", bootstrap_script)
    return HTMLResponse(html)


# ---- Helper Functions ----

def _detect_provider(model: str, cfg) -> str:
    """Detect provider from model name."""
    if not model:
        if cfg.claude.api_key:
            return "claude"
        elif cfg.deepseek.api_key:
            return "deepseek"
        elif cfg.openai.api_key:
            return "openai"
        return "claude"
    model_lower = model.lower()
    if "gpt" in model_lower or "o1" in model_lower or "o3" in model_lower:
        return "openai"
    if "claude" in model_lower:
        return "claude"
    if "deepseek" in model_lower:
        return "deepseek"
    if "qwen" in model_lower or "llama" in model_lower:
        return "local"
    return "openai"


def _get_default_model(provider: str, cfg) -> str:
    """Get default model for a provider."""
    if provider == "openai":
        return cfg.openai.model or "gpt-4o-mini"
    if provider == "claude":
        return cfg.claude.model or "claude-haiku-3-5-20251022"
    if provider == "deepseek":
        return cfg.deepseek.model or "deepseek-v4-flash"
    if provider == "local":
        return cfg.local.model or "qwen2.5:7b"
    return "gpt-4o-mini"


def _parse_model_route(route: str) -> tuple[str, str]:
    """Parse a model route like 'claude-haiku-3-5-20251022' into (provider, model)."""
    route_lower = route.lower()
    if route_lower.startswith("gpt") or route_lower.startswith("o1") or route_lower.startswith("o3"):
        return ("openai", route)
    if route_lower.startswith("claude"):
        return ("claude", route)
    if "deepseek" in route_lower:
        return ("deepseek", route)
    # Local models
    return ("local", route)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8765)
