"""Tests never inherit developer application credentials or model selection."""
import pytest
from pharma import config  # Load .env once, before the per-test isolation.

@pytest.fixture(autouse=True)
def isolated_model_configuration(monkeypatch):
    for key in ('PHARMA_API_KEY','GLM_API_KEY','ZHIPU_API_KEY','PHARMA_API_KEY_FILE','PHARMA_MODEL_KEY_FILE'):
        monkeypatch.delenv(key,raising=False)
    monkeypatch.setenv('PHARMA_MODEL','glm-5.3-flash')
    monkeypatch.setenv('PHARMA_MODEL_BASE_URL','https://open.bigmodel.cn/api/paas/v4')
    monkeypatch.setenv('PHARMA_MODEL_PROTOCOL','openai')
