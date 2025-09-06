class Instrument {
  final String instrumentId;
  final String symbol;
  final String name;
  final InstrumentType type;
  final double currentPrice;
  final double? priceChange24h;
  final double? volume24h;
  final double? marketCap;
  final bool isActive;
  final DateTime lastUpdated;
  final String? tvSymbol; // TradingView symbol (e.g., "BINANCE:BTCUSDT")

  Instrument({
    required this.instrumentId,
    required this.symbol,
    required this.name,
    required this.type,
    required this.currentPrice,
    this.priceChange24h,
    this.volume24h,
    this.marketCap,
    required this.isActive,
    required this.lastUpdated,
    this.tvSymbol,
  });

  factory Instrument.fromJson(Map<String, dynamic> json) {
    return Instrument(
      instrumentId: json['instrument_id'],
      symbol: json['symbol'],
      name: json['name'],
      type: InstrumentType.values.firstWhere(
        (e) => e.value == json['type'],
        orElse: () => InstrumentType.CRYPTO,
      ),
      currentPrice: (json['current_price'] as num).toDouble(),
      priceChange24h: json['price_change_24h'] != null 
          ? (json['price_change_24h'] as num).toDouble() 
          : null,
      volume24h: json['volume_24h'] != null 
          ? (json['volume_24h'] as num).toDouble() 
          : null,
      marketCap: json['market_cap'] != null 
          ? (json['market_cap'] as num).toDouble() 
          : null,
      isActive: json['is_active'] ?? true,
      lastUpdated: DateTime.parse(json['last_updated']),
      tvSymbol: json['tv_symbol'],
    );
  }

  factory Instrument.fromMarketData(Map<String, dynamic> json) {
    return Instrument(
      instrumentId: json['symbol'] ?? json['instrument_id'] ?? '',
      symbol: json['symbol'] ?? '',
      name: json['name'] ?? '',
      type: InstrumentType.values.firstWhere(
        (e) => e.value == json['type'],
        orElse: () => InstrumentType.CRYPTO,
      ),
      currentPrice: (json['current_price'] as num?)?.toDouble() ?? 0.0,
      priceChange24h: json['price_change_24h'] != null 
          ? (json['price_change_24h'] as num).toDouble() 
          : null,
      volume24h: json['volume'] != null 
          ? (json['volume'] as num).toDouble() 
          : null,
      marketCap: json['market_cap'] != null 
          ? (json['market_cap'] as num).toDouble() 
          : null,
      isActive: true,
      lastUpdated: json['last_updated'] != null 
          ? DateTime.parse(json['last_updated'])
          : DateTime.now(),
      tvSymbol: json['tv_symbol'],
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'instrument_id': instrumentId,
      'symbol': symbol,
      'name': name,
      'type': type.value,
      'current_price': currentPrice,
      'price_change_24h': priceChange24h,
      'volume_24h': volume24h,
      'market_cap': marketCap,
      'is_active': isActive,
      'last_updated': lastUpdated.toIso8601String(),
      'tv_symbol': tvSymbol,
    };
  }

  @override
  String toString() {
    return 'Instrument(symbol: $symbol, name: $name, type: $type, price: \$${currentPrice.toStringAsFixed(2)})';
  }
}

enum InstrumentType {
  CRYPTO('crypto'),
  STOCK('stock');

  const InstrumentType(this.value);
  final String value;
}
