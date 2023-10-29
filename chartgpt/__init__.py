from .chartgpt import ChartGPT


class Chart:
    """Main ChartGPT object.

    This object is used to generate charts from a DataFrame. It can be used in \
    two ways:

    1. To generate a chart from a DataFrame with OPENAI_API_KEY set as an \
    environment variable:
        ```
        from chartgpt import Chart
        chart = Chart(df)
        chart.plot("your prompt")
        ```

    2. To generate a chart from a DataFrame and an API key provided as an argument:
        ```
        from chartgpt import Chart
        chart = Chart(df, api_key="my_api_key")
        chart.plot("your prompt")
        ```

    Args:
        df (pd.DataFrame): A DataFrame.
        api_key (str, optional): An OpenAI API key. Defaults to None.

    Additional keywords arguments:
        - max_tokens (int, optional): Maximum number of tokens to use. Defaults to 1000.
        - temperature (float, optional): Temperature. Defaults to 0.2.
        - top_p (float, optional): Top p. Defaults to 1.
        - frequency_penalty (float, optional): Frequency penalty. Defaults to 0.
        - presence_penalty (float, optional): Presence penalty. Defaults to 0.
        - chat (bool, optional): Whether to use the chat model or not. Defaults to True.

    Returns:
        Chart: A ChartGPT object.
    """

    def __init__(self, df=None, api_key=None, **kwargs):
        self.chartgpt_instance = ChartGPT(api_key=api_key, **kwargs)
        if df is not None:
            self.chartgpt_instance.load(df=df)

    def plot(self, prompt, **kwargs):
        return self.chartgpt_instance.plot(prompt=prompt, **kwargs)

    @property
    def last_run_code(self):
        return self.chartgpt_instance.last_run_code
