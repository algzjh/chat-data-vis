"""Base class for all prompts."""


class Prompt:
    """Base class to implement a new Prompt"""

    context = None
    instructions = {}

    def __init__(self, **kwargs):
        """
        __init__ method of Base class of Prompt Module
        Args:
            **kwargs: Inferred Keyword Arguments
        """
        if kwargs:
            self.instructions = kwargs

    def __str__(self):
        if self.context is None:
            print("No context found for this prompt")

        return self.context.format(**self.instructions)
