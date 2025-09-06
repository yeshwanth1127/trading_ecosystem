class Position {
  final String positionId;
  final String userId;
  final String instrumentId;
  final String? instrumentSymbol; // Add instrument symbol
  final PositionSide side;
  final PositionStatus status;
  final double quantity;
  final double averageEntryPrice;
  final double? currentPrice;
  final double? unrealizedPnl;
  final double? realizedPnl;
  final double? marginUsed;
  final double? leverage;
  final DateTime openedAt;
  final DateTime? closedAt;
  final DateTime lastUpdated;

  Position({
    required this.positionId,
    required this.userId,
    required this.instrumentId,
    this.instrumentSymbol,
    required this.side,
    required this.status,
    required this.quantity,
    required this.averageEntryPrice,
    this.currentPrice,
    this.unrealizedPnl,
    this.realizedPnl,
    this.marginUsed,
    this.leverage,
    required this.openedAt,
    this.closedAt,
    required this.lastUpdated,
  });

  factory Position.fromJson(Map<String, dynamic> json) {
    return Position(
      positionId: json['position_id'],
      userId: json['user_id'],
      instrumentId: json['instrument_id'],
      instrumentSymbol: json['instrument_symbol'],
      side: PositionSide.values.firstWhere(
        (e) => e.value == json['side'],
        orElse: () => PositionSide.LONG,
      ),
      status: PositionStatus.values.firstWhere(
        (e) => e.value == json['status'],
        orElse: () => PositionStatus.OPEN,
      ),
      quantity: (json['quantity'] as num).toDouble(),
      averageEntryPrice: (json['average_entry_price'] as num).toDouble(),
      currentPrice: json['current_price'] != null ? (json['current_price'] as num).toDouble() : null,
      unrealizedPnl: json['unrealized_pnl'] != null ? (json['unrealized_pnl'] as num).toDouble() : null,
      realizedPnl: json['realized_pnl'] != null ? (json['realized_pnl'] as num).toDouble() : null,
      marginUsed: json['margin_used'] != null ? (json['margin_used'] as num).toDouble() : null,
      leverage: json['leverage'] != null ? (json['leverage'] as num).toDouble() : null,
      openedAt: DateTime.parse(json['opened_at']),
      closedAt: json['closed_at'] != null ? DateTime.parse(json['closed_at']) : null,
      lastUpdated: DateTime.parse(json['last_updated']),
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'position_id': positionId,
      'user_id': userId,
      'instrument_id': instrumentId,
      'instrument_symbol': instrumentSymbol,
      'side': side.value,
      'status': status.value,
      'quantity': quantity,
      'average_entry_price': averageEntryPrice,
      'current_price': currentPrice,
      'unrealized_pnl': unrealizedPnl,
      'realized_pnl': realizedPnl,
      'margin_used': marginUsed,
      'leverage': leverage,
      'opened_at': openedAt.toIso8601String(),
      'closed_at': closedAt?.toIso8601String(),
      'last_updated': lastUpdated.toIso8601String(),
    };
  }

  @override
  String toString() {
    return 'Position(${side.value} ${quantity} - ${status.value})';
  }
}

enum PositionSide {
  LONG('long'),
  SHORT('short');

  const PositionSide(this.value);
  final String value;
}

enum PositionStatus {
  OPEN('open'),
  CLOSED('closed');

  const PositionStatus(this.value);
  final String value;
}
