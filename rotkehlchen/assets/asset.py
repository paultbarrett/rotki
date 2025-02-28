from dataclasses import InitVar, dataclass, field
from functools import total_ordering
from typing import TYPE_CHECKING, Any, Optional, Type, TypeVar

from rotkehlchen.constants.resolver import (
    ETHEREUM_DIRECTIVE,
    ETHEREUM_DIRECTIVE_LENGTH,
    strethaddress_to_identifier,
)
from rotkehlchen.errors import DeserializationError, UnsupportedAsset
from rotkehlchen.typing import ChecksumEthAddress, Timestamp

from .typing import AssetType

if TYPE_CHECKING:
    from rotkehlchen.chain.ethereum.typing import CustomEthereumTokenWithIdentifier

WORLD_TO_BITTREX = {
    # In Rotkehlchen Bitswift is BITS-2 but in Bittrex it's BITS
    'BITS-2': 'BITS',
    # In Rotkehlchen NuBits is USNBT but in Bittrex it's NBT
    'USNBT': 'NBT',
    # In Rotkehlchen BTM-2 is Bytom but in Bittrex it's BTM
    'BTM-2': 'BTM',
    # Bittrex PI shoould map to rotki's PCHAIN
    strethaddress_to_identifier('0xB9bb08AB7E9Fa0A1356bd4A39eC0ca267E03b0b3'): 'PI',
    # Bittrex PLA should map to rotki's PlayChip
    strethaddress_to_identifier('0x0198f46f520F33cd4329bd4bE380a25a90536CD5'): 'PLA',
    # In Rotkehlchen LUNA-2 is Terra Luna but in Bittrex it's LUNA
    'LUNA-2': 'LUNA',
    # WASP in binance maps to WorldWideAssetExchange in rotki
    # In Rotkehlchen WorldWideAssetExchange is WAX but in Bittrex it's WASP
    strethaddress_to_identifier('0x39Bb259F66E1C59d5ABEF88375979b4D20D98022'): 'WAXP',
    # In Rotkehlchen Validity is RADS, the old name but in Bittrex it's VAL
    'RADS': 'VAL',
    # make sure bittrex matches ADX latest contract
    strethaddress_to_identifier('0xADE00C28244d5CE17D72E40330B1c318cD12B7c3'): 'ADX',
    # Bittrex AID maps to Aidcoin
    strethaddress_to_identifier('0x37E8789bB9996CaC9156cD5F5Fd32599E6b91289'): 'AID',
    # make sure bittrex matches ANT latest contract
    strethaddress_to_identifier('0xa117000000f279D81A1D3cc75430fAA017FA5A2e'): 'ANT',
    # Bittrex CMCT maps to Crowdmachine
    strethaddress_to_identifier('0x47bc01597798DCD7506DCCA36ac4302fc93a8cFb'): 'CMCT',
    # Bittrex REV maps to REV (and not R)
    strethaddress_to_identifier('0x2ef52Ed7De8c5ce03a4eF0efbe9B7450F2D7Edc9'): 'REV',
    # make sure bittrex matches latest VRA contract
    strethaddress_to_identifier('0xF411903cbC70a74d22900a5DE66A2dda66507255'): 'VRA',
    # FET is Fetch AI in bittrex
    strethaddress_to_identifier('0x1D287CC25dAD7cCaF76a26bc660c5F7C8E2a05BD'): 'FET',
    # make sure GNY maps to the appropriate token for bittrex
    strethaddress_to_identifier('0xb1f871Ae9462F1b2C6826E88A7827e76f86751d4'): 'GNY',
    # MTC is Metacoin in Bittrex
    'MTC-3': 'MTC',
}

WORLD_TO_FTX = {
    strethaddress_to_identifier('0x50D1c9771902476076eCFc8B2A83Ad6b9355a4c9'): 'FTT',
}

