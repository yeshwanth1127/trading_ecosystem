class Order {
  final String orderId;
  final String userId;
  final String instrumentId;
  final OrderType orderType;
  final OrderSide side;
  final double quantity;
  final double filledQuantity;
  final double? price;
  final double? stopPrice;
  final double totalAmount;
  final double commission;
  final String? notes;
  final DateTime createdAt;
  final DateTime updatedAt;
  final DateTime? filledAt;
  final DateTime? cancelledAt;

  Order({
    required this.orderId,
    required this.userId,
    required this.instrumentId,
    required this.orderType,
    required this.side,
    required this.quantity,
    required this.filledQuantity,
    this.price,
    this.stopPrice,
    required this.totalAmount,
    required this.commission,
    this.notes,
    required this.createdAt,
    required this.updatedAt,
    this.filledAt,
    this.cancelledAt,
  });

  factory Order.fromJson(Map<String, dynamic> json) {
    return Order(
      orderId: json['order_id'],
      userId: json['user_id'],
      instrumentId: json['instrument_id'],
      orderType: OrderType.values.firstWhere(
        (e) => e.value == json['order_type'],
        orElse: () => OrderType.MARKET,
      ),
      side: OrderSide.values.firstWhere(
        (e) => e.value == json['side'],
        orElse: () => OrderSide.BUY,
      ),
      quantity: (json['quantity'] as num).toDouble(),
      filledQuantity: (json['filled_quantity'] as num).toDouble(),
      price: json['price'] != null ? (json['price'] as num).toDouble() : null,
      stopPrice: json['stop_price'] != null ? (json['stop_price'] as num).toDouble() : null,
      totalAmount: (json['total_amount'] as num).toDouble(),
      commission: (json['commission'] as num).toDouble(),
      notes: json['notes'],
      createdAt: DateTime.parse(json['created_at']),
      updatedAt: DateTime.parse(json['updated_at']),
      filledAt: json['filled_at'] != null ? DateTime.parse(json['filled_at']) : null,
      cancelledAt: json['cancelled_at'] != null ? DateTime.parse(json['cancelled_at']) : null,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'order_id': orderId,
      'user_id': userId,
      'instrument_id': instrumentId,
      'order_type': orderType.value,
      'side': side.value,
      'quantity': quantity,
      'filled_quantity': filledQuantity,
      'price': price,
      'stop_price': stopPrice,
      'total_amount': totalAmount,
      'commission': commission,
      'notes': notes,
      'created_at': createdAt.toIso8601String(),
      'updated_at': updatedAt.toIso8601String(),
      'filled_at': filledAt?.toIso8601String(),
      'cancelled_at': cancelledAt?.toIso8601String(),
    };
  }

  @override
  String toString() {
    return 'Order(${side.value} ${quantity} ${orderType.value})';
  }
}

enum OrderType {
  MARKET('market'),
  LIMIT('limit'),
  STOP('stop'),
  STOP_LIMIT('stop_limit');

  const OrderType(this.value);
  final String value;
}

enum OrderSide {
  BUY('buy'),
  SELL('sell');

  const OrderSide(this.value);
  final String value;
}

// Status removed per requirement.
