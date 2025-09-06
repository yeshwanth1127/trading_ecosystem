import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../../utils/theme.dart';
import '../../providers/auth_provider.dart';
import '../../services/api_service.dart';

class LoginScreen extends StatefulWidget {
  const LoginScreen({super.key});

  @override
  State<LoginScreen> createState() => _LoginScreenState();
}

class _LoginScreenState extends State<LoginScreen>
    with TickerProviderStateMixin {
  final _formKey = GlobalKey<FormState>();
  final _emailController = TextEditingController();
  final _passwordController = TextEditingController();
  
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
    _emailController.dispose();
    _passwordController.dispose();
    super.dispose();
  }

  Future<void> _handleLogin() async {
    if (!_formKey.currentState!.validate()) return;

    setState(() => _isLoading = true);
    
    try {
      final apiService = ApiService();
      final result = await apiService.login(
        _emailController.text.trim(),
        _passwordController.text,
      );
      
      if (mounted) {
        if (result.isSuccess) {
          // Update auth provider
          final authProvider = Provider.of<AuthProvider>(context, listen: false);
          await authProvider.login(
            result.data!['access_token'],
            result.data!['user_id'],
          );
          
          // Navigate to demo dashboard
          Navigator.pushReplacementNamed(context, '/dashboard');
        } else {
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(
              content: Text(result.error ?? 'Login failed'),
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
                      maxWidth: isMobile ? double.infinity : isTablet ? 500 : 600,
                    ),
                    child: Column(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        // ORBIT Logo
                        _buildOrbitLogo(),
                        
                        SizedBox(height: isMobile ? 24 : 40),
                        
                        // Login Form
                        _buildLoginForm(),
                        
                        SizedBox(height: isMobile ? 24 : 40),
                        
                        // Social Login
                        _buildSocialLogin(),
                        
                        SizedBox(height: isMobile ? 24 : 40),
                        
                        // Register Link
                        _buildRegisterLink(),
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
        painter: LoginBackgroundPainter(),
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
          colors: [AppTheme.primaryNeon, AppTheme.secondaryNeon],
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
        ),
        boxShadow: [
          BoxShadow(
            color: AppTheme.primaryNeon.withOpacity(0.4),
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

  Widget _buildLoginForm() {
    return FadeTransition(
      opacity: _formOpacity,
      child: SlideTransition(
        position: _formSlide,
        child: Container(
          constraints: const BoxConstraints(maxWidth: 400),
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
                  color: AppTheme.primaryNeon.withOpacity(0.3),
                  width: 1,
                ),
              ),
              child: Form(
                key: _formKey,
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.stretch,
                  children: [
                    // Title
                    const Text(
                      'LAUNCH INTO ORBIT',
                      textAlign: TextAlign.center,
                      style: TextStyle(
                        fontSize: 28,
                        fontWeight: FontWeight.bold,
                        color: AppTheme.primaryNeon,
                        letterSpacing: 3,
                      ),
                    ),
                    
                    const SizedBox(height: 8),
                    
                    const Text(
                      'Access your trading dashboard',
                      textAlign: TextAlign.center,
                      style: TextStyle(
                        fontSize: 16,
                        color: AppTheme.textSecondary,
                      ),
                    ),
                    
                    const SizedBox(height: 32),
                    
                    // Email field
                    _buildEmailField(),
                    
                    const SizedBox(height: 24),
                    
                    // Password field
                    _buildPasswordField(),
                    
                    const SizedBox(height: 16),
                    
                    // Forgot password
                    _buildForgotPassword(),
                    
                    const SizedBox(height: 32),
                    
                    // Login button
                    _buildLoginButton(),
                  ],
                ),
              ),
            ),
          ),
        ),
      ),
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
          color: AppTheme.primaryNeon.withOpacity(0.7),
        ),
        border: OutlineInputBorder(
          borderRadius: BorderRadius.circular(12),
          borderSide: BorderSide(color: AppTheme.primaryNeon.withOpacity(0.3)),
        ),
        enabledBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(12),
          borderSide: BorderSide(color: AppTheme.primaryNeon.withOpacity(0.3)),
        ),
        focusedBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(12),
          borderSide: BorderSide(color: AppTheme.primaryNeon, width: 2),
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
          color: AppTheme.primaryNeon.withOpacity(0.7),
        ),
        suffixIcon: IconButton(
          icon: Icon(
            _obscurePassword ? Icons.visibility : Icons.visibility_off,
            color: AppTheme.primaryNeon.withOpacity(0.7),
          ),
          onPressed: () {
            setState(() {
              _obscurePassword = !_obscurePassword;
            });
          },
        ),
        border: OutlineInputBorder(
          borderRadius: BorderRadius.circular(12),
          borderSide: BorderSide(color: AppTheme.primaryNeon.withOpacity(0.3)),
        ),
        enabledBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(12),
          borderSide: BorderSide(color: AppTheme.primaryNeon.withOpacity(0.3)),
        ),
        focusedBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(12),
          borderSide: BorderSide(color: AppTheme.primaryNeon, width: 2),
        ),
        labelStyle: const TextStyle(color: AppTheme.textSecondary),
        filled: true,
        fillColor: AppTheme.darkerBackground,
      ),
      validator: (value) {
        if (value == null || value.isEmpty) {
          return 'Password is required';
        }
        if (value.length < 6) {
          return 'Password must be at least 6 characters';
        }
        return null;
      },
    );
  }

  Widget _buildForgotPassword() {
    return Align(
      alignment: Alignment.centerRight,
      child: TextButton(
        onPressed: () {},
        child: const Text(
          'Forgot Password?',
          style: TextStyle(
            color: AppTheme.primaryNeon,
            fontSize: 14,
          ),
        ),
      ),
    );
  }

  Widget _buildLoginButton() {
    return FadeTransition(
      opacity: _buttonOpacity,
      child: ScaleTransition(
        scale: _buttonScale,
        child: FuturisticButton(
          text: 'LAUNCH',
          onPressed: _isLoading ? null : _handleLogin,
          isLoading: _isLoading,
          color: AppTheme.primaryNeon,
        ),
      ),
    );
  }

  Widget _buildSocialLogin() {
    return FadeTransition(
      opacity: _formOpacity,
      child: SlideTransition(
        position: _formSlide,
        child: Column(
          children: [
            const Text(
              'Or continue with',
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
            color: AppTheme.primaryNeon.withOpacity(0.3),
            width: 1,
          ),
        ),
        child: Column(
          children: [
            Icon(
              icon,
              color: AppTheme.primaryNeon,
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

  Widget _buildRegisterLink() {
    return FadeTransition(
      opacity: _formOpacity,
      child: SlideTransition(
        position: _formSlide,
        child: Row(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            const Text(
              "Don't have an account? ",
              style: TextStyle(
                color: AppTheme.textSecondary,
                fontSize: 14,
              ),
            ),
            TextButton(
              onPressed: () => Navigator.pushNamed(context, '/register'),
              child: const Text(
                'Join ORBIT',
                style: TextStyle(
                  color: AppTheme.secondaryNeon,
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
          color: AppTheme.primaryNeon.withOpacity(0.3),
          width: 1,
        ),
      ),
      child: IconButton(
        icon: const Icon(
          Icons.arrow_back,
          color: AppTheme.primaryNeon,
        ),
        onPressed: () => Navigator.pop(context),
      ),
    );
  }
}

// Custom painter for login background
class LoginBackgroundPainter extends CustomPainter {
  @override
  void paint(Canvas canvas, Size size) {
    final paint = Paint()
      ..color = AppTheme.primaryNeon.withOpacity(0.05)
      ..style = PaintingStyle.fill;

    // Draw orbital rings
    final center = Offset(size.width / 2, size.height / 2);
    
    for (int i = 1; i <= 3; i++) {
      final radius = 100.0 * i;
      canvas.drawCircle(center, radius, paint);
    }

    // Draw connecting lines
    final linePaint = Paint()
      ..color = AppTheme.primaryNeon.withOpacity(0.03)
      ..strokeWidth = 1;

    for (int i = 0; i < size.width; i += 100) {
      canvas.drawLine(
        Offset(i.toDouble(), 0),
        Offset(i.toDouble(), size.height),
        linePaint,
      );
    }

    for (int i = 0; i < size.height; i += 100) {
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