WORLD_TO_POLONIEX = {
    # AIR-2 is aircoin for us and AIR is airtoken. Poloniex has only aircoin
    'AIR-2': 'AIR',
    # DEC in poloniex matches Decentr
    strethaddress_to_identifier('0x30f271C9E86D2B7d00a6376Cd96A1cFBD5F0b9b3'): 'DEC',
    # Poloniex delisted BCH and listed it as BCHABC after the Bitcoin Cash
    # ABC / SV fork. In Rotkehlchen we consider BCH to be the same as BCHABC
    'BCH': 'BCHABC',
    # Poloniex has the BCH Fork, Bitcoin Satoshi's vision listed as BCHSV.
    # We know it as BSV
    'BSV': 'BCHSV',
    # Caishen is known as CAI in Poloniex. This is before the swap to CAIX
    'CAIX': 'CAI',
    # CCN is Cannacoin in Poloniex but in Rotkehlchen we know it as CCN-2
    'CCN-2': 'CCN',
    # CCN is CustomContractNetwork in Rotkehlchen but does not exist in Cryptocompare
    # Putting it as conversion to make sure we don't accidentally ask for wrong price
    'CCN': '',
    'cUSDT': 'CUSDT',
    # Faircoin is known as FAIR outside of Poloniex. Seems to be the same as the
    # now delisted Poloniex's FAC if you look at the bitcointalk announcement
    # https://bitcointalk.org/index.php?topic=702675.0
    'FAIR': 'FAC',
    # KeyCoin in Poloniex is KEY but in Rotkehlchen it's KEY-3
    'KEY-3': 'KEY',
    # Mazacoin in Poloniex is MZC but in Rotkehlchen it's MAZA
    'MAZA': 'MZC',
    # Myriadcoin in Poloniex is MYR but in Rotkehlchen it's XMY
    'XMY': 'MYR',
    # NuBits in Poloniex is NBT but in Rotkehlchen it's USNBT
    'USNBT': 'NBT',
    # Stellar is XLM everywhere, apart from Poloniex
    'XLM': 'STR',
    # Poloniex still has the old name WC for WhiteCoin
    'XWC': 'WC',
    # Poloniex uses a different name for 1inch. Maybe due to starting with number?
    '1INCH': 'ONEINCH',
    # FTT is FTX token in poloniex
    strethaddress_to_identifier('0x50D1c9771902476076eCFc8B2A83Ad6b9355a4c9'): 'FTT',
    # TRB is Tellor Tributes in poloniex
    strethaddress_to_identifier('0x88dF592F8eb5D7Bd38bFeF7dEb0fBc02cf3778a0'): 'TRB',
    # WINK is WIN in poloniex
    'WIN-3': 'WIN',
}

WORLD_TO_KRAKEN = {
    'ATOM': 'ATOM',
    'ALGO': 'ALGO',
    'AUD': 'ZAUD',
    'BAT': 'BAT',
    'COMP': 'COMP',
    'DOT': 'DOT',
    'KAVA': 'KAVA',
    'KNC': 'KNC',
    'LINK': 'LINK',
    'BSV': 'BSV',
    'ETC': 'XETC',
    'ETH': 'XETH',
    'LTC': 'XLTC',
    # REP V1
    strethaddress_to_identifier('0x1985365e9f78359a9B6AD760e32412f4a445E862'): 'XREP',
    'BTC': 'XXBT',
    'XMR': 'XXMR',
    'XRP': 'XXRP',
    'ZEC': 'XZEC',
    'EUR': 'ZEUR',
    'USD': 'ZUSD',
    'GBP': 'ZGBP',
    'CAD': 'ZCAD',
    'JPY': 'ZJPY',
    'CHF': 'CHF',
    'KRW': 'ZKRW',
    # REP V2
    strethaddress_to_identifier('0x221657776846890989a759BA2973e427DfF5C9bB'): 'REPV2',
    'DAO': 'XDAO',
    'MLN': 'XMLN',
    'ICN': 'XICN',
    'GNO': 'GNO',
    'BCH': 'BCH',
    'XLM': 'XXLM',
    'DASH': 'DASH',
    'EOS': 'EOS',
    'USDC': 'USDC',
    'USDT': 'USDT',
    'KFEE': 'KFEE',
    'ADA': 'ADA',
    'QTUM': 'QTUM',
    'NMC': 'XNMC',
    'VEN': 'XXVN',
    'DOGE': 'XXDG',
    'DAI': 'DAI',
    'XTZ': 'XTZ',
    'WAVES': 'WAVES',
    'ICX': 'ICX',
    'NANO': 'NANO',
    'OMG': 'OMG',
    'SC': 'SC',
    'PAXG': 'PAXG',
    'LSK': 'LSK',
    'TRX': 'TRX',
    'OXT': 'OXT',
    'STORJ': 'STORJ',
    'BAL': 'BAL',
    'KSM': 'KSM',
    'CRV': 'CRV',
    'SNX': 'SNX',
    'FIL': 'FIL',
    'UNI': 'UNI',
    'YFI': 'YFI',
    # Make sure kraken maps to latest ANT
    strethaddress_to_identifier('0xa117000000f279D81A1D3cc75430fAA017FA5A2e'): 'ANT',
    'KEEP': 'KEEP',
    'TBTC': 'TBTC',
    'ETH2': 'ETH2',
    'AAVE': 'AAVE',
    'MANA': 'MANA',
    'GRT': 'GRT',
    'FLOW': 'FLOW',
    'OCEAN': 'OCEAN',
    'EWT': 'EWT',
}

