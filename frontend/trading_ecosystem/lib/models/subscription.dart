enum SubscriptionStatus { active, expired, cancelled }

class Subscription {
  final String subscriptionId;
  final String userId;
  final String planId;
  final SubscriptionStatus status;
  final DateTime startDate;
  final DateTime endDate;
  final DateTime? cancelledAt;
  final Map<String, dynamic>? metadata;

  Subscription({
    required this.subscriptionId,
    required this.userId,
    required this.planId,
    required this.status,
    required this.startDate,
    required this.endDate,
    this.cancelledAt,
    this.metadata,
  });

  factory Subscription.fromJson(Map<String, dynamic> json) {
    return Subscription(
      subscriptionId: json['subscription_id'] ?? '',
      userId: json['user_id'] ?? '',
      planId: json['plan_id'] ?? '',
      status: SubscriptionStatus.values.firstWhere(
        (e) => e.name == json['status'],
        orElse: () => SubscriptionStatus.active,
      ),
      startDate: DateTime.parse(json['start_date'] ?? DateTime.now().toIso8601String()),
      endDate: DateTime.parse(json['end_date'] ?? DateTime.now().toIso8601String()),
      cancelledAt: json['cancelled_at'] != null 
          ? DateTime.parse(json['cancelled_at']) 
          : null,
      metadata: json['metadata'],
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'subscription_id': subscriptionId,
      'user_id': userId,
      'plan_id': planId,
      'status': status.name,
      'start_date': startDate.toIso8601String(),
      'end_date': endDate.toIso8601String(),
      'cancelled_at': cancelledAt?.toIso8601String(),
      'metadata': metadata,
    };
  }

  Subscription copyWith({
    String? subscriptionId,
    String? userId,
    String? planId,
    SubscriptionStatus? status,
    DateTime? startDate,
    DateTime? endDate,
    DateTime? cancelledAt,
    Map<String, dynamic>? metadata,
  }) {
    return Subscription(
      subscriptionId: subscriptionId ?? this.subscriptionId,
      userId: userId ?? this.userId,
      planId: planId ?? this.planId,
      status: status ?? this.status,
      startDate: startDate ?? this.startDate,
      endDate: endDate ?? this.endDate,
      cancelledAt: cancelledAt ?? this.cancelledAt,
      metadata: metadata ?? this.metadata,
    );
  }

  bool get isActive => status == SubscriptionStatus.active;
  bool get isExpired => status == SubscriptionStatus.expired;
  bool get isCancelled => status == SubscriptionStatus.cancelled;

  Duration get duration => endDate.difference(startDate);
  int get daysRemaining {
    final now = DateTime.now();
    if (now.isAfter(endDate)) return 0;
    return endDate.difference(now).inDays;
  }

  bool get isExpiringSoon => daysRemaining <= 7 && daysRemaining > 0;

  @override
  String toString() {
    return 'Subscription(subscriptionId: $subscriptionId, status: $status, startDate: $startDate, endDate: $endDate)';
  }

  @override
  bool operator ==(Object other) {
    if (identical(this, other)) return true;
    return other is Subscription && other.subscriptionId == subscriptionId;
  }

  @override
  int get hashCode => subscriptionId.hashCode;
}
