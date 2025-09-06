import 'package:dio/dio.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import '../models/api_response.dart';
import '../models/user.dart';
import '../models/account.dart';
import '../models/challenge_template.dart';
import '../models/challenge_attempt.dart';
import '../models/trade.dart';
import '../models/subscription_plan.dart';
import '../models/subscription.dart';

class ApiService {
  static const String baseUrl = 'http://localhost:8000/api/v1';
  static const String _tokenKey = 'auth_token';
  
  late final Dio _dio;
  final FlutterSecureStorage _storage = const FlutterSecureStorage();
  
  ApiService() {
    _dio = Dio(BaseOptions(
      baseUrl: baseUrl,
      connectTimeout: const Duration(seconds: 30),
      receiveTimeout: const Duration(seconds: 30),
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
      },
    ));
    
    _setupInterceptors();
  }
  
  void _setupInterceptors() {
    _dio.interceptors.add(
      InterceptorsWrapper(
        onRequest: (options, handler) async {
          final token = await _storage.read(key: _tokenKey);
          if (token != null) {
            options.headers['Authorization'] = 'Bearer $token';
          }
          handler.next(options);
        },
        onError: (error, handler) {
          if (error.response?.statusCode == 401) {
            // Handle unauthorized access
            _handleUnauthorized();
          }
          handler.next(error);
        },
      ),
    );
  }

  // Get stored token
  Future<String?> getToken() async {
    return await _storage.read(key: _tokenKey);
  }
  
  void _handleUnauthorized() {
    // Clear token and redirect to login
    _storage.delete(key: _tokenKey);
    // You can add navigation logic here
  }
  
  // Authentication
  Future<ApiResponse<Map<String, dynamic>>> login(String email, String password) async {
    try {
      final response = await _dio.post('/auth/login', data: {
        'email': email,
        'password': password,
      });
      
      if (response.statusCode == 200) {
        final token = response.data['access_token'];
        final userData = response.data['user'] ?? {};
        await _storage.write(key: _tokenKey, value: token);
        return ApiResponse.success({
          'access_token': token,
          'user_id': userData['user_id'] ?? '',
        });
      } else if (response.statusCode == 401) {
        return ApiResponse.error('Incorrect email or password');
      } else if (response.statusCode == 400) {
        final data = response.data;
        return ApiResponse.error('Invalid request: ${data['detail']}');
      }
      
      return ApiResponse.error('Login failed');
    } catch (e) {
      return ApiResponse.error('Network error: $e');
    }
  }
  
  Future<ApiResponse<void>> logout() async {
    try {
      await _dio.post('/auth/logout');
      await _storage.delete(key: _tokenKey);
      return ApiResponse.success(null);
    } catch (e) {
      await _storage.delete(key: _tokenKey); // Clear token even if logout fails
      return ApiResponse.success(null);
    }
  }
  
  Future<ApiResponse<User>> register(String email, String password, String fullName) async {
    try {
      final response = await _dio.post('/auth/register', data: {
        'email': email,
        'password': password,
        'name': fullName,
      });
      
      if (response.statusCode == 201) {
        final user = User.fromJson(response.data);
        return ApiResponse.success(user);
      } else if (response.statusCode == 400) {
        final data = response.data;
        final detail = data['detail'];
        if (detail == 'User with this email already exists') {
          return ApiResponse.error('User with this email already exists');
        }
        return ApiResponse.error('Invalid request: $detail');
      }
      
      return ApiResponse.error('Registration failed');
    } catch (e) {
      return ApiResponse.error('Network error: $e');
    }
  }
  
  // Users
  Future<ApiResponse<User>> getCurrentUser() async {
    try {
      final response = await _dio.get('/auth/me');
      if (response.statusCode == 200) {
        final user = User.fromJson(response.data);
        return ApiResponse.success(user);
      }
      return ApiResponse.error('Failed to get user');
    } catch (e) {
      return ApiResponse.error('Network error: $e');
    }
  }
  
  Future<ApiResponse<User>> updateUser(String userId, Map<String, dynamic> data) async {
    try {
      final response = await _dio.put('/users/$userId', data: data);
      if (response.statusCode == 200) {
        final user = User.fromJson(response.data);
        return ApiResponse.success(user);
      }
      return ApiResponse.error('Update failed');
    } catch (e) {
      return ApiResponse.error('Network error: $e');
    }
  }
  
  // Accounts
  Future<ApiResponse<List<Account>>> getUserAccounts() async {
    try {
      final response = await _dio.get('/accounts/');
      if (response.statusCode == 200) {
        final accounts = (response.data as List)
            .map((json) => Account.fromJson(json))
            .toList();
        return ApiResponse.success(accounts);
      }
      return ApiResponse.error('Failed to get accounts');
    } catch (e) {
      return ApiResponse.error('Network error: $e');
    }
  }
  
  Future<ApiResponse<Account>> createAccount(Map<String, dynamic> data) async {
    try {
      final response = await _dio.post('/accounts/', data: data);
      if (response.statusCode == 201) {
        final account = Account.fromJson(response.data);
        return ApiResponse.success(account);
      }
      return ApiResponse.error('Account creation failed');
    } catch (e) {
      return ApiResponse.error('Network error: $e');
    }
  }
  
  // Challenge Templates
  Future<ApiResponse<List<ChallengeTemplate>>> getChallengeTemplates() async {
    try {
      final response = await _dio.get('/challenges/templates/');
      if (response.statusCode == 200) {
        final templates = (response.data as List)
            .map((json) => ChallengeTemplate.fromJson(json))
            .toList();
        return ApiResponse.success(templates);
      }
      return ApiResponse.error('Failed to get challenge templates');
    } catch (e) {
      return ApiResponse.error('Network error: $e');
    }
  }
  
  // Challenge Attempts
  Future<ApiResponse<List<ChallengeAttempt>>> getUserChallenges() async {
    try {
      final response = await _dio.get('/challenges/attempts/');
      if (response.statusCode == 200) {
        final attempts = (response.data as List)
            .map((json) => ChallengeAttempt.fromJson(json))
            .toList();
        return ApiResponse.success(attempts);
      }
      return ApiResponse.error('Failed to get challenges');
    } catch (e) {
      return ApiResponse.error('Network error: $e');
    }
  }
  
  // Trading Challenges
  Future<ApiResponse<Map<String, dynamic>>> getCurrentUserActiveChallenge() async {
    try {
      final response = await _dio.get('/trading-challenges/me/active');
      if (response.statusCode == 200) {
        return ApiResponse.success(response.data);
      } else if (response.statusCode == 404) {
        return ApiResponse.error('No active challenge found');
      }
      return ApiResponse.error('Failed to get active challenge');
    } catch (e) {
      return ApiResponse.error('Network error: $e');
    }
  }
  
  Future<ApiResponse<Map<String, dynamic>>> getCurrentUserChallengeBalance() async {
    try {
      final response = await _dio.get('/trading-challenges/me/balance');
      if (response.statusCode == 200) {
        return ApiResponse.success(response.data);
      } else if (response.statusCode == 404) {
        return ApiResponse.error('No active challenge found');
      }
      return ApiResponse.error('Failed to get challenge balance');
    } catch (e) {
      return ApiResponse.error('Network error: $e');
    }
  }
  
  Future<ApiResponse<ChallengeAttempt>> startChallenge(String templateId, String accountId) async {
    try {
      final response = await _dio.post('/challenges/attempts/', data: {
        'challenge_template_id': templateId,
        'account_id': accountId,
      });
      
      if (response.statusCode == 201) {
        final attempt = ChallengeAttempt.fromJson(response.data);
        return ApiResponse.success(attempt);
      }
      return ApiResponse.error('Failed to start challenge');
    } catch (e) {
      return ApiResponse.error('Network error: $e');
    }
  }
  
  // Trades
  Future<ApiResponse<List<Trade>>> getUserTrades() async {
    try {
      final response = await _dio.get('/trades/');
      if (response.statusCode == 200) {
        final trades = (response.data as List)
            .map((json) => Trade.fromJson(json))
            .toList();
        return ApiResponse.success(trades);
      }
      return ApiResponse.error('Failed to get trades');
    } catch (e) {
      return ApiResponse.error('Network error: $e');
    }
  }
  
  Future<ApiResponse<Trade>> createTrade(Map<String, dynamic> data) async {
    try {
      final response = await _dio.post('/trades/', data: data);
      if (response.statusCode == 201) {
        final trade = Trade.fromJson(response.data);
        return ApiResponse.success(trade);
      }
      return ApiResponse.error('Trade creation failed');
    } catch (e) {
      return ApiResponse.error('Network error: $e');
    }
  }
  
  // Market Data
  Future<ApiResponse<Map<String, dynamic>>> getInstrumentPrice(String symbol, String marketType) async {
    try {
      final response = await _dio.get('/market-data/price/$symbol', queryParameters: {
        'market_type': marketType,
      });
      
      if (response.statusCode == 200) {
        return ApiResponse.success(response.data);
      } else if (response.statusCode == 404) {
        return ApiResponse.error('Instrument not found');
      }
      
      return ApiResponse.error('Failed to get instrument price');
    } on DioException catch (e) {
      if (e.type == DioExceptionType.connectionTimeout || e.type == DioExceptionType.receiveTimeout) {
        return ApiResponse.error('Request timeout. Please check your connection and try again.');
      } else if (e.type == DioExceptionType.connectionError) {
        return ApiResponse.error('Connection error. Please check if the server is running.');
      } else if (e.type == DioExceptionType.badResponse) {
        final statusCode = e.response?.statusCode;
        if (statusCode == 404) {
          return ApiResponse.error('Instrument not found');
        }
        return ApiResponse.error('Server error (Status: $statusCode)');
      }
      return ApiResponse.error('Network error: ${e.message}');
    } catch (e) {
      return ApiResponse.error('Unexpected error: $e');
    }
  }

  // Freqtrade proxy
  Future<ApiResponse<Map<String, dynamic>>> ftStart() async {
    try {
      final response = await _dio.post('/ft/start');
      if (response.statusCode == 200) {
        return ApiResponse.success(response.data);
      }
      return ApiResponse.error('Failed to start trading instance');
    } catch (e) {
      return ApiResponse.error('Network error: $e');
    }
  }

  Future<ApiResponse<Map<String, dynamic>>> ftStatus() async {
    try {
      final response = await _dio.get('/ft/status');
      if (response.statusCode == 200) {
        return ApiResponse.success(response.data);
      }
      return ApiResponse.error('Failed to get status');
    } catch (e) {
      return ApiResponse.error('Network error: $e');
    }
  }

  Future<ApiResponse<Map<String, dynamic>>> ftBalance() async {
    try {
      final response = await _dio.get('/ft/balance');
      if (response.statusCode == 200) {
        return ApiResponse.success(response.data);
      }
      return ApiResponse.error('Failed to get balance');
    } catch (e) {
      return ApiResponse.error('Network error: $e');
    }
  }

  Future<ApiResponse<Map<String, dynamic>>> ftPositions() async {
    try {
      final response = await _dio.get('/ft/positions');
      if (response.statusCode == 200) {
        return ApiResponse.success(response.data);
      }
      return ApiResponse.error('Failed to get positions');
    } catch (e) {
      return ApiResponse.error('Network error: $e');
    }
  }

  Future<ApiResponse<Map<String, dynamic>>> ftTrades() async {
    try {
      final response = await _dio.get('/ft/trades');
      if (response.statusCode == 200) {
        return ApiResponse.success(response.data);
      }
      return ApiResponse.error('Failed to get trades');
    } catch (e) {
      return ApiResponse.error('Network error: $e');
    }
  }

  Future<ApiResponse<Map<String, dynamic>>> ftOverview() async {
    try {
      final response = await _dio.get('/ft/overview');
      if (response.statusCode == 200) {
        return ApiResponse.success(Map<String, dynamic>.from(response.data));
      }
      return ApiResponse.error('Failed to get overview');
    } catch (e) {
      return ApiResponse.error('Network error: $e');
    }
  }

  Future<ApiResponse<Map<String, dynamic>>> ftForcebuy(String pair, {double? amount}) async {
    try {
      final response = await _dio.post('/ft/forcebuy', data: {
        'pair': pair,
        if (amount != null) 'amount': amount,
      });
      if (response.statusCode == 200) {
        return ApiResponse.success(Map<String, dynamic>.from(response.data));
      }
      return ApiResponse.error('Failed to place order');
    } catch (e) {
      return ApiResponse.error('Network error: $e');
    }
  }

  Future<ApiResponse<Map<String, dynamic>>> ftForcesell(String tradeId) async {
    try {
      final response = await _dio.post('/ft/forcesell', data: {
        'tradeid': tradeId,
      });
      if (response.statusCode == 200) {
        return ApiResponse.success(Map<String, dynamic>.from(response.data));
      }
      return ApiResponse.error('Failed to close trade');
    } catch (e) {
      return ApiResponse.error('Network error: $e');
    }
  }

  Future<ApiResponse<Map<String, dynamic>>> getMarketData({String? marketType}) async {
    try {
      final Map<String, dynamic>? queryParams = marketType != null ? {'market_type': marketType} : null;
      final response = await _dio.get('/market-data/instruments', queryParameters: queryParams);
      
      if (response.statusCode == 200) {
        return ApiResponse.success(response.data);
      }
      
      return ApiResponse.error('Failed to get market data');
    } on DioException catch (e) {
      if (e.type == DioExceptionType.connectionTimeout || e.type == DioExceptionType.receiveTimeout) {
        return ApiResponse.error('Request timeout. Please check your connection and try again.');
      } else if (e.type == DioExceptionType.connectionError) {
        return ApiResponse.error('Connection error. Please check if the server is running.');
      }
      return ApiResponse.error('Network error: ${e.message}');
    } catch (e) {
      return ApiResponse.error('Unexpected error: $e');
    }
  }

  // Position Management
  Future<ApiResponse<Map<String, dynamic>>> closePosition(String positionId, {double? closeQuantity}) async {
    try {
      // Check if we have a valid token before making the request
      final token = await getToken();
      if (token == null || token.isEmpty) {
        return ApiResponse.error('Authentication required. Please login again.');
      }

      final response = await _dio.post('/trading/positions/$positionId/close', data: {
        if (closeQuantity != null) 'close_quantity': closeQuantity,
      });
      
      if (response.statusCode == 200) {
        return ApiResponse.success(response.data);
      } else if (response.statusCode == 404) {
        return ApiResponse.error('Position not found');
      } else if (response.statusCode == 400) {
        final data = response.data;
        return ApiResponse.error('Invalid request: ${data['detail'] ?? 'Bad request'}');
      } else if (response.statusCode == 401) {
        return ApiResponse.error('Authentication expired. Please login again.');
      } else if (response.statusCode == 403) {
        return ApiResponse.error('Access denied. You do not have permission to close this position.');
      } else if (response.statusCode == 500) {
        return ApiResponse.error('Server error. Please try again later.');
      }
      
      return ApiResponse.error('Failed to close position (Status: ${response.statusCode})');
    } on DioException catch (e) {
      // Handle specific Dio exceptions
      if (e.type == DioExceptionType.connectionTimeout || e.type == DioExceptionType.receiveTimeout) {
        return ApiResponse.error('Request timeout. Please check your connection and try again.');
      } else if (e.type == DioExceptionType.connectionError) {
        return ApiResponse.error('Connection error. Please check if the server is running.');
      } else if (e.type == DioExceptionType.badResponse) {
        final statusCode = e.response?.statusCode;
        if (statusCode == 401) {
          return ApiResponse.error('Authentication expired. Please login again.');
        } else if (statusCode == 403) {
          return ApiResponse.error('Access denied. You do not have permission to close this position.');
        } else if (statusCode == 404) {
          return ApiResponse.error('Position not found');
        } else if (statusCode == 400) {
          final data = e.response?.data;
          return ApiResponse.error('Invalid request: ${data?['detail'] ?? 'Bad request'}');
        }
        return ApiResponse.error('Server error (Status: $statusCode)');
      } else if (e.type == DioExceptionType.cancel) {
        return ApiResponse.error('Request was cancelled');
      } else {
        return ApiResponse.error('Network error: ${e.message}');
      }
    } catch (e) {
      return ApiResponse.error('Unexpected error: $e');
    }
  }

  // Subscription Plans
  Future<ApiResponse<List<SubscriptionPlan>>> getSubscriptionPlans() async {
    try {
      final response = await _dio.get('/subscriptions/plans/');
      if (response.statusCode == 200) {
        final plans = (response.data as List)
            .map((json) => SubscriptionPlan.fromJson(json))
            .toList();
        return ApiResponse.success(plans);
      }
      return ApiResponse.error('Failed to get subscription plans');
    } catch (e) {
      return ApiResponse.error('Network error: $e');
    }
  }
  
  // Subscriptions
  Future<ApiResponse<List<Subscription>>> getUserSubscriptions() async {
    try {
      final response = await _dio.get('/subscriptions/');
      if (response.statusCode == 200) {
        final subscriptions = (response.data as List)
            .map((json) => Subscription.fromJson(json))
            .toList();
        return ApiResponse.success(subscriptions);
      }
      return ApiResponse.error('Failed to get subscriptions');
    } catch (e) {
      return ApiResponse.error('Network error: $e');
    }
  }
  
  Future<ApiResponse<Subscription>> subscribeToPlan(String planId) async {
    try {
      final response = await _dio.post('/subscriptions/', data: {
        'plan_id': planId,
      });
      
      if (response.statusCode == 201) {
        final subscription = Subscription.fromJson(response.data);
        return ApiResponse.success(subscription);
      }
      return ApiResponse.error('Subscription failed');
    } catch (e) {
      return ApiResponse.error('Network error: $e');
    }
  }
  
  // Challenge Selections
  Future<ApiResponse<Map<String, dynamic>>> createChallengeSelection(Map<String, dynamic> data) async {
    try {
      final response = await _dio.post('/challenge-selections/', data: data);
      if (response.statusCode == 201) {
        return ApiResponse.success(response.data);
      }
      return ApiResponse.error('Failed to create challenge selection');
    } catch (e) {
      if (e is DioException) {
        if (e.response?.statusCode == 400) {
          final detail = e.response?.data['detail'];
          if (detail == 'User already has an active challenge selection') {
            return ApiResponse.error('You already have an active challenge selection');
          }
          return ApiResponse.error('Invalid request: $detail');
        }
      }
      return ApiResponse.error('Network error: $e');
    }
  }
  
  Future<ApiResponse<List<Map<String, dynamic>>>> getUserChallengeSelections() async {
    try {
      final response = await _dio.get('/challenge-selections/my-selections');
      if (response.statusCode == 200) {
        final data = response.data;
        final selections = (data['selections'] as List).cast<Map<String, dynamic>>();
        return ApiResponse.success(selections);
      }
      return ApiResponse.error('Failed to get challenge selections');
    } catch (e) {
      return ApiResponse.error('Network error: $e');
    }
  }
  
  Future<ApiResponse<Map<String, dynamic>>> getActiveChallengeSelection() async {
    try {
      final response = await _dio.get('/challenge-selections/active');
      if (response.statusCode == 200) {
        return ApiResponse.success(response.data);
      } else if (response.statusCode == 404) {
        return ApiResponse.error('No active challenge selection found');
      }
      return ApiResponse.error('Failed to get active challenge selection');
    } catch (e) {
      return ApiResponse.error('Network error: $e');
    }
  }
  
  Future<ApiResponse<Map<String, dynamic>>> activateChallengeSelection(String selectionId) async {
    try {
      final response = await _dio.post('/challenge-selections/$selectionId/activate');
      if (response.statusCode == 200) {
        return ApiResponse.success(response.data);
      }
      return ApiResponse.error('Failed to activate challenge selection');
    } catch (e) {
      return ApiResponse.error('Network error: $e');
    }
  }
}