WORLD_TO_BINANCE = {
    # When BCH forked to BCHABC and BCHSV, binance renamed the original to ABC
    'BCH': 'BCHABC',
    'BSV': 'BCHSV',
    # ETHOS is known as BQX in Binance
    strethaddress_to_identifier('0x5Af2Be193a6ABCa9c8817001F45744777Db30756'): 'BQX',
    # GXChain is GXS in Binance but GXC in Rotkehlchen
    'GXC': 'GXS',
    # Luna Terra is LUNA-2 in rotki
    'LUNA-2': 'LUNA',
    # YOYOW is known as YOYO in Binance
    strethaddress_to_identifier('0xcbeAEc699431857FDB4d37aDDBBdc20E132D4903'): 'YOYO',
    # Solana is SOL-2 in rotki
    'SOL-2': 'SOL',
    # BETH is the eth staked in beacon chain
    'ETH2': 'BETH',
    # STX is Blockstack in Binance
    'STX-2': 'STX',
    # ONE is Harmony in Binance
    'ONE-2': 'ONE',
    # FTT is FTX in Binance
    strethaddress_to_identifier('0x50D1c9771902476076eCFc8B2A83Ad6b9355a4c9'): 'FTT',
    # make sure binance matches ADX latest contract
    strethaddress_to_identifier('0xADE00C28244d5CE17D72E40330B1c318cD12B7c3'): 'ADX',
    # make sure binance matces ANT latest contract
    strethaddress_to_identifier('0xa117000000f279D81A1D3cc75430fAA017FA5A2e'): 'ANT',
    # HOT is Holo in Binance
    strethaddress_to_identifier('0x6c6EE5e31d828De241282B9606C8e98Ea48526E2'): 'HOT',
    # Key is SelfKey in Binance
    strethaddress_to_identifier('0x4CC19356f2D37338b9802aa8E8fc58B0373296E7'): 'KEY',
    # PNT is pNetwork in Binance
    strethaddress_to_identifier('0x89Ab32156e46F46D02ade3FEcbe5Fc4243B9AAeD'): 'PNT',
    # FET is Fetch AI in Binance
    strethaddress_to_identifier('0x1D287CC25dAD7cCaF76a26bc660c5F7C8E2a05BD'): 'FET',
    # TRB is Tellor Tributes in Binance
    strethaddress_to_identifier('0x88dF592F8eb5D7Bd38bFeF7dEb0fBc02cf3778a0'): 'TRB',
    # WIN is WINk in Binance
    'WIN-3': 'WIN',
}

