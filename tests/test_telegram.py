from services.telegram.config import TelegramConfig


def test_telegram_configuration_contract_exists():
    config = TelegramConfig()
    assert config.token is None or isinstance(config.token, str)
    assert isinstance(config.enabled, bool)
