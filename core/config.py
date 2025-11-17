# Location: scripts/tbcv/core/config.py
"""
Configuration management for TBCV system (Pydantic v2 compatible).

WHAT CHANGED (important):
- When applying YAML overrides, we now DEEP-MERGE into nested BaseSettings
  models (e.g., cache.l1 / cache.l2) instead of overwriting them with dicts.
- This prevents situations where `settings.cache.l1` becomes a plain dict,
  which caused downstream AttributeErrors (e.g., `.enabled` not found).
"""

import os
import yaml
from pathlib import Path
from typing import Dict, List, Any
from functools import lru_cache

# Pydantic v2: BaseSettings lives in pydantic_settings
try:
    # Preferred: Pydantic Settings
    from pydantic_settings import BaseSettings, SettingsConfigDict
except ImportError:
    try:
        # Pydantic v2 fallback: BaseModel instead of BaseSettings
        from pydantic import BaseModel

        class BaseSettings(BaseModel):
            class Config:
                env_file = '.env'
                env_file_encoding = 'utf-8'

        class SettingsConfigDict(dict):
            pass
    except ImportError:
        # Minimal fallback when neither package is available
        class BaseSettings:
            pass

        class SettingsConfigDict(dict):
            pass


# -------------------------
# Settings model definitions
# -------------------------

class AgentConfig(BaseSettings):
    enabled: bool = True
    max_memory_mb: int = 512
    max_cpu_percent: int = 80
    max_concurrent: int = 5
    timeout_seconds: int = 300

class FuzzyDetectorConfig(AgentConfig):
    similarity_threshold: float = 0.85
    context_window_chars: int = 200
    max_patterns: int = 500
    fuzzy_algorithms: List[str] = ["levenshtein", "jaro_winkler"]
    pattern_cache_size: int = 1000

class ContentValidatorConfig(AgentConfig):
    html_sanitization: bool = True
    link_validation: bool = True
    link_timeout_seconds: int = 5
    image_validation: bool = False
    yaml_strict_mode: bool = False
    markdown_extensions: List[str] = ["tables", "fenced_code", "codehilite"]

class ContentEnhancerConfig(AgentConfig):
    auto_link_plugins: bool = True
    add_info_text: bool = True
    prevent_duplicate_links: bool = True
    link_template: str = "https://products.aspose.com/words/net/plugins/{slug}/"
    info_text_template: str = "*This code requires the **{plugin_name}** plugin.*"
    # Maximum allowed absolute rewrite ratio when enhancing content. A value of 0.3 means
    # enhancements may increase or decrease the original length by up to 30%. Beyond this
    # threshold, the enhancer will gate the changes and return the original content.
    rewrite_ratio_threshold: float = 0.5
    # List of case-insensitive phrases that must not appear in the enhanced content. If any
    # blocked topic is found after applying enhancements, the enhancer will reject the result.
    blocked_topics: List[str] = []

class OrchestratorConfig(AgentConfig):
    max_concurrent_workflows: int = 50
    workflow_timeout_seconds: int = 3600
    checkpoint_interval_seconds: int = 30
    retry_attempts: int = 3
    retry_backoff_base: float = 1.0

class TruthManagerConfig(AgentConfig):
    auto_reload: bool = True
    validation_strict: bool = False
    cache_ttl_seconds: int = 604800  # 7 days
    truth_directories: List[str] = ["./truth"]

class CacheConfig(BaseSettings):
    """Two-level cache settings: L1 (memory) and L2 (persistent DB)."""

    class L1Config(BaseSettings):
        enabled: bool = True
        max_entries: int = 1000
        max_memory_mb: int = 256
        ttl_seconds: int = 3600
        cleanup_interval_seconds: int = 300
        eviction_policy: str = "LRU"

    class L2Config(BaseSettings):
        enabled: bool = True
        database_path: str = "./data/cache/tbcv_cache.db"
        max_size_mb: int = 1024
        cleanup_interval_hours: int = 24
        compression_enabled: bool = True
        compression_threshold_bytes: int = 1024

    l1: L1Config = L1Config()
    l2: L2Config = L2Config()

class ServerConfig(BaseSettings):
    host: str = "localhost"
    port: int = 8080
    enable_cors: bool = True
    cors_origins: List[str] = ["http://localhost:3000"]
    request_timeout_seconds: int = 30
    max_request_size_mb: int = 50
    websocket_ping_interval: int = 30
    websocket_ping_timeout: int = 10

