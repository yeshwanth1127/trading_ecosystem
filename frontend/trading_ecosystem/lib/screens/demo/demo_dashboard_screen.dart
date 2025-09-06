import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../../providers/auth_provider.dart';
import '../../services/api_service.dart';
import '../../utils/theme.dart';
import '../../models/user.dart';

class DemoDashboardScreen extends StatefulWidget {
  const DemoDashboardScreen({super.key});

  @override
  State<DemoDashboardScreen> createState() => _DemoDashboardScreenState();
}

class _DemoDashboardScreenState extends State<DemoDashboardScreen> {
  final ApiService _apiService = ApiService();
  
  User? _currentUser;
  Map<String, dynamic>? _activeChallengeSelection;
  bool _isLoading = true;
  String? _error;

  @override
  void initState() {
    super.initState();
    _loadUserData();
  }

  Future<void> _loadUserData() async {
    try {
      setState(() => _isLoading = true);
      
      // Check if user is authenticated first
      final authProvider = Provider.of<AuthProvider>(context, listen: false);
      if (!authProvider.isAuthenticated) {
        setState(() => _error = 'User not authenticated');
        return;
      }
      
      // Get current user
      final userResult = await _apiService.getCurrentUser();
      if (userResult.isSuccess) {
        _currentUser = userResult.data;
      }
      
      // Get active challenge selection
      final activeSelectionResult = await _apiService.getActiveChallengeSelection();
      if (activeSelectionResult.isSuccess) {
        _activeChallengeSelection = activeSelectionResult.data;
      }
      
    } catch (e) {
      setState(() => _error = e.toString());
    } finally {
      setState(() => _isLoading = false);
    }
  }

