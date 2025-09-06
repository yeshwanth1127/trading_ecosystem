enum PlanType { copy_trade, algo }
enum PlanStatus { active, archived }

class SubscriptionPlan {
  final String planId;
  final String name;
  final PlanType type;
  final double price;
  final Map<String, dynamic>? features;
  final PlanStatus status;

  SubscriptionPlan({
    required this.planId,
    required this.name,
    required this.type,
    required this.price,
    this.features,
    required this.status,
  });

  factory SubscriptionPlan.fromJson(Map<String, dynamic> json) {
    return SubscriptionPlan(
      planId: json['plan_id'] ?? '',
      name: json['name'] ?? '',
      type: PlanType.values.firstWhere(
        (e) => e.name == json['type'],
        orElse: () => PlanType.copy_trade,
      ),
      price: (json['price'] ?? 0.0).toDouble(),
      features: json['features'],
      status: PlanStatus.values.firstWhere(
        (e) => e.name == json['status'],
        orElse: () => PlanStatus.active,
      ),
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'plan_id': planId,
      'name': name,
      'type': type.name,
      'price': price,
      'features': features,
      'status': status.name,
    };
  }

  SubscriptionPlan copyWith({
    String? planId,
    String? name,
    PlanType? type,
    double? price,
    Map<String, dynamic>? features,
    PlanStatus? status,
  }) {
    return SubscriptionPlan(
      planId: planId ?? this.planId,
      name: name ?? this.name,
      type: type ?? this.type,
      price: price ?? this.price,
      features: features ?? this.features,
      status: status ?? this.status,
    );
  }

  bool get isActive => status == PlanStatus.active;
  bool get isCopyTrade => type == PlanType.copy_trade;
  bool get isAlgo => type == PlanType.algo;

  String get formattedPrice => '\$${price.toStringAsFixed(2)}';
  String get typeDisplayName => type.name.replaceAll('_', ' ').toUpperCase();

  @override
  String toString() {
    return 'SubscriptionPlan(planId: $planId, name: $name, type: $type, price: $formattedPrice)';
  }

  @override
  bool operator ==(Object other) {
    if (identical(this, other)) return true;
    return other is SubscriptionPlan && other.planId == planId;
  }

  @override
  int get hashCode => planId.hashCode;
}
