class Spring83Exception(Exception):
    status: int

    def __init__(self, *args, status: int | None = None):
        super().__init__(*args)
        if status is None:
            raise ValueError("Status code must be set for custom exception")

        self.status = status
