import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../../utils/theme.dart';
import '../../providers/challenge_provider.dart';
import '../../providers/auth_provider.dart';
import '../../services/api_service.dart'; // Added import for ApiService

class RegisterScreen extends StatefulWidget {
  const RegisterScreen({super.key});

  @override
  State<RegisterScreen> createState() => _RegisterScreenState();
}

class _RegisterScreenState extends State<RegisterScreen>
    with TickerProviderStateMixin {
  final _formKey = GlobalKey<FormState>();
  final _firstNameController = TextEditingController();
  final _lastNameController = TextEditingController();
  final _emailController = TextEditingController();
  final _passwordController = TextEditingController();
  final _confirmPasswordController = TextEditingController();
  
  late AnimationController _backgroundController;
  late AnimationController _formController;
  late AnimationController _buttonController;
  
  late Animation<double> _backgroundOpacity;
  late Animation<double> _formOpacity;
  late Animation<Offset> _formSlide;
  late Animation<double> _buttonOpacity;
  late Animation<double> _buttonScale;

  bool _isLoading = false;
  bool _obscurePassword = true;
  bool _obscureConfirmPassword = true;
  bool _acceptTerms = false;

  @override
  void initState() {
    super.initState();
    
    // Background animation
    _backgroundController = AnimationController(
      duration: const Duration(seconds: 2),
      vsync: this,
    );
    _backgroundOpacity = Tween<double>(
      begin: 0.0,
      end: 1.0,
    ).animate(CurvedAnimation(
      parent: _backgroundController,
      curve: AppTheme.futuristicCurve,
    ));
    
    // Form animation
    _formController = AnimationController(
      duration: const Duration(milliseconds: 1200),
      vsync: this,
    );
    _formOpacity = Tween<double>(
      begin: 0.0,
      end: 1.0,
    ).animate(CurvedAnimation(
      parent: _formController,
      curve: AppTheme.futuristicCurve,
    ));
    _formSlide = Tween<Offset>(
      begin: const Offset(0, 0.3),
      end: Offset.zero,
    ).animate(CurvedAnimation(
      parent: _formController,
      curve: AppTheme.futuristicCurve,
    ));
    
    // Button animation
    _buttonController = AnimationController(
      duration: const Duration(milliseconds: 800),
      vsync: this,
    );
    _buttonOpacity = Tween<double>(
      begin: 0.0,
      end: 1.0,
    ).animate(CurvedAnimation(
      parent: _buttonController,
      curve: AppTheme.futuristicCurve,
    ));
    _buttonScale = Tween<double>(
      begin: 0.8,
      end: 1.0,
    ).animate(CurvedAnimation(
      parent: _buttonController,
      curve: AppTheme.bounceCurve,
    ));
    
    // Start animations
    _startAnimations();
  }

  void _startAnimations() async {
    await Future.delayed(const Duration(milliseconds: 300));
    _backgroundController.forward();
    
    await Future.delayed(const Duration(milliseconds: 500));
    _formController.forward();
    
    await Future.delayed(const Duration(milliseconds: 400));
    _buttonController.forward();
  }

  @override
  void dispose() {
    _backgroundController.dispose();
    _formController.dispose();
    _buttonController.dispose();
    _firstNameController.dispose();
    _lastNameController.dispose();
    _emailController.dispose();
    _passwordController.dispose();
    _confirmPasswordController.dispose();
    super.dispose();
  }

  Future<void> _handleRegister() async {
    if (!_formKey.currentState!.validate()) return;
    if (!_acceptTerms) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('Please accept the terms and conditions'),
          backgroundColor: AppTheme.warningNeon,
        ),
      );
      return;
    }

    setState(() => _isLoading = true);
    
    try {
      // Create API service instance
      final apiService = ApiService();
      
      // Call registration API
      final result = await apiService.register(
        _emailController.text.trim(),
        _passwordController.text,
        '${_firstNameController.text.trim()} ${_lastNameController.text.trim()}',
      );
      
      if (mounted) {
        if (result.isSuccess) {
          // Registration successful
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(
              content: Text('Registration successful! Welcome ${result.data?.fullName}'),
              backgroundColor: AppTheme.successNeon,
            ),
          );
          
          // If user has a selected challenge, save it to backend
          final challengeProvider = Provider.of<ChallengeProvider>(context, listen: false);
          final selectedChallenge = challengeProvider.selectedChallenge;
          
          if (selectedChallenge != null) {
            try {
              // Login to get authentication token
              final loginResult = await apiService.login(
                _emailController.text.trim(),
                _passwordController.text,
              );
              
                             if (loginResult.isSuccess) {
                 // Update auth provider with login status
                 final authProvider = Provider.of<AuthProvider>(context, listen: false);
                 await authProvider.login(loginResult.data!['access_token'], loginResult.data!['user_id']);
                 
                 // Save challenge selection to backend
                 final challengeData = {
                   'challenge_id': selectedChallenge.challengeId,
                   'amount': selectedChallenge.amount,
                   'price': selectedChallenge.price,
                   'profit_target': selectedChallenge.profitTarget,
                   'max_drawdown': selectedChallenge.maxDrawdown,
                   'daily_limit': selectedChallenge.dailyLimit,
                   'category': selectedChallenge.category.name,
                 };
                 
                 final selectionResult = await apiService.createChallengeSelection(challengeData);
                 
                 if (selectionResult.isSuccess) {
                   ScaffoldMessenger.of(context).showSnackBar(
                     const SnackBar(
                       content: Text('Challenge selection saved successfully!'),
                       backgroundColor: AppTheme.successNeon,
                     ),
                   );
                   
                   // Clear the challenge selection from provider
                   challengeProvider.clearChallenge();
                 } else {
                   ScaffoldMessenger.of(context).showSnackBar(
                     SnackBar(
                       content: Text('Challenge saved but selection failed: ${selectionResult.error}'),
                       backgroundColor: AppTheme.warningNeon,
                     ),
                   );
                 }
               }
            } catch (e) {
              // Challenge saving failed, but registration was successful
              ScaffoldMessenger.of(context).showSnackBar(
                SnackBar(
                  content: Text('Registration successful! Challenge selection will be saved after login.'),
                  backgroundColor: AppTheme.successNeon,
                ),
              );
            }
          }
          
          // Navigate to demo dashboard to show all user data
          Navigator.pushReplacementNamed(context, '/');
        } else {
          // Registration failed
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(
              content: Text(result.error ?? 'Registration failed'),
              backgroundColor: AppTheme.warningNeon,
            ),
          );
        }
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('Error: $e'),
            backgroundColor: AppTheme.warningNeon,
          ),
        );
      }
    } finally {
      if (mounted) {
        setState(() => _isLoading = false);
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final screenSize = MediaQuery.of(context).size;
    final isMobile = screenSize.width < 600;
    final isTablet = screenSize.width >= 600 && screenSize.width < 1200;
    
    return Scaffold(
      body: Container(
        decoration: const BoxDecoration(
          gradient: AppTheme.backgroundGradient,
        ),
        child: Stack(
          children: [
            // Animated background
            _buildAnimatedBackground(),
            
            // Main content
            SafeArea(
              child: Center(
                child: SingleChildScrollView(
                  padding: EdgeInsets.all(isMobile ? 16 : isTablet ? 24 : 32),
                  child: ConstrainedBox(
                    constraints: BoxConstraints(
                      maxWidth: isMobile ? double.infinity : isTablet ? 600 : 700,
                    ),
                    child: Column(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        // ORBIT Logo
                        _buildOrbitLogo(),
                        
                        SizedBox(height: isMobile ? 24 : 40),
                        
                        // Registration Form
                        _buildRegistrationForm(),
                        
                        SizedBox(height: isMobile ? 24 : 40),
                        
                        // Social Registration
                        _buildSocialRegistration(),
                        
                        SizedBox(height: isMobile ? 24 : 40),
                        
                        // Login Link
                        _buildLoginLink(),
                      ],
                    ),
                  ),
                ),
              ),
            ),
            
            // Back button
            Positioned(
              top: isMobile ? 20 : 40,
              left: isMobile ? 16 : 24,
              child: _buildBackButton(),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildAnimatedBackground() {
    return FadeTransition(
      opacity: _backgroundOpacity,
      child: CustomPaint(
        painter: RegisterBackgroundPainter(),
        size: Size.infinite,
      ),
    );
  }

  Widget _buildOrbitLogo() {
    return Container(
      width: 80,
      height: 80,
      decoration: BoxDecoration(
        shape: BoxShape.circle,
        gradient: const LinearGradient(
          colors: [AppTheme.secondaryNeon, AppTheme.accentNeon],
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
        ),
        boxShadow: [
          BoxShadow(
            color: AppTheme.secondaryNeon.withOpacity(0.4),
            blurRadius: 20,
            spreadRadius: 2,
          ),
        ],
      ),
      child: const Center(
        child: Text(
          'ORBIT',
          style: TextStyle(
            color: Colors.black,
            fontSize: 16,
            fontWeight: FontWeight.bold,
            letterSpacing: 2,
          ),
        ),
      ),
    );
  }

  Widget _buildRegistrationForm() {
    return FadeTransition(
      opacity: _formOpacity,
      child: SlideTransition(
        position: _formSlide,
        child: Container(
          constraints: const BoxConstraints(maxWidth: 450),
          child: Card(
            child: Container(
              padding: const EdgeInsets.all(32),
              decoration: BoxDecoration(
                borderRadius: BorderRadius.circular(20),
                gradient: LinearGradient(
                  colors: [
                    AppTheme.cardBackground,
                    AppTheme.surfaceBackground,
                  ],
                  begin: Alignment.topLeft,
                  end: Alignment.bottomRight,
                ),
                border: Border.all(
                  color: AppTheme.secondaryNeon.withOpacity(0.3),
                  width: 1,
                ),
              ),
              child: Consumer<ChallengeProvider>(
                builder: (context, challengeProvider, child) {
                  return Form(
                    key: _formKey,
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.stretch,
                      children: [
                        // Title
                        const Text(
                          'JOIN ORBIT',
                          textAlign: TextAlign.center,
                          style: TextStyle(
                            fontSize: 28,
                            fontWeight: FontWeight.bold,
                            color: AppTheme.secondaryNeon,
                            letterSpacing: 3,
                          ),
                        ),
                        
                        const SizedBox(height: 8),
                        
                        const Text(
                          'Begin your trading journey',
                          textAlign: TextAlign.center,
                          style: TextStyle(
                            fontSize: 16,
                            color: AppTheme.textSecondary,
                          ),
                        ),
                        
                        const SizedBox(height: 24),
                        
                        // Challenge Selection Banner
                        _buildChallengeSelectionBanner(),
                        
                        const SizedBox(height: 24),
                        
                        // Name fields
                        Row(
                          children: [
                            Expanded(child: _buildFirstNameField()),
                            const SizedBox(width: 16),
                            Expanded(child: _buildLastNameField()),
                          ],
                        ),
                        
                        const SizedBox(height: 24),
                        
                        // Email field
                        _buildEmailField(),
                        
                        const SizedBox(height: 24),
                        
                        // Password fields
                        Row(
                          children: [
                            Expanded(child: _buildPasswordField()),
                            const SizedBox(width: 16),
                            Expanded(child: _buildConfirmPasswordField()),
                          ],
                        ),
                        
                        const SizedBox(height: 24),
                        
                        // Terms and conditions
                        _buildTermsCheckbox(),
                        
                        const SizedBox(height: 32),
                        
                        // Register button
                        _buildRegisterButton(),
                      ],
                    ),
                  );
                },
              ),
            ),
          ),
        ),
      ),
    );
  }

  Widget _buildFirstNameField() {
    return TextFormField(
      controller: _firstNameController,
      style: const TextStyle(color: AppTheme.textPrimary),
      decoration: InputDecoration(
        labelText: 'FIRST NAME',
        prefixIcon: Icon(
          Icons.person_outline,
          color: AppTheme.secondaryNeon.withOpacity(0.7),
        ),
        border: OutlineInputBorder(
          borderRadius: BorderRadius.circular(12),
          borderSide: BorderSide(color: AppTheme.secondaryNeon.withOpacity(0.3)),
        ),
        enabledBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(12),
          borderSide: BorderSide(color: AppTheme.secondaryNeon.withOpacity(0.3)),
        ),
        focusedBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(12),
          borderSide: BorderSide(color: AppTheme.secondaryNeon, width: 2),
        ),
        labelStyle: const TextStyle(color: AppTheme.textSecondary),
        filled: true,
        fillColor: AppTheme.darkerBackground,
      ),
      validator: (value) {
        if (value == null || value.isEmpty) {
          return 'First name is required';
        }
        return null;
      },
    );
  }

  Widget _buildLastNameField() {
    return TextFormField(
      controller: _lastNameController,
      style: const TextStyle(color: AppTheme.textPrimary),
      decoration: InputDecoration(
        labelText: 'LAST NAME',
        prefixIcon: Icon(
          Icons.person_outline,
          color: AppTheme.secondaryNeon.withOpacity(0.7),
        ),
        border: OutlineInputBorder(
          borderRadius: BorderRadius.circular(12),
          borderSide: BorderSide(color: AppTheme.secondaryNeon.withOpacity(0.3)),
        ),
        enabledBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(12),
          borderSide: BorderSide(color: AppTheme.secondaryNeon.withOpacity(0.3)),
        ),
        focusedBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(12),
          borderSide: BorderSide(color: AppTheme.secondaryNeon, width: 2),
        ),
        labelStyle: const TextStyle(color: AppTheme.textSecondary),
        filled: true,
        fillColor: AppTheme.darkerBackground,
      ),
      validator: (value) {
        if (value == null || value.isEmpty) {
          return 'Last name is required';
        }
        return null;
      },
    );
  }

  Widget _buildEmailField() {
    return TextFormField(
      controller: _emailController,
      keyboardType: TextInputType.emailAddress,
      style: const TextStyle(color: AppTheme.textPrimary),
      decoration: InputDecoration(
        labelText: 'EMAIL',
        prefixIcon: Icon(
          Icons.email_outlined,
          color: AppTheme.secondaryNeon.withOpacity(0.7),
        ),
        border: OutlineInputBorder(
          borderRadius: BorderRadius.circular(12),
          borderSide: BorderSide(color: AppTheme.secondaryNeon.withOpacity(0.3)),
        ),
        enabledBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(12),
          borderSide: BorderSide(color: AppTheme.secondaryNeon.withOpacity(0.3)),
        ),
        focusedBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(12),
          borderSide: BorderSide(color: AppTheme.secondaryNeon, width: 2),
        ),
        labelStyle: const TextStyle(color: AppTheme.textSecondary),
        filled: true,
        fillColor: AppTheme.darkerBackground,
      ),
      validator: (value) {
        if (value == null || value.isEmpty) {
          return 'Email is required';
        }
        if (!RegExp(r'^[\w-\.]+@([\w-]+\.)+[\w-]{2,4}$').hasMatch(value)) {
          return 'Please enter a valid email';
        }
        return null;
      },
    );
  }

  Widget _buildPasswordField() {
    return TextFormField(
      controller: _passwordController,
      obscureText: _obscurePassword,
      style: const TextStyle(color: AppTheme.textPrimary),
      decoration: InputDecoration(
        labelText: 'PASSWORD',
        prefixIcon: Icon(
          Icons.lock_outlined,
          color: AppTheme.secondaryNeon.withOpacity(0.7),
        ),
        suffixIcon: IconButton(
          icon: Icon(
            _obscurePassword ? Icons.visibility : Icons.visibility_off,
            color: AppTheme.secondaryNeon.withOpacity(0.7),
          ),
          onPressed: () {
            setState(() {
              _obscurePassword = !_obscurePassword;
            });
          },
        ),
        border: OutlineInputBorder(
          borderRadius: BorderRadius.circular(12),
          borderSide: BorderSide(color: AppTheme.secondaryNeon.withOpacity(0.3)),
        ),
        enabledBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(12),
          borderSide: BorderSide(color: AppTheme.secondaryNeon.withOpacity(0.3)),
        ),
        focusedBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(12),
          borderSide: BorderSide(color: AppTheme.secondaryNeon, width: 2),
        ),
        labelStyle: const TextStyle(color: AppTheme.textSecondary),
        filled: true,
        fillColor: AppTheme.darkerBackground,
      ),
      validator: (value) {
        if (value == null || value.isEmpty) {
          return 'Password is required';
        }
        if (value.length < 8) {
          return 'Password must be at least 8 characters';
        }
        if (!RegExp(r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)').hasMatch(value)) {
          return 'Password must contain uppercase, lowercase & number';
        }
        return null;
      },
    );
  }

  Widget _buildConfirmPasswordField() {
    return TextFormField(
      controller: _confirmPasswordController,
      obscureText: _obscureConfirmPassword,
      style: const TextStyle(color: AppTheme.textPrimary),
      decoration: InputDecoration(
        labelText: 'CONFIRM PASSWORD',
        prefixIcon: Icon(
          Icons.lock_outlined,
          color: AppTheme.secondaryNeon.withOpacity(0.7),
        ),
        suffixIcon: IconButton(
          icon: Icon(
            _obscureConfirmPassword ? Icons.visibility : Icons.visibility_off,
            color: AppTheme.secondaryNeon.withOpacity(0.7),
          ),
          onPressed: () {
            setState(() {
              _obscureConfirmPassword = !_obscureConfirmPassword;
            });
          },
        ),
        border: OutlineInputBorder(
          borderRadius: BorderRadius.circular(12),
          borderSide: BorderSide(color: AppTheme.secondaryNeon.withOpacity(0.3)),
        ),
        enabledBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(12),
          borderSide: BorderSide(color: AppTheme.secondaryNeon.withOpacity(0.3)),
        ),
        focusedBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(12),
          borderSide: BorderSide(color: AppTheme.secondaryNeon, width: 2),
        ),
        labelStyle: const TextStyle(color: AppTheme.textSecondary),
        filled: true,
        fillColor: AppTheme.darkerBackground,
      ),
      validator: (value) {
        if (value == null || value.isEmpty) {
          return 'Please confirm your password';
        }
        if (value != _passwordController.text) {
          return 'Passwords do not match';
        }
        return null;
      },
    );
  }

  Widget _buildTermsCheckbox() {
    return Row(
      children: [
        Checkbox(
          value: _acceptTerms,
          onChanged: (value) {
            setState(() {
              _acceptTerms = value ?? false;
            });
          },
          activeColor: AppTheme.secondaryNeon,
          checkColor: Colors.black,
        ),
        Expanded(
          child: GestureDetector(
            onTap: () {
              setState(() {
                _acceptTerms = !_acceptTerms;
              });
            },
            child: RichText(
              text: const TextSpan(
                text: 'I agree to the ',
                style: TextStyle(
                  color: AppTheme.textSecondary,
                  fontSize: 14,
                ),
                children: [
                  TextSpan(
                    text: 'Terms of Service',
                    style: TextStyle(
                      color: AppTheme.secondaryNeon,
                      decoration: TextDecoration.underline,
                    ),
                  ),
                  TextSpan(text: ' and '),
                  TextSpan(
                    text: 'Privacy Policy',
                    style: TextStyle(
                      color: AppTheme.secondaryNeon,
                      decoration: TextDecoration.underline,
                    ),
                  ),
                ],
              ),
            ),
          ),
        ),
      ],
    );
  }

  Widget _buildRegisterButton() {
    return FadeTransition(
      opacity: _buttonOpacity,
      child: ScaleTransition(
        scale: _buttonScale,
        child: FuturisticButton(
          text: 'JOIN ORBIT',
          onPressed: _isLoading ? null : _handleRegister,
          isLoading: _isLoading,
          color: AppTheme.secondaryNeon,
        ),
      ),
    );
  }

  Widget _buildSocialRegistration() {
    return FadeTransition(
      opacity: _formOpacity,
      child: SlideTransition(
        position: _formSlide,
        child: Column(
          children: [
            const Text(
              'Or join with',
              style: TextStyle(
                color: AppTheme.textSecondary,
                fontSize: 14,
              ),
            ),
            
            const SizedBox(height: 20),
            
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceEvenly,
              children: [
                _buildSocialButton(
                  icon: Icons.g_mobiledata,
                  label: 'Google',
                  onPressed: () {},
                ),
                _buildSocialButton(
                  icon: Icons.facebook,
                  label: 'Facebook',
                  onPressed: () {},
                ),
                _buildSocialButton(
                  icon: Icons.apple,
                  label: 'Apple',
                  onPressed: () {},
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildSocialButton({
    required IconData icon,
    required String label,
    required VoidCallback onPressed,
  }) {
    return GestureDetector(
      onTap: onPressed,
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 12),
        decoration: BoxDecoration(
          color: AppTheme.surfaceBackground,
          borderRadius: BorderRadius.circular(12),
          border: Border.all(
            color: AppTheme.secondaryNeon.withOpacity(0.3),
            width: 1,
          ),
        ),
        child: Column(
          children: [
            Icon(
              icon,
              color: AppTheme.secondaryNeon,
              size: 24,
            ),
            const SizedBox(height: 4),
            Text(
              label,
              style: const TextStyle(
                color: AppTheme.textSecondary,
                fontSize: 12,
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildLoginLink() {
    return FadeTransition(
      opacity: _formOpacity,
      child: SlideTransition(
        position: _formSlide,
        child: Row(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            const Text(
              'Already have an account? ',
              style: TextStyle(
                color: AppTheme.textSecondary,
                fontSize: 14,
              ),
            ),
            TextButton(
              onPressed: () => Navigator.pushNamed(context, '/login'),
              child: const Text(
                'Launch into ORBIT',
                style: TextStyle(
                  color: AppTheme.primaryNeon,
                  fontSize: 14,
                  fontWeight: FontWeight.bold,
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildBackButton() {
    return Container(
      decoration: BoxDecoration(
        color: AppTheme.cardBackground.withOpacity(0.8),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(
          color: AppTheme.secondaryNeon.withOpacity(0.3),
          width: 1,
        ),
      ),
      child: IconButton(
        icon: const Icon(
          Icons.arrow_back,
          color: AppTheme.secondaryNeon,
        ),
        onPressed: () => Navigator.pop(context),
      ),
    );
  }

  Widget _buildChallengeSelectionBanner() {
    return Consumer<ChallengeProvider>(
      builder: (context, challengeProvider, child) {
        final selectedChallenge = challengeProvider.selectedChallenge;
        
        // Debug logging
        debugPrint('Registration Screen: Building challenge banner');
        debugPrint('Registration Screen: Selected challenge: ${selectedChallenge?.toJson()}');
        
        if (selectedChallenge != null) {
          // Show selected challenge details
          return Container(
            padding: const EdgeInsets.all(16),
            decoration: BoxDecoration(
              color: AppTheme.secondaryNeon.withOpacity(0.1),
              borderRadius: BorderRadius.circular(12),
              border: Border.all(
                color: AppTheme.secondaryNeon.withOpacity(0.5),
                width: 2,
              ),
            ),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  children: [
                    Icon(
                      Icons.check_circle,
                      color: AppTheme.secondaryNeon,
                      size: 24,
                    ),
                    const SizedBox(width: 12),
                    Expanded(
                      child: Text(
                        'Selected Challenge: ${selectedChallenge.amount}',
                        style: const TextStyle(
                          color: AppTheme.secondaryNeon,
                          fontSize: 16,
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                    ),
                    IconButton(
                      icon: Icon(
                        Icons.close,
                        color: AppTheme.secondaryNeon,
                        size: 20,
                      ),
                      onPressed: () {
                        challengeProvider.clearChallenge();
                      },
                    ),
                  ],
                ),
                const SizedBox(height: 12),
                Text(
                  'Price: ${selectedChallenge.price}',
                  style: const TextStyle(
                    color: AppTheme.textSecondary,
                    fontSize: 14,
                  ),
                ),
                const SizedBox(height: 8),
                Text(
                  'Profit Target: ${selectedChallenge.profitTarget} | Daily Limit: ${selectedChallenge.dailyLimit}',
                  style: const TextStyle(
                    color: AppTheme.textSecondary,
                    fontSize: 12,
                  ),
                ),
              ],
            ),
          );
        } else {
          // Show prompt to select challenge
          return Container(
            padding: const EdgeInsets.all(16),
            decoration: BoxDecoration(
              color: AppTheme.surfaceBackground,
              borderRadius: BorderRadius.circular(12),
              border: Border.all(
                color: AppTheme.secondaryNeon.withOpacity(0.3),
                width: 1,
              ),
            ),
            child: Row(
              children: [
                Icon(
                  Icons.lightbulb_outline,
                  color: AppTheme.secondaryNeon,
                  size: 24,
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: Text(
                    'Select a challenge to start your trading journey. Each challenge offers unique opportunities and rewards.',
                    style: TextStyle(
                      color: AppTheme.textSecondary,
                      fontSize: 14,
                    ),
                  ),
                ),
                IconButton(
                  icon: Icon(
                    Icons.arrow_forward_ios,
                    color: AppTheme.secondaryNeon,
                    size: 16,
                  ),
                  onPressed: () {
                    Navigator.pushNamed(context, '/funded-challenges');
                  },
                ),
              ],
            ),
          );
        }
      },
    );
  }
}

// Custom painter for register background
class RegisterBackgroundPainter extends CustomPainter {
  @override
  void paint(Canvas canvas, Size size) {
    final paint = Paint()
      ..color = AppTheme.secondaryNeon.withOpacity(0.05)
      ..style = PaintingStyle.fill;

    // Draw constellation pattern
    final points = [
      Offset(100, 100),
      Offset(300, 150),
      Offset(500, 100),
      Offset(200, 300),
      Offset(400, 350),
      Offset(150, 500),
      Offset(350, 450),
    ];

    for (final point in points) {
      canvas.drawCircle(point, 3, paint);
    }

    // Draw connecting lines
    final linePaint = Paint()
      ..color = AppTheme.secondaryNeon.withOpacity(0.03)
      ..strokeWidth = 1;

    for (int i = 0; i < points.length - 1; i++) {
      canvas.drawLine(points[i], points[i + 1], linePaint);
    }

    // Draw grid
    for (int i = 0; i < size.width; i += 80) {
      canvas.drawLine(
        Offset(i.toDouble(), 0),
        Offset(i.toDouble(), size.height),
        linePaint,
      );
    }

    for (int i = 0; i < size.height; i += 80) {
      canvas.drawLine(
        Offset(0, i.toDouble()),
        Offset(size.width, i.toDouble()),
        linePaint,
      );
    }
  }

  @override
  bool shouldRepaint(covariant CustomPainter oldDelegate) => false;
}
