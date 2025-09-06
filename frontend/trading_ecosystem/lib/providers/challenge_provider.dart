import 'package:flutter/foundation.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'dart:convert';
import '../models/challenge_template.dart';

class ChallengeData {
  final String challengeId;
  final String amount;
  final String price;
  final String profitTarget;
  final String maxDrawdown;
  final String dailyLimit;
  final ChallengeCategory category;

  ChallengeData({
    required this.challengeId,
    required this.amount,
    required this.price,
    required this.profitTarget,
    required this.maxDrawdown,
    required this.dailyLimit,
    required this.category,
  });

  Map<String, dynamic> toJson() {
    return {
      'challengeId': challengeId,
      'amount': amount,
      'price': price,
      'profitTarget': profitTarget,
      'maxDrawdown': maxDrawdown,
      'dailyLimit': dailyLimit,
      'category': category.name,
    };
  }

  factory ChallengeData.fromJson(Map<String, dynamic> json) {
    return ChallengeData(
      challengeId: json['challengeId'] ?? '',
      amount: json['amount'] ?? '',
      price: json['price'] ?? '',
      profitTarget: json['profitTarget'] ?? '',
      maxDrawdown: json['maxDrawdown'] ?? '',
      dailyLimit: json['dailyLimit'] ?? '',
      category: ChallengeCategory.values.firstWhere(
        (e) => e.name == json['category'],
        orElse: () => ChallengeCategory.stocks,
      ),
    );
  }
}

class ChallengeProvider extends ChangeNotifier {
  ChallengeData? _selectedChallenge;
  ChallengeData? get selectedChallenge => _selectedChallenge;

  // Set selected challenge
  void selectChallenge(ChallengeData challenge) {
    debugPrint('ChallengeProvider: Selecting challenge: ${challenge.toJson()}');
    _selectedChallenge = challenge;
    _saveChallengeToPrefs(challenge);
    notifyListeners();
    debugPrint('ChallengeProvider: Challenge selected and listeners notified');
  }

  // Clear selected challenge
  void clearChallenge() {
    debugPrint('ChallengeProvider: Clearing challenge');
    _selectedChallenge = null;
    _clearChallengeFromPrefs();
    notifyListeners();
    debugPrint('ChallengeProvider: Challenge cleared and listeners notified');
  }

  // Clear challenge when navigating from landing screen
  void clearForNewRegistration() {
    debugPrint('ChallengeProvider: Clearing challenge for new registration');
    clearChallenge();
  }

  // Load challenge from preferences on app start
  Future<void> loadChallengeFromPrefs() async {
    try {
      final prefs = await SharedPreferences.getInstance();
      final challengeJson = prefs.getString('selected_challenge');
      
      if (challengeJson != null) {
        final challengeData = ChallengeData.fromJson(
          Map<String, dynamic>.from(
            jsonDecode(challengeJson),
          ),
        );
        _selectedChallenge = challengeData;
        notifyListeners();
      }
    } catch (e) {
      debugPrint('Error loading challenge from preferences: $e');
    }
  }

  // Save challenge to preferences
  Future<void> _saveChallengeToPrefs(ChallengeData challenge) async {
    try {
      final prefs = await SharedPreferences.getInstance();
      final challengeJson = jsonEncode(challenge.toJson());
      await prefs.setString('selected_challenge', challengeJson);
    } catch (e) {
      debugPrint('Error saving challenge to preferences: $e');
    }
  }

  // Clear challenge from preferences
  Future<void> _clearChallengeFromPrefs() async {
    try {
      final prefs = await SharedPreferences.getInstance();
      await prefs.remove('selected_challenge');
    } catch (e) {
      debugPrint('Error clearing challenge from preferences: $e');
    }
  }
}
