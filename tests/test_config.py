from delatore.configuration import BOT_CONFIG, BotConfig, read_config


def test_config_load(config_file, token, chat_id):
    new = read_config(config_file)
    assert new != BOT_CONFIG
    assert new == BotConfig(token, chat_id)


def test_config_load_empty(empty_env_vars):
    file_name = "fl"
    with open(file_name, "w+") as file:
        file.write("[DEFAULT]\n")
    cfg = read_config(file_name)
    assert cfg.chat_id is None
    assert cfg.token is None
