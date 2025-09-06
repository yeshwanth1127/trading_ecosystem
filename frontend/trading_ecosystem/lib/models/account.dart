enum AccountType { demo, live, challenge }

class Account {
  final String accountId;
  final String userId;
  final String name;
  final AccountType type;
  final double balance;
  final String currency;
  final bool isActive;
  final DateTime createdAt;
  final DateTime? updatedAt;

  Account({
    required this.accountId,
    required this.userId,
    required this.name,
    required this.type,
    required this.balance,
    required this.currency,
    required this.isActive,
    required this.createdAt,
    this.updatedAt,
  });

  factory Account.fromJson(Map<String, dynamic> json) {
    return Account(
      accountId: json['account_id'] ?? '',
      userId: json['user_id'] ?? '',
      name: json['name'] ?? '',
      type: AccountType.values.firstWhere(
        (e) => e.name == json['type'],
        orElse: () => AccountType.demo,
      ),
      balance: (json['balance'] ?? 0.0).toDouble(),
      currency: json['currency'] ?? 'USD',
      isActive: json['is_active'] ?? true,
      createdAt: DateTime.parse(json['created_at'] ?? DateTime.now().toIso8601String()),
      updatedAt: json['updated_at'] != null 
          ? DateTime.parse(json['updated_at']) 
          : null,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'account_id': accountId,
      'user_id': userId,
      'name': name,
      'type': type.name,
      'balance': balance,
      'currency': currency,
      'is_active': isActive,
      'created_at': createdAt.toIso8601String(),
      'updated_at': updatedAt?.toIso8601String(),
    };
  }

  Account copyWith({
    String? accountId,
    String? userId,
    String? name,
    AccountType? type,
    double? balance,
    String? currency,
    bool? isActive,
    DateTime? createdAt,
    DateTime? updatedAt,
  }) {
    return Account(
      accountId: accountId ?? this.accountId,
      userId: userId ?? this.userId,
      name: name ?? this.name,
      type: type ?? this.type,
      balance: balance ?? this.balance,
      currency: currency ?? this.currency,
      isActive: isActive ?? this.isActive,
      createdAt: createdAt ?? this.createdAt,
      updatedAt: updatedAt ?? this.updatedAt,
    );
  }

  @override
  String toString() {
    return 'Account(accountId: $accountId, name: $name, type: $type, balance: $balance $currency)';
  }

  @override
  bool operator ==(Object other) {
    if (identical(this, other)) return true;
    return other is Account && other.accountId == accountId;
  }

  @override
  int get hashCode => accountId.hashCode;
}
