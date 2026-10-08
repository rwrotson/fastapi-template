from cli_app.utils.emoji import Emoji


def test_emoji_values() -> None:
    assert Emoji.ROCKET == "🚀"
    assert Emoji.STOP_SIGN == "🛑"
    assert Emoji.SUNGLASSES == "😎"
    assert Emoji.PRAY == "🙏"
    assert {e.name for e in Emoji} == {"ROCKET", "STOP_SIGN", "SUNGLASSES", "PRAY"}
