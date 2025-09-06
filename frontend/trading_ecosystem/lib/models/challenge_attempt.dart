enum ChallengeState { active, passed, failed }

class ChallengeAttempt {
  final String attemptId;
  final String userId;
  final String challengeId;
  final String accountId;
  final ChallengeState state;
  final DateTime startedAt;
  final DateTime? endedAt;
  final Map<String, dynamic>? metrics;

  ChallengeAttempt({
    required this.attemptId,
    required this.userId,
    required this.challengeId,
    required this.accountId,
    required this.state,
    required this.startedAt,
    this.endedAt,
    this.metrics,
  });

  factory ChallengeAttempt.fromJson(Map<String, dynamic> json) {
    return ChallengeAttempt(
      attemptId: json['attempt_id'] ?? '',
      userId: json['user_id'] ?? '',
      challengeId: json['challenge_id'] ?? '',
      accountId: json['account_id'] ?? '',
      state: ChallengeState.values.firstWhere(
        (e) => e.name == json['state'],
        orElse: () => ChallengeState.active,
      ),
      startedAt: DateTime.parse(json['started_at'] ?? DateTime.now().toIso8601String()),
      endedAt: json['ended_at'] != null 
          ? DateTime.parse(json['ended_at']) 
          : null,
      metrics: json['metrics'],
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'attempt_id': attemptId,
      'user_id': userId,
      'challenge_id': challengeId,
      'account_id': accountId,
      'state': state.name,
      'started_at': startedAt.toIso8601String(),
      'ended_at': endedAt?.toIso8601String(),
      'metrics': metrics,
    };
  }

  ChallengeAttempt copyWith({
    String? attemptId,
    String? userId,
    String? challengeId,
    String? accountId,
    ChallengeState? state,
    DateTime? startedAt,
    DateTime? endedAt,
    Map<String, dynamic>? metrics,
  }) {
    return ChallengeAttempt(
      attemptId: attemptId ?? this.attemptId,
      userId: userId ?? this.userId,
      challengeId: challengeId ?? this.challengeId,
      accountId: accountId ?? this.accountId,
      state: state ?? this.state,
      startedAt: startedAt ?? this.startedAt,
      endedAt: endedAt ?? this.endedAt,
      metrics: metrics ?? this.metrics,
    );
  }

  bool get isActive => state == ChallengeState.active;
  bool get isPassed => state == ChallengeState.passed;
  bool get isFailed => state == ChallengeState.failed;

  Duration get duration {
    final end = endedAt ?? DateTime.now();
    return end.difference(startedAt);
  }

  int get daysRemaining {
    if (endedAt != null) return 0;
    final now = DateTime.now();
    final end = startedAt.add(const Duration(days: 30)); // Assuming 30-day challenges
    return end.difference(now).inDays;
  }

  @override
  String toString() {
    return 'ChallengeAttempt(attemptId: $attemptId, state: $state, startedAt: $startedAt)';
  }

  @override
  bool operator ==(Object other) {
    if (identical(this, other)) return true;
    return other is ChallengeAttempt && other.attemptId == attemptId;
  }

  @override
  int get hashCode => attemptId.hashCode;
}
