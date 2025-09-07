from freqtrade.strategy.interface import IStrategy
from pandas import DataFrame


class SampleStrategy(IStrategy):
    INTERFACE_VERSION = 3
    timeframe = "5m"
    minimal_roi = {"0": 10}
    stoploss = -0.99

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:  # type: ignore[override]
        return dataframe

    def populate_buy_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:  # type: ignore[override]
        dataframe["buy"] = 0
        return dataframe

    def populate_sell_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:  # type: ignore[override]
        dataframe["sell"] = 0
        return dataframe



