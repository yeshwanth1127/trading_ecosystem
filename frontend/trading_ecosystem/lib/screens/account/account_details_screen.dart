import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../../services/api_service.dart';
import '../../utils/theme.dart';
import '../../models/user.dart';
import '../../providers/auth_provider.dart';

class AccountDetailsScreen extends StatefulWidget {
  const AccountDetailsScreen({super.key});

  @override
  State<AccountDetailsScreen> createState() => _AccountDetailsScreenState();
}

class _AccountDetailsScreenState extends State<AccountDetailsScreen> {
  final ApiService _apiService = ApiService();
  
  User? _currentUser;
  Map<String, dynamic>? _activeChallengeSelection;
  List<Map<String, dynamic>>? _allChallengeSelections;
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
      
      // Get all challenge selections
      final allSelectionsResult = await _apiService.getUserChallengeSelections();
      if (allSelectionsResult.isSuccess) {
        _allChallengeSelections = allSelectionsResult.data;
      }
      
    } catch (e) {
      setState(() => _error = e.toString());
    } finally {
      setState(() => _isLoading = false);
    }
  }

  Future<void> _handleLogout() async {
    // Show confirmation dialog
    final shouldLogout = await showDialog<bool>(
      context: context,
      builder: (BuildContext context) {
        return AlertDialog(
          backgroundColor: AppTheme.surfaceBackground,
          title: Text(
            'Logout',
            style: TextStyle(color: AppTheme.textPrimary),
          ),
          content: Text(
            'Are you sure you want to logout?',
            style: TextStyle(color: AppTheme.textSecondary),
          ),
          actions: [
            TextButton(
              onPressed: () => Navigator.of(context).pop(false),
              child: Text(
                'Cancel',
                style: TextStyle(color: AppTheme.textSecondary),
              ),
            ),
            ElevatedButton(
              onPressed: () => Navigator.of(context).pop(true),
              style: ElevatedButton.styleFrom(
                backgroundColor: AppTheme.warningNeon,
                foregroundColor: Colors.white,
              ),
              child: const Text('Logout'),
            ),
          ],
        );
      },
    );

    if (shouldLogout == true) {
      // Get auth provider and logout
      final authProvider = Provider.of<AuthProvider>(context, listen: false);
      await authProvider.logout();
      
      // Navigate to landing screen and clear all previous routes
      if (mounted) {
        Navigator.of(context).pushNamedAndRemoveUntil(
          '/landing',
          (Route<dynamic> route) => false,
        );
        
        // Show success message
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: const Text('Logged out successfully'),
            backgroundColor: AppTheme.successNeon,
            duration: const Duration(seconds: 2),
          ),
        );
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppTheme.darkBackground,
      appBar: AppBar(
        title: const Text('Account Details', style: TextStyle(color: AppTheme.textPrimary)),
        backgroundColor: AppTheme.surfaceBackground,
        foregroundColor: AppTheme.textPrimary,
        elevation: 0,
        leading: IconButton(
          icon: const Icon(Icons.arrow_back),
          onPressed: () => Navigator.pop(context),
        ),
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh),
            onPressed: _loadUserData,
            tooltip: 'Refresh Data',
          ),
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
              : _buildAccountDetailsContent(),
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

  Widget _buildAccountDetailsContent() {
    return SingleChildScrollView(
      padding: const EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          _buildHeader(),
          const SizedBox(height: 24),
          _buildUserInfoCard(),
          const SizedBox(height: 16),
          _buildChallengeSelectionCard(),
          const SizedBox(height: 16),
          _buildAllSelectionsCard(),
          const SizedBox(height: 16),
          _buildSystemInfoCard(),
          const SizedBox(height: 16),
          _buildLogoutCard(),
        ],
      ),
    );
  }

  Widget _buildHeader() {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        gradient: LinearGradient(
          colors: [
            AppTheme.primaryNeon.withOpacity(0.1),
            AppTheme.secondaryNeon.withOpacity(0.1),
          ],
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
        ),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: AppTheme.primaryNeon.withOpacity(0.3)),
      ),
      child: Column(
        children: [
          Icon(
            Icons.account_circle,
            size: 48,
            color: AppTheme.primaryNeon,
          ),
          const SizedBox(height: 16),
          Text(
            'Account Details',
            style: TextStyle(
              color: AppTheme.primaryNeon,
              fontSize: 24,
              fontWeight: FontWeight.bold,
            ),
          ),
          const SizedBox(height: 8),
          Text(
            'Complete User Information & Challenge Data',
            style: TextStyle(
              color: AppTheme.textSecondary,
              fontSize: 16,
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildUserInfoCard() {
    return _buildInfoCard(
      title: 'User Information',
      icon: Icons.person,
      color: AppTheme.primaryNeon,
      child: _currentUser != null
          ? Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                _buildInfoRow('User ID', _currentUser!.userId),
                _buildInfoRow('Name', _currentUser!.fullName),
                _buildInfoRow('Email', _currentUser!.email),
                _buildInfoRow('Role', _currentUser!.role.name),
                _buildInfoRow('Status', _currentUser!.isActive ? 'Active' : 'Inactive'),
                _buildInfoRow('Created At', _currentUser!.createdAt.toString()),
                if (_currentUser!.updatedAt != null)
                  _buildInfoRow('Updated At', _currentUser!.updatedAt.toString()),
              ],
            )
          : const Text('No user data available', style: TextStyle(color: AppTheme.textSecondary)),
    );
  }

  Widget _buildChallengeSelectionCard() {
    return _buildInfoCard(
      title: 'Active Challenge Selection',
      icon: Icons.flag,
      color: AppTheme.secondaryNeon,
      child: _activeChallengeSelection != null
          ? Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                _buildInfoRow('Selection ID', _activeChallengeSelection!['selection_id'] ?? 'N/A'),
                _buildInfoRow('Challenge ID', _activeChallengeSelection!['challenge_id'] ?? 'N/A'),
                _buildInfoRow('Amount', _activeChallengeSelection!['amount'] ?? 'N/A'),
                _buildInfoRow('Price', _activeChallengeSelection!['price'] ?? 'N/A'),
                _buildInfoRow('Profit Target', _activeChallengeSelection!['profit_target'] ?? 'N/A'),
                _buildInfoRow('Max Drawdown', _activeChallengeSelection!['max_drawdown'] ?? 'N/A'),
                _buildInfoRow('Daily Limit', _activeChallengeSelection!['daily_limit'] ?? 'N/A'),
                _buildInfoRow('Status', _activeChallengeSelection!['status'] ?? 'N/A'),
                _buildInfoRow('Created At', _activeChallengeSelection!['created_at'] ?? 'N/A'),
                if (_activeChallengeSelection!['activated_at'] != null)
                  _buildInfoRow('Activated At', _activeChallengeSelection!['activated_at']),
                if (_activeChallengeSelection!['trading_started_at'] != null)
                  _buildInfoRow('Trading Started At', _activeChallengeSelection!['trading_started_at']),
              ],
            )
          : const Text('No active challenge selection', style: TextStyle(color: AppTheme.textSecondary)),
    );
  }

  Widget _buildAllSelectionsCard() {
    return _buildInfoCard(
      title: 'All Challenge Selections',
      icon: Icons.list,
      color: AppTheme.accentNeon,
      child: _allChallengeSelections != null && _allChallengeSelections!.isNotEmpty
          ? Column(
              children: _allChallengeSelections!.map((selection) {
                return Container(
                  margin: const EdgeInsets.only(bottom: 12),
                  padding: const EdgeInsets.all(12),
                  decoration: BoxDecoration(
                    color: AppTheme.surfaceBackground,
                    borderRadius: BorderRadius.circular(8),
                    border: Border.all(color: AppTheme.accentNeon.withOpacity(0.3)),
                  ),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        'Challenge: ${selection['challenge_id'] ?? 'N/A'}',
                        style: TextStyle(
                          color: AppTheme.accentNeon,
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                      const SizedBox(height: 8),
                      _buildInfoRow('Amount', selection['amount'] ?? 'N/A'),
                      _buildInfoRow('Status', selection['status'] ?? 'N/A'),
                      _buildInfoRow('Created', selection['created_at'] ?? 'N/A'),
                    ],
                  ),
                );
              }).toList(),
            )
          : const Text('No challenge selections found', style: TextStyle(color: AppTheme.textSecondary)),
    );
  }

  Widget _buildSystemInfoCard() {
    return _buildInfoCard(
      title: 'System Information',
      icon: Icons.info,
      color: AppTheme.warningNeon,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          _buildInfoRow('Data Loaded At', DateTime.now().toString()),
          _buildInfoRow('User Data Status', _currentUser != null ? '✅ Loaded' : '❌ Not Loaded'),
          _buildInfoRow('Challenge Selection Status', _activeChallengeSelection != null ? '✅ Loaded' : '❌ Not Loaded'),
          _buildInfoRow('All Selections Status', _allChallengeSelections != null ? '✅ Loaded' : '❌ Not Loaded'),
          _buildInfoRow('Total Selections', _allChallengeSelections?.length.toString() ?? '0'),
        ],
      ),
    );
  }

  Widget _buildLogoutCard() {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        color: AppTheme.surfaceBackground,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: AppTheme.warningNeon.withOpacity(0.3)),
        boxShadow: [
          BoxShadow(
            color: AppTheme.warningNeon.withOpacity(0.1),
            blurRadius: 10,
            offset: const Offset(0, 4),
          ),
        ],
      ),
      child: Column(
        children: [
          Row(
            children: [
              Icon(Icons.logout, color: AppTheme.warningNeon, size: 24),
              const SizedBox(width: 12),
              Text(
                'Account Actions',
                style: TextStyle(
                  color: AppTheme.warningNeon,
                  fontSize: 18,
                  fontWeight: FontWeight.bold,
                ),
              ),
            ],
          ),
          const SizedBox(height: 16),
          Text(
            'Sign out of your account and return to the landing screen.',
            style: TextStyle(
              color: AppTheme.textSecondary,
              fontSize: 14,
            ),
            textAlign: TextAlign.center,
          ),
          const SizedBox(height: 20),
          SizedBox(
            width: double.infinity,
            child: ElevatedButton.icon(
              onPressed: _handleLogout,
              icon: const Icon(Icons.logout),
              label: const Text('Logout'),
              style: ElevatedButton.styleFrom(
                backgroundColor: AppTheme.warningNeon,
                foregroundColor: Colors.white,
                padding: const EdgeInsets.symmetric(vertical: 16),
                shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(8),
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildInfoCard({
    required String title,
    required IconData icon,
    required Color color,
    required Widget child,
  }) {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: AppTheme.surfaceBackground,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: color.withOpacity(0.3)),
        boxShadow: [
          BoxShadow(
            color: color.withOpacity(0.1),
            blurRadius: 10,
            offset: const Offset(0, 4),
          ),
        ],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Icon(icon, color: color, size: 24),
              const SizedBox(width: 12),
              Text(
                title,
                style: TextStyle(
                  color: color,
                  fontSize: 18,
                  fontWeight: FontWeight.bold,
                ),
              ),
            ],
          ),
          const SizedBox(height: 16),
          child,
        ],
      ),
    );
  }

  Widget _buildInfoRow(String label, String value) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 8),
      child: Row(
        children: [
          SizedBox(
            width: 120,
            child: Text(
              '$label:',
              style: TextStyle(
                color: AppTheme.textSecondary,
                fontSize: 14,
                fontWeight: FontWeight.w500,
              ),
            ),
          ),
          Expanded(
            child: Text(
              value,
              style: TextStyle(
                color: AppTheme.textPrimary,
                fontSize: 14,
              ),
            ),
          ),
        ],
      ),
    );
  }
}
