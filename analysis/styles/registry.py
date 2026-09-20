"""Canonical analysis-style definitions and registry.

Styles are configuration-level groupings of existing analysis capabilities.
They are not profitability claims or rankings.
"""

from dataclasses import dataclass
from typing import Dict, Tuple


@dataclass(frozen=True)
class AnalysisStyle:
    style_id: str
    title_fa: str
    title_en: str
    description_fa: str
    description_en: str
    component_ids: Tuple[str, ...]
    category: str


_STYLE_DEFINITIONS = (
    AnalysisStyle("scalping", "اسکلپ", "Scalping", "تمرکز کوتاه‌مدت روی حرکات سریع بازار.", "Short-horizon analysis focused on fast market moves.", ("momentum", "price_action", "multi_timeframe"), "preset"),
    AnalysisStyle("swing", "سوئینگ", "Swing Trading", "تمرکز روی حرکات میان‌مدت و ساختار بازار.", "Medium-horizon analysis focused on market structure.", ("market_structure", "trend", "multi_timeframe"), "preset"),
    AnalysisStyle("day_trading", "دی‌تریدینگ", "Day Trading", "تحلیل درون‌روزی با ترکیب روند و مومنتوم.", "Intraday analysis combining trend and momentum.", ("trend", "momentum", "price_action"), "preset"),
    AnalysisStyle("trend_following", "دنبال‌کننده روند", "Trend Following", "تمرکز بر تشخیص و دنبال‌کردن روند.", "Analysis centered on identifying and following trends.", ("trend", "multi_timeframe", "market_structure"), "preset"),
    AnalysisStyle("price_action", "پرایس اکشن", "Price Action", "تمرکز بر رفتار قیمت و ساختار کندلی.", "Price-behavior and candle-structure analysis.", ("price_action", "market_structure"), "technical"),
    AnalysisStyle("breakout", "بریک‌اوت", "Breakout", "تمرکز بر شکست سطوح و تأیید حرکت.", "Breakout and move-confirmation analysis.", ("price_action", "momentum", "support_resistance"), "technical"),
    AnalysisStyle("mean_reversion", "بازگشت به میانگین", "Mean Reversion", "تمرکز بر بازگشت قیمت به ناحیه تعادل.", "Analysis focused on moves back toward equilibrium.", ("momentum", "support_resistance"), "technical"),
    AnalysisStyle("momentum", "مومنتوم", "Momentum", "تمرکز بر قدرت و شتاب حرکت قیمت.", "Analysis focused on price strength and acceleration.", ("momentum", "trend"), "technical"),
    AnalysisStyle("multi_timeframe", "چندتایم‌فریمی", "Multi-Timeframe", "ترکیب دید چند تایم‌فریم برای ساختار و جهت.", "Combines multiple timeframes for structure and direction.", ("multi_timeframe", "market_structure"), "technical"),
    AnalysisStyle("wyckoff", "وایکوف", "Wyckoff", "تحلیل فازهای عرضه، تقاضا و ساختار بازار.", "Supply, demand, and market-phase analysis.", ("wyckoff", "market_structure"), "methodology"),
    AnalysisStyle("smart_money", "اسمارت مانی", "Smart Money", "تمرکز بر ساختار، نقدینگی و نواحی مهم بازار.", "Structure, liquidity, and key market-zone analysis.", ("smc", "market_structure"), "methodology"),
    AnalysisStyle("elliott", "الیوت", "Elliott Wave", "تحلیل ساختار موجی قیمت.", "Wave-structure analysis.", ("elliott", "market_structure"), "methodology"),
    AnalysisStyle("harmonic", "هارمونیک", "Harmonic", "تحلیل الگوهای هارمونیک قیمت.", "Harmonic price-pattern analysis.", ("harmonic", "price_action"), "methodology"),
    AnalysisStyle("support_resistance", "حمایت و مقاومت", "Support & Resistance", "تمرکز بر سطوح کلیدی قیمت.", "Key price-level analysis.", ("support_resistance", "price_action"), "technical"),
)

_STYLE_REGISTRY: Dict[str, AnalysisStyle] = {item.style_id: item for item in _STYLE_DEFINITIONS}


def list_analysis_styles() -> Tuple[AnalysisStyle, ...]:
    return tuple(_STYLE_DEFINITIONS)


def get_analysis_style(style_id: str) -> AnalysisStyle:
    try:
        return _STYLE_REGISTRY[style_id]
    except KeyError as exc:
        raise ValueError(f"Unknown analysis style: {style_id}") from exc


def list_preset_styles() -> Tuple[AnalysisStyle, ...]:
    return tuple(item for item in _STYLE_DEFINITIONS if item.category == "preset")