class SystemConfig(BaseSettings):
    name: str = "TBCV"
    version: str = "1.0.0"
    environment: str = "development"
    debug: bool = True
    log_level: str = "info"
    timezone: str = "UTC"
    data_directory: str = "./data"
    temp_directory: str = "./data/temp"

class PerformanceConfig(BaseSettings):
    max_concurrent_workflows: int = 50
    worker_pool_size: int = 4
    memory_limit_mb: int = 2048
    cpu_limit_percent: int = 80
    file_size_limits: Dict[str, int] = {"small_kb": 5, "medium_kb": 50, "large_kb": 1000}
    response_time_targets: Dict[str, int] = {"small_file_ms": 300, "medium_file_ms": 1000, "large_file_ms": 3000}

class ValidationLLMThresholds(BaseSettings):
    """
    Thresholds for LLM gating decisions. Values must be between 0.0 and 1.0.

    downgrade_threshold: issues with a score below this value will be downgraded.
    confirm_threshold: scores between downgrade_threshold and this value are confirmed.
    upgrade_threshold: scores above this value will be escalated.

    Default values are chosen conservatively. You can override them in the
    configuration file or via environment variables (e.g.,
    TBCV_VALIDATION__LLM_THRESHOLDS__DOWNGRADE_THRESHOLD).
    """
    downgrade_threshold: float = 0.2
    confirm_threshold: float = 0.5
    upgrade_threshold: float = 0.8


class LLMConfig(BaseSettings):
    """Global toggle and settings for LLM validation."""
    enabled: bool = True


class ValidationConfig(BaseSettings):
    """
    Control the multi-stage validation pipeline.

    mode:
      - "two_stage": run heuristic/fuzzy validation first and then LLM validation (default).
      - "heuristic_only": run only heuristic/fuzzy validation.
      - "llm_only": run only LLM validation, skipping heuristics.
    llm_thresholds: thresholds used to gate heuristic issues when LLM is available.
    """
    mode: str = "two_stage"
    llm_thresholds: ValidationLLMThresholds = ValidationLLMThresholds()


class TBCVSettings(BaseSettings):
    """Top-level settings composed of nested config models."""
    model_config = SettingsConfigDict(env_prefix="TBCV_", case_sensitive=False, env_file=".env")

    system: SystemConfig = SystemConfig()
    server: ServerConfig = ServerConfig()
    cache: CacheConfig = CacheConfig()
    performance: PerformanceConfig = PerformanceConfig()

    fuzzy_detector: FuzzyDetectorConfig = FuzzyDetectorConfig()
    content_validator: ContentValidatorConfig = ContentValidatorConfig()
    content_enhancer: ContentEnhancerConfig = ContentEnhancerConfig()
    orchestrator: OrchestratorConfig = OrchestratorConfig()
    truth_manager: TruthManagerConfig = TruthManagerConfig()

    # Global LLM settings (enable/disable)
    llm: LLMConfig = LLMConfig()
    # Validation pipeline settings
    validation: ValidationConfig = ValidationConfig()

    truth_default_family: str = "words"
    truth_files: Dict[str, str] = {
        "words": "./truth/aspose_words_plugins_truth.json",
        "combinations": "./truth/aspose_words_plugins_combinations.json"
    }

    workflow_types: List[str] = ["validate_file", "validate_directory", "full_validation", "content_update"]
    workflow_checkpoints: List[str] = [
        "workflow_start","detection_start","fuzzy_analysis","context_analysis",
        "detection_complete","validation_start","validation_complete",
        "enhancement_start","enhancement_complete","workflow_complete"
    ]

    database_url: str = "sqlite:///./data/tbcv.db"
    database_echo: bool = False

    log_level: str = "INFO"
    log_format: str = "json"
    log_file_path: str = "./data/logs/tbcv.log"
    log_max_file_size_mb: int = 100
    log_backup_count: int = 5

# -----------------
# YAML load helpers
# -----------------

def load_config_from_yaml(config_path: str = "config/main.yaml") -> Dict[str, Any]:
    """Load a YAML file into a dict. Missing file → empty dict."""
    p = Path(config_path)
    if not p.exists():
        return {}
    with p.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}

