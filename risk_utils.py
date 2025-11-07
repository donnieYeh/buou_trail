# -*- coding: utf-8 -*-
import time
from typing import Any, Dict, List, Optional, Tuple, Union


class StopLossEvaluator:
    ATR_TIMEFRAME = "15m"
    ATR_MULTIPLIER = 2.0
    ATR_CACHE_TTL = 60  # seconds

    def __init__(self, exchange, logger, stop_loss_setting: Union[str, float, int]):
        self.exchange = exchange
        self.logger = logger
        self.rule = self._parse_setting(stop_loss_setting)
        self._cache: Dict[str, Dict[str, Any]] = {}

    def should_stop(
        self,
        symbol: str,
        entry_price: float,
        current_price: float,
        side: str,
        profit_pct: float,
    ) -> Tuple[bool, Optional[Dict[str, Any]]]:
        """
        Evaluate whether the current position should trigger a stop loss.
        Returns a tuple (triggered, context).
        """
        context = self.evaluate_stop(symbol, entry_price, current_price, side, profit_pct)
        if not context:
            return False, None
        return context["triggered"], context

    def evaluate_stop(
        self,
        symbol: str,
        entry_price: float,
        current_price: float,
        side: str,
        profit_pct: float,
    ) -> Optional[Dict[str, Any]]:
        if self.rule["mode"] == "percent":
            threshold = self.rule["value"]
            triggered = profit_pct <= -threshold
            distance_pct = profit_pct + threshold
            return {
                "mode": "percent",
                "threshold": threshold,
                "distance_pct": distance_pct,
                "triggered": triggered,
            }

        metrics = self._get_atr_metrics(symbol)
        if not metrics:
            return None

        distance = metrics["distance"]
        stop_price = entry_price - distance if side == "long" else entry_price + distance
        price_gap = (
            current_price - stop_price if side == "long" else stop_price - current_price
        )
        triggered = price_gap <= 0

        return {
            "mode": "atr",
            "period": self.rule["period"],
            "multiplier": self.rule["multiplier"],
            "timeframe": self.rule["timeframe"],
            "stop_price": stop_price,
            "atr": metrics["atr"],
            "distance": distance,
            "distance_to_stop": price_gap,
            "triggered": triggered,
        }

    def _parse_setting(self, value: Union[str, float, int]) -> Dict[str, Any]:
        if isinstance(value, (int, float)):
            return {"mode": "percent", "value": float(value)}

        if isinstance(value, str):
            stripped = value.strip()
            # Allow numeric strings to behave like raw numbers
            try:
                numeric_value = float(stripped)
                return {"mode": "percent", "value": numeric_value}
            except ValueError:
                normalized = stripped.replace(" ", "").upper()
                if normalized.endswith("ATR"):
                    period_part = normalized[:-3]
                    if not period_part.isdigit():
                        raise ValueError(f"无法解析ATR止损周期: {value}")
                    period = int(period_part)
                    if period <= 0:
                        raise ValueError("ATR止损周期必须大于0")
                    return {
                        "mode": "atr",
                        "period": period,
                        "multiplier": self.ATR_MULTIPLIER,
                        "timeframe": self.ATR_TIMEFRAME,
                        "cache_ttl": self.ATR_CACHE_TTL,
                    }
        raise ValueError(f"不支持的止损配置: {value}")

    def _candidate_symbols(self, symbol: str) -> List[str]:
        candidates = [symbol]
        if ":" in symbol:
            candidates.append(symbol.split(":")[0])
        return list(dict.fromkeys(filter(None, candidates)))

    def refresh_atr(self, symbols: List[str]) -> None:
        """Force refresh ATR cache for the provided symbols."""
        unique_symbols = list(dict.fromkeys(symbols))
        for symbol in unique_symbols:
            self._cache.pop(symbol, None)
            refreshed = self._get_atr_metrics(symbol, force=True)
            if refreshed:
                self.logger.info(
                    f"{symbol} ATR已刷新: {refreshed['atr']:.6f} ({self.rule['period']} @ {self.rule.get('timeframe')})"
                )

    def _get_atr_metrics(self, symbol: str, force: bool = False) -> Optional[Dict[str, Any]]:
        now = time.time()
        cached = self._cache.get(symbol)
        cache_ttl = self.rule.get("cache_ttl", self.ATR_CACHE_TTL)

        if not force and cached and now - cached["ts"] < cache_ttl:
            if cached.get("error"):
                return None
            return cached

        limit = max(self.rule["period"] * 2, self.rule["period"] + 2)
        ohlcv = None
        last_error: Optional[Exception] = None

        for candidate in self._candidate_symbols(symbol):
            try:
                ohlcv = self.exchange.fetch_ohlcv(
                    candidate, timeframe=self.rule["timeframe"], limit=limit
                )
                if ohlcv:
                    break
            except Exception as exc:
                last_error = exc

        if not ohlcv:
            if last_error:
                self.logger.error(f"{symbol} ATR数据获取失败: {last_error}")
            else:
                self.logger.warning(f"{symbol} 未获取到足够K线用于ATR计算")
            self._cache[symbol] = {"ts": now, "error": True}
            return None

        atr = self._calculate_atr(ohlcv, self.rule["period"])
        if atr is None:
            self.logger.warning(f"{symbol} ATR计算数据不足，至少需要 {self.rule['period']} 根K线")
            self._cache[symbol] = {"ts": now, "error": True}
            return None

        metrics = {
            "atr": atr,
            "distance": atr * self.rule["multiplier"],
            "ts": now,
        }
        self._cache[symbol] = metrics
        return metrics

    @staticmethod
    def _calculate_atr(ohlcv: List[List[Any]], period: int) -> Optional[float]:
        if len(ohlcv) < period + 1:
            return None

        true_ranges = []
        prev_close = None

        for candle in ohlcv:
            high = float(candle[2])
            low = float(candle[3])
            close = float(candle[4])

            if prev_close is None:
                tr = high - low
            else:
                tr = max(high - low, abs(high - prev_close), abs(low - prev_close))

            true_ranges.append(tr)
            prev_close = close

        if len(true_ranges) < period:
            return None

        recent_tr = true_ranges[-period:]
        return sum(recent_tr) / period
