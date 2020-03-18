from delatore.configuration import DEFAULT_INSTANCE_CONFIG, InstanceConfig, read_config


def test_config_load(config_file, token, chat_id, influx_password, awx_auth_token, alerta_api_key, alerta_service):
    new = read_config(config_file)
    assert new != DEFAULT_INSTANCE_CONFIG
    assert new == InstanceConfig(token, chat_id, influx_password, awx_auth_token, alerta_api_key, alerta_service)


def test_config_load_empty(empty_env_vars, empty_config_file):
    cfg = read_config(empty_config_file)
    assert cfg.chat_id is None
    assert cfg.token is None
