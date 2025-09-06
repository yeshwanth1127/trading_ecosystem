import 'package:flutter/foundation.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';

class AuthProvider extends ChangeNotifier {
  bool _isLoggedIn = false;
  String? _authToken;
  String? _userId;
  Map<String, dynamic>? _user;
  bool _isInitialized = false;
  
  bool get isLoggedIn => _isLoggedIn;
  bool get isAuthenticated => _isLoggedIn;
  String? get authToken => _authToken;
  String? get token => _authToken;
  String? get userId => _userId;
  Map<String, dynamic>? get user => _user;
  bool get isInitialized => _isInitialized;

  final FlutterSecureStorage _storage = const FlutterSecureStorage();

  AuthProvider() {
    _checkAuthStatus();
  }

  // Check if user is already authenticated
  Future<void> _checkAuthStatus() async {
    try {
      print('AuthProvider: Checking authentication status...');
      final token = await _storage.read(key: 'auth_token');
      final userId = await _storage.read(key: 'user_id');
      
      print('AuthProvider: Token found: ${token != null}, User ID found: ${userId != null}');
      
      if (token != null && userId != null) {
        _authToken = token;
        _userId = userId;
        _isLoggedIn = true;
        print('AuthProvider: User is already logged in');
      } else {
        print('AuthProvider: No stored authentication found');
      }
      
      _isInitialized = true;
      notifyListeners();
    } catch (e) {
      print('Error checking auth status: $e');
      _isInitialized = true;
      notifyListeners();
    }
  }

  // Wait for authentication to be initialized
  Future<void> waitForInitialization() async {
    while (!_isInitialized) {
      await Future.delayed(const Duration(milliseconds: 100));
    }
  }

  // Login user
  Future<void> login(String token, String userId) async {
    try {
      await _storage.write(key: 'auth_token', value: token);
      await _storage.write(key: 'user_id', value: userId);
      
      _authToken = token;
      _userId = userId;
      _isLoggedIn = true;
      
      notifyListeners();
      debugPrint('AuthProvider: User logged in successfully');
    } catch (e) {
      debugPrint('Error saving auth data: $e');
    }
  }

  // Logout user
  Future<void> logout() async {
    try {
      await _storage.delete(key: 'auth_token');
      await _storage.delete(key: 'user_id');
      
      _authToken = null;
      _userId = null;
      _isLoggedIn = false;
      
      notifyListeners();
      debugPrint('AuthProvider: User logged out successfully');
    } catch (e) {
      debugPrint('Error clearing auth data: $e');
    }
  }

  // Clear auth data (for registration)
  Future<void> clearAuth() async {
    try {
      await _storage.delete(key: 'auth_token');
      await _storage.delete(key: 'user_id');
      
      _authToken = null;
      _userId = null;
      _isLoggedIn = false;
      
      notifyListeners();
      debugPrint('AuthProvider: Auth data cleared');
    } catch (e) {
      debugPrint('Error clearing auth data: $e');
    }
  }
}
