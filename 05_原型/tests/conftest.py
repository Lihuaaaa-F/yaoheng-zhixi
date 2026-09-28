"""Tests never inherit developer application credentials or model selection."""
import pytest
import os
from pharma import config  # Load .env once, before the per-test isolation.

@pytest.fixture(autouse=True)
def isolated_model_configuration(monkeypatch, tmp_path):
    for key in ('PHARMA_API_KEY','GLM_API_KEY','ZHIPU_API_KEY','PHARMA_API_KEY_FILE','PHARMA_MODEL_KEY_FILE'):
        monkeypatch.delenv(key,raising=False)
    for key in list(os.environ):
        if key == 'PHARMA_MODEL_ROUTES' or any(key.startswith('PHARMA_MODEL_' + role + '_')
                for role in ('ASSISTANT', 'ANALYSIS', 'EXTRACTION', 'NARRATIVE', 'DECISION')):
            monkeypatch.delenv(key, raising=False)
    from pharma import model_settings
    monkeypatch.setattr(model_settings, 'SETTINGS_PATH', tmp_path / 'isolated-model-settings.json')
    monkeypatch.setattr(model_settings, 'KEYS_DIR', tmp_path / 'isolated-model-keys')
    monkeypatch.setenv('PHARMA_MODEL','glm-5.3-flash')
    monkeypatch.setenv('PHARMA_MODEL_BASE_URL','https://open.bigmodel.cn/api/paas/v4')
    monkeypatch.setenv('PHARMA_MODEL_PROTOCOL','openai')
