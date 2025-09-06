enum ChallengeCategory { stocks, crypto }

class ChallengeTemplate {
  final String challengeId;
  final String name;
  final String description;
  final double targetProfit;
  final double maxDrawdown;
  final int durationDays;
  final double initialBalance;
  final String currency;
  final ChallengeCategory category;
  final Map<String, dynamic> rules;
  final bool isActive;
  final DateTime createdAt;
  final DateTime? updatedAt;

  ChallengeTemplate({
    required this.challengeId,
    required this.name,
    required this.description,
    required this.targetProfit,
    required this.maxDrawdown,
    required this.durationDays,
    required this.initialBalance,
    required this.currency,
    required this.category,
    required this.rules,
    required this.isActive,
    required this.createdAt,
    this.updatedAt,
  });

  factory ChallengeTemplate.fromJson(Map<String, dynamic> json) {
    return ChallengeTemplate(
      challengeId: json['challenge_id'] ?? '',
      name: json['name'] ?? '',
      description: json['description'] ?? '',
      targetProfit: (json['target_profit'] ?? 0.0).toDouble(),
      maxDrawdown: (json['max_drawdown'] ?? 0.0).toDouble(),
      durationDays: json['duration_days'] ?? 30,
      initialBalance: (json['initial_balance'] ?? 0.0).toDouble(),
      currency: json['currency'] ?? 'USD',
      category: ChallengeCategory.values.firstWhere(
        (e) => e.name == json['category'],
        orElse: () => ChallengeCategory.stocks,
      ),
      rules: json['rules'] ?? {},
      isActive: json['is_active'] ?? true,
      createdAt: DateTime.parse(json['created_at'] ?? DateTime.now().toIso8601String()),
      updatedAt: json['updated_at'] != null 
          ? DateTime.parse(json['updated_at']) 
          : null,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'challenge_id': challengeId,
      'name': name,
      'description': description,
      'target_profit': targetProfit,
      'max_drawdown': maxDrawdown,
      'duration_days': durationDays,
      'initial_balance': initialBalance,
      'currency': currency,
      'category': category.name,
      'rules': rules,
      'is_active': isActive,
      'created_at': createdAt.toIso8601String(),
      'updated_at': updatedAt?.toIso8601String(),
    };
  }

  ChallengeTemplate copyWith({
    String? challengeId,
    String? name,
    String? description,
    double? targetProfit,
    double? maxDrawdown,
    int? durationDays,
    double? initialBalance,
    String? currency,
    ChallengeCategory? category,
    Map<String, dynamic>? rules,
    bool? isActive,
    DateTime? createdAt,
    DateTime? updatedAt,
  }) {
    return ChallengeTemplate(
      challengeId: challengeId ?? this.challengeId,
      name: name ?? this.name,
      description: description ?? this.description,
      targetProfit: targetProfit ?? this.targetProfit,
      maxDrawdown: maxDrawdown ?? this.maxDrawdown,
      durationDays: durationDays ?? this.durationDays,
      initialBalance: initialBalance ?? this.initialBalance,
      currency: currency ?? this.currency,
      category: category ?? this.category,
      rules: rules ?? this.rules,
      isActive: isActive ?? this.isActive,
      createdAt: createdAt ?? this.createdAt,
      updatedAt: updatedAt ?? this.updatedAt,
    );
  }

  @override
  String toString() {
    return 'ChallengeTemplate(challengeId: $challengeId, name: $name, targetProfit: $targetProfit%, maxDrawdown: $maxDrawdown%)';
  }

  @override
  bool operator ==(Object other) {
    if (identical(this, other)) return true;
    return other is ChallengeTemplate && other.challengeId == challengeId;
  }

  @override
  int get hashCode => challengeId.hashCode;
}