WORLD_TO_BITFINEX = {
    'BCH': 'BCHABC',
    'CNY': 'CNH',
    'DOGE': 'DOG',
    'LUNA-2': 'LUNA',
    # make sure GNY maps to the appropriate token for bitfinex
    strethaddress_to_identifier('0xb1f871Ae9462F1b2C6826E88A7827e76f86751d4'): 'GNY',
    # make sure REP maps to latest one in bitfinex
    strethaddress_to_identifier('0x221657776846890989a759BA2973e427DfF5C9bB'): 'REP',
    # TRIO is TRI in bitfinex
    strethaddress_to_identifier('0x8B40761142B9aa6dc8964e61D0585995425C3D94'): 'TRI',
    # ZB token is ZBT in bitfinex
    strethaddress_to_identifier('0xBd0793332e9fB844A52a205A233EF27a5b34B927'): 'ZBT',
    # GOT is parkingo in bitfinex
    strethaddress_to_identifier('0x613Fa2A6e6DAA70c659060E86bA1443D2679c9D7'): 'GOT',
    # make sure ANT maps to latest one in bitfinex
    strethaddress_to_identifier('0xa117000000f279D81A1D3cc75430fAA017FA5A2e'): 'ANT',
    # PNT is pNetwork in bitfinex. Also original symbol is EDO there.
    strethaddress_to_identifier('0x89Ab32156e46F46D02ade3FEcbe5Fc4243B9AAeD'): 'EDO',
    # ORS is orsgroup in bitfinex
    strethaddress_to_identifier('0xac2e58A06E6265F1Cf5084EE58da68e5d75b49CA'): 'ORS',
    # FTT is ftx in bitfinex
    strethaddress_to_identifier('0x50D1c9771902476076eCFc8B2A83Ad6b9355a4c9'): 'FTT',
    # FET is Fetch AI in bitfinex
    strethaddress_to_identifier('0x1D287CC25dAD7cCaF76a26bc660c5F7C8E2a05BD'): 'FET',
}

WORLD_TO_KUCOIN = {
    'BSV': 'BCHSV',
    'LUNA-2': 'LUNA',
    # make sure Veracity maps to latest one in kucoin
    strethaddress_to_identifier('0xF411903cbC70a74d22900a5DE66A2dda66507255'): 'VRA',
    # KEY is selfkey in kucoin
    strethaddress_to_identifier('0x4CC19356f2D37338b9802aa8E8fc58B0373296E7'): 'KEY',
    # MTC is doc.com in kucoin
    strethaddress_to_identifier('0x905E337c6c8645263D3521205Aa37bf4d034e745'): 'MTC',
    # R is revain in kucoin
    strethaddress_to_identifier('0x2ef52Ed7De8c5ce03a4eF0efbe9B7450F2D7Edc9'): 'R',
    # FET is Fetch AI in Kucoin
    strethaddress_to_identifier('0x1D287CC25dAD7cCaF76a26bc660c5F7C8E2a05BD'): 'FET',
    # WINK is WINk in KUCOIN
    'WIN-3': 'WINK',
}

WORLD_TO_ICONOMI = {
    # In Rotkehlchen LUNA-2 is Terra Luna but in Iconomi it's LUNA
    'LUNA-2': 'LUNA',
    # make sure iconomi matches ADX latest contract
    strethaddress_to_identifier('0xADE00C28244d5CE17D72E40330B1c318cD12B7c3'): 'ADX',
    # make sure iconomi matces ANT latest contract
    strethaddress_to_identifier('0xa117000000f279D81A1D3cc75430fAA017FA5A2e'): 'ANT',
    # make sure iconomi matces REP latest contract
    strethaddress_to_identifier('0x221657776846890989a759BA2973e427DfF5C9bB'): 'REP',
    # FTT is ftx in iconomi
    strethaddress_to_identifier('0x50D1c9771902476076eCFc8B2A83Ad6b9355a4c9'): 'FTT',
    # HOT is Holo chain token in iconomi
    strethaddress_to_identifier('0x6c6EE5e31d828De241282B9606C8e98Ea48526E2'): 'HOT',
    # PNT is pNetwork in iconomi
    strethaddress_to_identifier('0x89Ab32156e46F46D02ade3FEcbe5Fc4243B9AAeD'): 'PNT',
    # FET is Fetch AI in iconomi
    strethaddress_to_identifier('0x1D287CC25dAD7cCaF76a26bc660c5F7C8E2a05BD'): 'FET',
    # TRB is Tellor Tributes in iconomi
    strethaddress_to_identifier('0x88dF592F8eb5D7Bd38bFeF7dEb0fBc02cf3778a0'): 'TRB',
}


