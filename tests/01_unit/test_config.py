from delatore.configuration import BOT_CONFIG, BotConfig, read_config


def test_config_load(config_file, token, chat_id, influx_password, awx_auth_token):
    new = read_config(config_file)
    assert new != BOT_CONFIG
    assert new == BotConfig(token, chat_id, influx_password, awx_auth_token)


def test_config_load_empty(empty_env_vars, empty_config_file):
    cfg = read_config(empty_config_file)
    assert cfg.chat_id is None
    assert cfg.token is None