def _deep_apply_dict_to_model(model_obj: Any, data: Dict[str, Any]) -> None:
    """
    Recursively apply dict `data` onto a Pydantic BaseSettings model `model_obj`.
    - If the target attribute is itself a BaseSettings, we recurse into it.
    - If the target attribute is a simple value (int/str/bool/list/dict), we set it directly.
    - This preserves model TYPES (no accidental dict replacement).
    """
    for key, value in (data or {}).items():
        if not hasattr(model_obj, key):
            # Unknown key in YAML → ignore safely
            continue

        current = getattr(model_obj, key)

        # Recurse if nested model and source is a dict
        if isinstance(current, BaseSettings) and isinstance(value, dict):
            _deep_apply_dict_to_model(current, value)
        else:
            # Directly assign (primitive or replacing with supported type)
            setattr(model_obj, key, value)

def merge_configs(base_config: Dict[str, Any], override_config: Dict[str, Any]) -> Dict[str, Any]:
    """Dict → dict merge. (Used only for plain dicts before applying to models.)"""
    merged = dict(base_config or {})
    for k, v in (override_config or {}).items():
        if k in merged and isinstance(merged[k], dict) and isinstance(v, dict):
            merged[k] = merge_configs(merged[k], v)
        else:
            merged[k] = v
    return merged

# --------------
# Public getters
# --------------

@lru_cache()
def get_settings() -> TBCVSettings:
    """
    Create a TBCVSettings instance and apply YAML overrides *deeply* so nested
    models (e.g., cache.l1) remain model instances, not plain dicts.
    """
    # 1) Load base YAML and optional environment overlay
    yaml_config = load_config_from_yaml("config/main.yaml")

    environment = os.getenv("TBCV_ENVIRONMENT", "development")
    env_path = f"config/environments/{environment}.yaml"
    env_config = load_config_from_yaml(env_path)

    merged_yaml = merge_configs(yaml_config, env_config)

    # After: merged_yaml = merge_configs(app_yaml, env_yaml)
    settings = TBCVSettings()

    # Deep-apply YAML onto the model.
    # 1) Special-case: support nested `agents:` sections (legacy & human-friendly shape)
    agents_section = (merged_yaml or {}).get("agents", {})
    if isinstance(agents_section, dict):
        for agent_key, agent_cfg in agents_section.items():
            if hasattr(settings, agent_key) and isinstance(agent_cfg, dict):
                _deep_apply_dict_to_model(getattr(settings, agent_key), agent_cfg)

    # 2) Apply regular top-level sections (performance, server, fuzzy_detector, etc.)
    for top_key, section in (merged_yaml or {}).items():
        if top_key == "agents":
            continue  # already handled above
        if hasattr(settings, top_key):
            target = getattr(settings, top_key)
            if isinstance(target, BaseSettings) and isinstance(section, dict):
                _deep_apply_dict_to_model(target, section)
            else:
                setattr(settings, top_key, section)

    return settings


def get_config_value(key_path: str, default: Any = None) -> Any:
    """Dot-path lookup (e.g., 'cache.l1.ttl_seconds'), returns `default` if missing."""
    settings = get_settings()
    value: Any = settings
    try:
        for key in key_path.split("."):
            value = getattr(value, key) if hasattr(value, key) else value[key]
        return value
    except Exception:
        return default

def validate_configuration() -> List[str]:
    """Create directories, verify truth files, basic sanity checks."""
    settings = get_settings()
    issues: List[str] = []

    # Ensure data & temp dirs exist
    for path_str in [settings.system.data_directory, settings.system.temp_directory]:
        path = Path(path_str)
        try:
            path.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            issues.append(f"Cannot create directory {path}: {e}")

    # Truth files exist?
    for _, truth_path in settings.truth_files.items():
        if not Path(truth_path).exists():
            issues.append(f"Truth file not found: {truth_path}")

    # L2 cache directory exists?
    if settings.cache.l2.enabled:
        cache_dir = Path(settings.cache.l2.database_path).parent
        try:
            cache_dir.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            issues.append(f"Cannot create cache directory {cache_dir}: {e}")

    # Performance constraints sanity
    if settings.performance.worker_pool_size > settings.performance.max_concurrent_workflows:
        issues.append("Worker pool size exceeds max concurrent workflows")
    if settings.performance.memory_limit_mb < 512:
        issues.append("Memory limit too low, minimum 512MB recommended")

    return issues

if __name__ == "__main__":
    s = get_settings()
    print(f"TBCV settings loaded for environment: {s.system.environment}")