@total_ordering
@dataclass(init=True, repr=True, eq=False, order=False, unsafe_hash=False, frozen=True)
class Asset():
    identifier: str
    form_with_incomplete_data: InitVar[bool] = field(default=False)
    name: str = field(init=False)
    symbol: str = field(init=False)
    asset_type: AssetType = field(init=False)
    started: Timestamp = field(init=False)
    forked: Optional[str] = field(init=False)
    swapped_for: Optional[str] = field(init=False)
    # None means no special mapping. '' means not supported
    cryptocompare: Optional[str] = field(init=False)
    coingecko: Optional[str] = field(init=False)

    def __post_init__(self, form_with_incomplete_data: bool = False) -> None:
        """
        Asset post initialization

        The only thing that is given to initialize an asset is a string.

        If a non string is given then it's probably a deserialization error or
        invalid data were given to us by the server if an API was queried.

        If `form_with_incomplete_data` is given and is True then we allow the generation
        of an asset object even if the corresponding underlying object is missing
        important data such as name, symbol, token decimals etc. In most case this
        is not wanted except for some exception like passing in some functions for
        icon generation.

        May raise UnknownAsset if the asset identifier can't be matched to anything
        """
        if not isinstance(self.identifier, str):
            raise DeserializationError(
                'Tried to initialize an asset out of a non-string identifier',
            )

        # TODO: figure out a way to move this out. Moved in here due to cyclic imports
        from rotkehlchen.assets.resolver import AssetResolver  # isort:skip  # noqa: E501  # pylint: disable=import-outside-toplevel
        data = AssetResolver().get_asset_data(self.identifier, form_with_incomplete_data)
        # make sure same case of identifier as in  DB is saved in the structure
        object.__setattr__(self, 'identifier', data.identifier)
        # Ugly hack to set attributes of a frozen data class as post init
        # https://docs.python.org/3/library/dataclasses.html#frozen-instances
        object.__setattr__(self, 'name', data.name)
        object.__setattr__(self, 'symbol', data.symbol)
        object.__setattr__(self, 'asset_type', data.asset_type)
        object.__setattr__(self, 'started', data.started)
        object.__setattr__(self, 'forked', data.forked)
        object.__setattr__(self, 'swapped_for', data.swapped_for)
        object.__setattr__(self, 'cryptocompare', data.cryptocompare)
        object.__setattr__(self, 'coingecko', data.coingecko)

    def serialize(self) -> str:
        return self.identifier

    def is_fiat(self) -> bool:
        return self.asset_type == AssetType.FIAT

    def is_eth_token(self) -> bool:
        return self.asset_type == AssetType.ETHEREUM_TOKEN

    def __str__(self) -> str:
        if self.is_eth_token():
            token = EthereumToken.from_asset(self)
            assert token, 'Token should exist here'
            return str(token)
        return f'{self.symbol}({self.name})'

    def __repr__(self) -> str:
        return f'<Asset identifier:{self.identifier} name:{self.name} symbol:{self.symbol}>'

    def to_kraken(self) -> str:
        return WORLD_TO_KRAKEN[self.identifier]

    def to_bitfinex(self) -> str:
        return WORLD_TO_BITFINEX.get(self.identifier, self.identifier)

    def to_bittrex(self) -> str:
        return WORLD_TO_BITTREX.get(self.identifier, self.identifier)

    def to_binance(self) -> str:
        return WORLD_TO_BINANCE.get(self.identifier, self.identifier)

    def to_cryptocompare(self) -> str:
        """Returns the symbol with which to query cryptocompare for the asset

        May raise:
            - UnsupportedAsset() if the asset is not supported by cryptocompare
        """
        cryptocompare_str = self.symbol if self.cryptocompare is None else self.cryptocompare
        # There is an asset which should not be queried in cryptocompare
        if cryptocompare_str is None or cryptocompare_str == '':
            raise UnsupportedAsset(f'{self.identifier} is not supported by cryptocompare')

        # Seems cryptocompare capitalizes everything. So cDAI -> CDAI
        return cryptocompare_str.upper()

    def to_coingecko(self) -> str:
        """Returns the symbol with which to query coingecko for the asset

        May raise:
            - UnsupportedAsset() if the asset is not supported by coingecko
        """
        coingecko_str = '' if self.coingecko is None else self.coingecko
        # This asset has no coingecko mapping
        if coingecko_str == '':
            raise UnsupportedAsset(f'{self.identifier} is not supported by coingecko')
        return coingecko_str

    def has_coingecko(self) -> bool:
        return self.coingecko is not None and self.coingecko != ''

    def __hash__(self) -> int:
        return hash(self.identifier)

    def __eq__(self, other: Any) -> bool:
        if other is None:
            return False

        if isinstance(other, Asset):
            return self.identifier.lower() == other.identifier.lower()
        if isinstance(other, str):
            return self.identifier.lower() == other.lower()
        # else
        raise ValueError(f'Invalid comparison of asset with {type(other)}')

    def __ne__(self, other: Any) -> bool:
        return not self.__eq__(other)

    def __lt__(self, other: Any) -> bool:
        if isinstance(other, Asset):
            return self.identifier < other.identifier
        if isinstance(other, str):
            return self.identifier < other
        # else
        raise ValueError(f'Invalid comparison of asset with {type(other)}')


