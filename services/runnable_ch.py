class Runnable:
    def __call__(self, data):
        raise NotImplementedError

    def __ror__(self, left):
        # dict -> RunnableMap 자동 변환
        if isinstance(left, dict):
            left = RunnableMap(left)
        return RunnableSequence([left, self])


class RunnableMap(Runnable):
    def __init__(self, mapping):
        self.mapping = mapping

    def __call__(self, data):
        result = {}
        for k, v in self.mapping.items():
            result[k] = v(data) if callable(v) else v
        return result


class RunnableSequence(Runnable):
    def __init__(self, steps):
        self.steps = steps

    def __call__(self, data):
        for step in self.steps:
            data = step(data)
        return data


class Printer(Runnable):
    def __call__(self, data):
        print("Printer got:", data)
        return data


# === 사용 예시 ===
pipeline = {"country": lambda x: x.get("country", "Korea")} | Printer()
pipeline({"country1": "Japan"})
