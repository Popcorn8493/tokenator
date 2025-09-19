import hashlib
from dataclasses import dataclass
from typing import Optional, Dict, List, Any
from enum import Enum


class TokenSide(Enum):
    FRONT = "front"
    BACK = "back"


@dataclass
class PriceData:

    tcgplayer_market_price: Optional[float] = None

    def __post_init__(self):
        for field_name in [
                'market_price', 'median_price', 'low_price', 'high_price',
                'tcgplayer', 'cardkingdom', 'cardmarket'
        ]:
            value = getattr(self, field_name)
            if value is not None and (not isinstance(value, (int, float))
                                      or value < 0):
                setattr(self, field_name, None)

    def get_best_price(self) -> tuple[Optional[float], Optional[str]]:
        price_sources = [(self.market_price, "Market"),
                         (self.median_price, "Median"),
                         (self.tcgplayer, "TCGPlayer"),
                         (self.cardkingdom, "Card Kingdom"),
                         (self.cardmarket, "Card Market")]

        best_price = None
        best_source = None

        for price, source in price_sources:
            if price is not None and (best_price is None
                                      or price > best_price):
                best_price = price
                best_source = source

        if self.source and best_price is not None:
            best_source = self.source

        return best_price, best_source


@dataclass
class TokenInfo:
    name: str
    uuid: Optional[str] = None
    set_code: Optional[str] = None
    collector_number: Optional[str] = None
    power: Optional[str] = None
    toughness: Optional[str] = None
    colors: Optional[List[str]] = None
    artist: Optional[str] = None
    image_uri: Optional[str] = None
    rarity: Optional[str] = "Token"


@dataclass
class TokenData:
    front_side: TokenInfo
    back_side: Optional[TokenInfo] = None
    front_price: Optional[PriceData] = None
    front_collector_number: Optional[str] = None
    back_collector_number: Optional[str] = None
    back_price: Optional[PriceData] = None
    double_sided_market_price: Optional[PriceData] = None
    is_double_sided: bool = False

    def get_more_valuable_side(self, analyzer=None) -> Optional[TokenSide]:
        try:
            from .price_strategies import TokenPriceAnalyzer
            price_analyzer = TokenPriceAnalyzer()
            return price_analyzer.get_more_valuable_side(self, analyzer)
        except ImportError:
            if not self.is_double_sided or not self.back_side:
                return TokenSide.FRONT

            front_price, _ = self.front_price.get_best_price(
            ) if self.front_price else (None, None)
            back_price, _ = self.back_price.get_best_price(
            ) if self.back_price else (None, None)

            if front_price is None and back_price is None:
                return None
            elif front_price is None:
                return TokenSide.BACK
            elif back_price is None:
                return TokenSide.FRONT
            else:
                return TokenSide.BACK if back_price > front_price else TokenSide.FRONT

    def double_sided_uuid(self) -> Optional[str]:
        if self.is_double_sided and self.front_side.uuid and self.back_side and self.back_side.uuid:
            uuids = sorted([self.front_side.uuid, self.back_side.uuid])
            combined_uuid_string = "-".join(uuids)
            return hashlib.sha1(combined_uuid_string.encode()).hexdigest()
        return None

    def get_value_difference(self, analyzer=None) -> Optional[float]:
        try:
            from .price_strategies import TokenPriceAnalyzer
            price_analyzer = TokenPriceAnalyzer()
            return price_analyzer.get_value_difference(self, analyzer)
        except ImportError:
            if not self.is_double_sided or not self.back_side:
                return None

            front_price, _ = self.front_price.get_best_price(
            ) if self.front_price else (None, None)
            back_price, _ = self.back_price.get_best_price(
            ) if self.back_price else (None, None)

            if front_price is None or back_price is None:
                return None

            return abs(back_price - front_price)