  Future<void> _handleLogout() async {
    try {
      final authProvider = Provider.of<AuthProvider>(context, listen: false);
      await authProvider.logout();
      
      if (mounted) {
        Navigator.pushReplacementNamed(context, '/');
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('Logout error: $e'),
            backgroundColor: AppTheme.warningNeon,
          ),
        );
      }
    }
  }

  void _navigateToTrading() {
    Navigator.pushReplacementNamed(context, '/trading');
  }

  void _navigateToAccountDetails() {
    Navigator.pushNamed(context, '/account');
  }

  @override
  Widget build(BuildContext context) {
    final screenSize = MediaQuery.of(context).size;
    final isMobile = screenSize.width < 600;
    final isTablet = screenSize.width >= 600 && screenSize.width < 1200;
    
    return Scaffold(
      backgroundColor: AppTheme.darkBackground,
      appBar: AppBar(
        title: Text(
          'Welcome to ORBIT', 
          style: TextStyle(
            color: AppTheme.textPrimary,
            fontSize: isMobile ? 18 : 20,
          ),
        ),
        backgroundColor: AppTheme.surfaceBackground,
        foregroundColor: AppTheme.textPrimary,
        elevation: 0,
        actions: [
          IconButton(
            icon: const Icon(Icons.logout),
            onPressed: _handleLogout,
            tooltip: 'Logout',
          ),
        ],
      ),
      body: _isLoading
          ? const Center(child: CircularProgressIndicator(color: AppTheme.primaryNeon))
          : _error != null
              ? _buildErrorWidget()
              : _buildWelcomeContent(isMobile, isTablet),
    );
  }

  Widget _buildErrorWidget() {
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Icon(Icons.error_outline, size: 64, color: AppTheme.warningNeon),
          const SizedBox(height: 16),
          Text('Error loading data:', style: TextStyle(color: AppTheme.textPrimary, fontSize: 18)),
          const SizedBox(height: 8),
          Text(_error!, style: TextStyle(color: AppTheme.textSecondary, fontSize: 14)),
          const SizedBox(height: 16),
          ElevatedButton(
            onPressed: _loadUserData,
            child: const Text('Retry'),
          ),
        ],
      ),
    );
  }

  Widget _buildWelcomeContent(bool isMobile, bool isTablet) {
    return SingleChildScrollView(
      padding: EdgeInsets.all(isMobile ? 16 : isTablet ? 24 : 32),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          _buildWelcomeHeader(isMobile, isTablet),
          SizedBox(height: isMobile ? 24 : 32),
          _buildTradingPanelCard(isMobile, isTablet),
          SizedBox(height: isMobile ? 20 : 24),
          _buildAccountDetailsCard(isMobile, isTablet),
          SizedBox(height: isMobile ? 20 : 24),
          _buildUserInfoCard(isMobile, isTablet),
        ],
      ),
    );
  }

  Widget _buildWelcomeHeader(bool isMobile, bool isTablet) {
    return Container(
      width: double.infinity,
      padding: EdgeInsets.all(isMobile ? 20 : isTablet ? 24 : 28),
      decoration: BoxDecoration(
        gradient: LinearGradient(
          colors: [
            AppTheme.primaryNeon.withOpacity(0.1),
            AppTheme.secondaryNeon.withOpacity(0.1),
          ],
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
        ),
        borderRadius: BorderRadius.circular(isMobile ? 12 : 16),
        border: Border.all(color: AppTheme.primaryNeon.withOpacity(0.3)),
      ),
      child: Column(
        children: [
          Icon(
            Icons.rocket_launch,
            size: isMobile ? 48 : isTablet ? 56 : 64,
            color: AppTheme.primaryNeon,
          ),
          SizedBox(height: isMobile ? 16 : 20),
          Text(
            'Welcome to ORBIT Trading',
            style: TextStyle(
              color: AppTheme.primaryNeon,
              fontSize: isMobile ? 22 : isTablet ? 26 : 28,
              fontWeight: FontWeight.bold,
            ),
            textAlign: TextAlign.center,
          ),
          SizedBox(height: isMobile ? 8 : 12),
          Text(
            'Your Professional Trading Platform',
            style: TextStyle(
              color: AppTheme.textSecondary,
              fontSize: isMobile ? 16 : 18,
            ),
            textAlign: TextAlign.center,
          ),
          SizedBox(height: isMobile ? 6 : 8),
          Text(
            'Ready to start trading? Access your dashboard below.',
            style: TextStyle(
              color: AppTheme.textSecondary,
              fontSize: isMobile ? 12 : 14,
            ),
            textAlign: TextAlign.center,
          ),
        ],
      ),
    );
  }

  Widget _buildTradingPanelCard(bool isMobile, bool isTablet) {
    return Container(
      width: double.infinity,
      padding: EdgeInsets.all(isMobile ? 20 : isTablet ? 24 : 28),
      decoration: BoxDecoration(
        color: AppTheme.surfaceBackground,
        borderRadius: BorderRadius.circular(isMobile ? 12 : 16),
        border: Border.all(color: AppTheme.primaryNeon.withOpacity(0.3)),
        boxShadow: [
          BoxShadow(
            color: AppTheme.primaryNeon.withOpacity(0.1),
            blurRadius: 20,
            offset: const Offset(0, 10),
          ),
        ],
      ),
      child: Column(
        children: [
          Icon(
            Icons.trending_up,
            size: isMobile ? 40 : isTablet ? 44 : 48,
            color: AppTheme.primaryNeon,
          ),
          SizedBox(height: isMobile ? 16 : 20),
          Text(
            'Trading Dashboard',
            style: TextStyle(
              color: AppTheme.textPrimary,
              fontSize: isMobile ? 20 : isTablet ? 22 : 24,
              fontWeight: FontWeight.bold,
            ),
            textAlign: TextAlign.center,
          ),
          SizedBox(height: isMobile ? 8 : 12),
          Text(
            'Access your professional trading interface with real-time charts, order management, and portfolio tracking.',
            style: TextStyle(
              color: AppTheme.textSecondary,
              fontSize: isMobile ? 14 : 16,
            ),
            textAlign: TextAlign.center,
          ),
          SizedBox(height: isMobile ? 20 : 24),
          SizedBox(
            width: double.infinity,
            height: isMobile ? 48 : 56,
            child: ElevatedButton(
              onPressed: _navigateToTrading,
              style: ElevatedButton.styleFrom(
                backgroundColor: AppTheme.primaryNeon,
                foregroundColor: Colors.black,
                shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(isMobile ? 8 : 12),
                ),
                elevation: 8,
                shadowColor: AppTheme.primaryNeon.withOpacity(0.5),
              ),
              child: Row(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  Icon(Icons.dashboard, size: isMobile ? 20 : 24),
                  SizedBox(width: isMobile ? 8 : 12),
                  Text(
                    'Launch Trading Dashboard',
                    style: TextStyle(
                      fontSize: isMobile ? 16 : 18,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildAccountDetailsCard(bool isMobile, bool isTablet) {
    return Container(
      width: double.infinity,
      padding: EdgeInsets.all(isMobile ? 20 : isTablet ? 24 : 28),
      decoration: BoxDecoration(
        color: AppTheme.surfaceBackground,
        borderRadius: BorderRadius.circular(isMobile ? 12 : 16),
        border: Border.all(color: AppTheme.secondaryNeon.withOpacity(0.3)),
        boxShadow: [
          BoxShadow(
            color: AppTheme.secondaryNeon.withOpacity(0.1),
            blurRadius: 20,
            offset: const Offset(0, 10),
          ),
        ],
      ),
      child: Column(
        children: [
          Icon(
            Icons.account_circle,
            size: isMobile ? 40 : isTablet ? 44 : 48,
            color: AppTheme.secondaryNeon,
          ),
          SizedBox(height: isMobile ? 16 : 20),
          Text(
            'Account Details',
            style: TextStyle(
              color: AppTheme.textPrimary,
              fontSize: isMobile ? 20 : isTablet ? 22 : 24,
              fontWeight: FontWeight.bold,
            ),
            textAlign: TextAlign.center,
          ),
          SizedBox(height: isMobile ? 8 : 12),
          Text(
            'View your profile information, challenge selections, and account statistics.',
            style: TextStyle(
              color: AppTheme.textSecondary,
              fontSize: isMobile ? 14 : 16,
            ),
            textAlign: TextAlign.center,
          ),
          SizedBox(height: isMobile ? 20 : 24),
          SizedBox(
            width: double.infinity,
            height: isMobile ? 48 : 56,
            child: ElevatedButton(
              onPressed: _navigateToAccountDetails,
              style: ElevatedButton.styleFrom(
                backgroundColor: AppTheme.secondaryNeon,
                foregroundColor: Colors.black,
                shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(isMobile ? 8 : 12),
                ),
                elevation: 8,
                shadowColor: AppTheme.secondaryNeon.withOpacity(0.5),
              ),
              child: Row(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  Icon(Icons.person, size: isMobile ? 20 : 24),
                  SizedBox(width: isMobile ? 8 : 12),
                  Text(
                    'View Account Details',
                    style: TextStyle(
                      fontSize: isMobile ? 16 : 18,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildUserInfoCard(bool isMobile, bool isTablet) {
    if (_currentUser == null) return const SizedBox.shrink();
    
    return Container(
      width: double.infinity,
      padding: EdgeInsets.all(isMobile ? 16 : isTablet ? 20 : 24),
      decoration: BoxDecoration(
        color: AppTheme.surfaceBackground,
        borderRadius: BorderRadius.circular(isMobile ? 12 : 16),
        border: Border.all(color: AppTheme.textSecondary.withOpacity(0.2)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            'Quick User Info',
            style: TextStyle(
              color: AppTheme.textPrimary,
              fontSize: isMobile ? 16 : 18,
              fontWeight: FontWeight.bold,
            ),
          ),
          SizedBox(height: isMobile ? 12 : 16),
          Row(
            children: [
              Icon(Icons.email, color: AppTheme.textSecondary, size: isMobile ? 18 : 20),
              SizedBox(width: isMobile ? 8 : 12),
              Expanded(
                child: Text(
                  _currentUser!.email,
                  style: TextStyle(
                    color: AppTheme.textSecondary,
                    fontSize: isMobile ? 14 : 16,
                  ),
                ),
              ),
            ],
          ),
          SizedBox(height: isMobile ? 6 : 8),
          Row(
            children: [
              Icon(Icons.person, color: AppTheme.textSecondary, size: isMobile ? 18 : 20),
              SizedBox(width: isMobile ? 8 : 12),
              Expanded(
                child: Text(
                  _currentUser!.fullName ?? 'N/A',
                  style: TextStyle(
                    color: AppTheme.textSecondary,
                    fontSize: isMobile ? 14 : 16,
                  ),
                ),
              ),
            ],
          ),
          if (_activeChallengeSelection != null) ...[
            SizedBox(height: isMobile ? 6 : 8),
            Row(
              children: [
                Icon(Icons.flag, color: AppTheme.primaryNeon, size: isMobile ? 18 : 20),
                SizedBox(width: isMobile ? 8 : 12),
                Expanded(
                  child: Text(
                    'Active Challenge: ${_activeChallengeSelection!['challengeId']}',
                    style: TextStyle(
                      color: AppTheme.primaryNeon, 
                      fontWeight: FontWeight.w500,
                      fontSize: isMobile ? 14 : 16,
                    ),
                  ),
                ),
              ],
            ),
          ],
        ],
      ),
    );
  }
}
