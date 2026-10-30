import json


class OpenUiWriter:
    def answer(self, sentence: str, widget_ids: list[str]) -> str:
        names = [f"w{index}" for index in range(1, len(widget_ids) + 1)]
        lines = [f"root = Stack({self._list(['intro', *names])})", f"intro = Text({json.dumps(sentence, ensure_ascii=False)})"]
        lines += [f"{name} = Widget({json.dumps(widget_id, ensure_ascii=False)})" for name, widget_id in zip(names, widget_ids)]
        return "\n".join(lines)

    def board(self, sentence: str, name: str, widget_ids: list[str]) -> str:
        ids = "[" + ", ".join(json.dumps(widget_id, ensure_ascii=False) for widget_id in widget_ids) + "]"
        return "\n".join(
            [
                "root = Stack([intro, board])",
                f"intro = Text({json.dumps(sentence, ensure_ascii=False)})",
                f"board = Board({json.dumps(name, ensure_ascii=False)}, {ids})",
            ]
        )

    def _list(self, names: list[str]) -> str:
        return "[" + ", ".join(names) + "]"