@dataclass(init=True, repr=True, eq=False, order=False, unsafe_hash=False, frozen=True)
class HasEthereumToken(Asset):
    """ Marker to denote assets having an Ethereum token address """
    ethereum_address: ChecksumEthAddress = field(init=False)
    decimals: int = field(init=False)
    protocol: str = field(init=False)

    def __post_init__(self, form_with_incomplete_data: bool = False) -> None:
        object.__setattr__(self, 'identifier', ETHEREUM_DIRECTIVE + self.identifier)
        super().__post_init__(form_with_incomplete_data)
        # TODO: figure out a way to move this out. Moved in here due to cyclic imports
        from rotkehlchen.assets.resolver import AssetResolver  # isort:skip  # noqa: E501  # pylint: disable=import-outside-toplevel

        data = AssetResolver().get_asset_data(self.identifier)  # pylint: disable=no-member

        if not data.ethereum_address:
            raise DeserializationError(
                'Tried to initialize a non Ethereum asset as Ethereum Token',
            )

        object.__setattr__(self, 'ethereum_address', data.ethereum_address)
        object.__setattr__(self, 'decimals', data.decimals)
        object.__setattr__(self, 'protocol', data.protocol)


# Create a generic variable that can be 'EthereumToken', or any subclass.
T = TypeVar('T', bound='EthereumToken')


@dataclass(init=True, repr=True, eq=False, order=False, unsafe_hash=False, frozen=True)
class EthereumToken(HasEthereumToken):

    def __str__(self) -> str:
        return f'{self.symbol}({self.ethereum_address})'

    @classmethod
    def from_asset(cls: Type[T], asset: Asset) -> Optional[T]:
        """Attempts to turn an asset into an EthereumToken. If it fails returns None"""
        return cls.from_identifier(asset.identifier)

    @classmethod
    def from_identifier(cls: Type[T], identifier: str) -> Optional[T]:
        """Attempts to turn an asset into an EthereumToken. If it fails returns None"""
        if not identifier.startswith(ETHEREUM_DIRECTIVE):
            return None

        try:
            return cls(identifier[ETHEREUM_DIRECTIVE_LENGTH:])
        except DeserializationError:
            return None

    def to_custom_ethereum_token(self) -> 'CustomEthereumTokenWithIdentifier':
        """TODO:This is just to satisfy its use in one place

        Eventually these two data structures should be consolidated."""
        # TODO: figure out a way to move this out. Moved in here due to cyclic imports
        from rotkehlchen.chain.ethereum.typing import CustomEthereumTokenWithIdentifier  # isort:skip  # noqa: E501  # pylint: disable=import-outside-toplevel
        swapped_for_asset = None if self.swapped_for is None else Asset(self.swapped_for)
        return CustomEthereumTokenWithIdentifier(
            identifier=self.identifier,
            address=self.ethereum_address,
            decimals=self.decimals,
            name=self.name,
            symbol=self.symbol,
            started=self.started,
            swapped_for=swapped_for_asset,
            coingecko=self.coingecko,
            cryptocompare=self.cryptocompare,
            protocol=None,
            underlying_tokens=None,
        )
