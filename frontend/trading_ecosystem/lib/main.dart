import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:flutter/foundation.dart';
import 'providers/auth_provider.dart';
import 'providers/trading_provider.dart';
import 'providers/challenge_provider.dart';
import 'screens/landing/landing_screen.dart';
import 'screens/demo/demo_dashboard_screen.dart';
import 'screens/trading/trading_screen.dart';
import 'screens/account/account_details_screen.dart';
import 'screens/auth/login_screen.dart';
import 'screens/auth/register_screen.dart';
import 'screens/services/services_screen.dart';
import 'screens/services/funded_challenges_screen.dart';
import 'screens/services/copy_trading_screen.dart';
import 'screens/services/algo_trading_screen.dart';

void main() {
  runApp(const TradingEcosystemApp());
}

class TradingEcosystemApp extends StatelessWidget {
  const TradingEcosystemApp({Key? key}) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return MultiProvider(
      providers: [
        ChangeNotifierProvider(create: (_) => AuthProvider()),
        ChangeNotifierProvider(create: (_) => TradingProvider()),
        ChangeNotifierProvider(create: (_) => ChallengeProvider()),
      ],
      child: MaterialApp(
        title: 'ORBIT Trading Ecosystem',
        theme: ThemeData(
          primarySwatch: Colors.blue,
          brightness: Brightness.dark,
          scaffoldBackgroundColor: const Color(0xFF0E1116),
          appBarTheme: const AppBarTheme(
            backgroundColor: Color(0xFF1E222D),
            foregroundColor: Colors.white,
            elevation: 0,
          ),
          elevatedButtonTheme: ElevatedButtonThemeData(
            style: ElevatedButton.styleFrom(
              backgroundColor: const Color(0xFF2962FF),
              foregroundColor: Colors.white,
              padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 12),
              shape: RoundedRectangleBorder(
                borderRadius: BorderRadius.circular(8),
              ),
            ),
          ),
          cardTheme: CardTheme(
            color: const Color(0xFF1E222D),
            elevation: 4,
            shape: RoundedRectangleBorder(
              borderRadius: BorderRadius.circular(12),
            ),
          ),
        ),
        home: Consumer<AuthProvider>(
          builder: (context, authProvider, child) {
            // Wait for authentication to be initialized
            if (!authProvider.isInitialized) {
              return const Scaffold(
                body: Center(
                  child: CircularProgressIndicator(),
                ),
              );
            }
            
            // Route based on authentication status
            if (authProvider.isLoggedIn) {
              return const DemoDashboardScreen();
            } else {
              return const LandingScreen();
            }
          },
        ),
        routes: {
          '/landing': (context) => const LandingScreen(),
          '/dashboard': (context) => const DemoDashboardScreen(),
          '/trading': (context) => const TradingScreen(),
          '/account': (context) => const AccountDetailsScreen(),
          '/login': (context) => const LoginScreen(),
          '/register': (context) => const RegisterScreen(),
          '/services': (context) => const ServicesScreen(),
          '/funded-challenges': (context) => const FundedChallengesScreen(),
          '/copy-trading': (context) => const CopyTradingScreen(),
          '/algo-trading': (context) => const AlgoTradingScreen(),
        },
      ),
    );
  }
}

// Web platform registration for TradingView widget
void registerWebViewFactories() {
  if (kIsWeb) {
    // Register the TradingView widget for web platform
    // This enables the HtmlElementView to work properly
    // In a real implementation, you would register custom elements here
  }
}
