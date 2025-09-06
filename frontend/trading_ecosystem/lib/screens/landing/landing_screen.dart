import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../../utils/theme.dart';
import '../../providers/challenge_provider.dart';
import '../../providers/auth_provider.dart';

class LandingScreen extends StatefulWidget {
  const LandingScreen({super.key});

  @override
  State<LandingScreen> createState() => _LandingScreenState();
}

class _LandingScreenState extends State<LandingScreen>
    with TickerProviderStateMixin {
  late AnimationController _backgroundController;
  late AnimationController _headerController;
  late AnimationController _heroController;
  late AnimationController _featuresController;
  
  late Animation<double> _backgroundOpacity;
  late Animation<double> _headerOpacity;
  late Animation<Offset> _headerSlide;
  late Animation<double> _heroOpacity;
  late Animation<Offset> _heroSlide;
  late Animation<double> _featuresOpacity;
  late Animation<Offset> _featuresSlide;

  String _displayText = '';
  String _fullText = 'ORBIT';
  int _currentIndex = 0;
  bool _isDeleting = false;

  @override
  void initState() {
    super.initState();
    
    // Background animation
    _backgroundController = AnimationController(
      duration: const Duration(seconds: 3),
      vsync: this,
    );
    _backgroundOpacity = Tween<double>(
      begin: 0.0,
      end: 1.0,
    ).animate(CurvedAnimation(
      parent: _backgroundController,
      curve: AppTheme.futuristicCurve,
    ));
    
    // Header animation
    _headerController = AnimationController(
      duration: const Duration(milliseconds: 800),
      vsync: this,
    );
    _headerOpacity = Tween<double>(
      begin: 0.0,
      end: 1.0,
    ).animate(CurvedAnimation(
      parent: _headerController,
      curve: AppTheme.futuristicCurve,
    ));
    _headerSlide = Tween<Offset>(
      begin: const Offset(-0.5, 0),
      end: Offset.zero,
    ).animate(CurvedAnimation(
      parent: _headerController,
      curve: AppTheme.futuristicCurve,
    ));
    
    // Hero animation
    _heroController = AnimationController(
      duration: const Duration(milliseconds: 1200),
      vsync: this,
    );
    _heroOpacity = Tween<double>(
      begin: 0.0,
      end: 1.0,
    ).animate(CurvedAnimation(
      parent: _heroController,
      curve: AppTheme.futuristicCurve,
    ));
    _heroSlide = Tween<Offset>(
      begin: const Offset(0, 0.5),
      end: Offset.zero,
    ).animate(CurvedAnimation(
      parent: _heroController,
      curve: AppTheme.futuristicCurve,
    ));
    
    // Features animation
    _featuresController = AnimationController(
      duration: const Duration(milliseconds: 1500),
      vsync: this,
    );
    _featuresOpacity = Tween<double>(
      begin: 0.0,
      end: 1.0,
    ).animate(CurvedAnimation(
      parent: _featuresController,
      curve: AppTheme.futuristicCurve,
    ));
    _featuresSlide = Tween<Offset>(
      begin: const Offset(0, 0.3),
      end: Offset.zero,
    ).animate(CurvedAnimation(
      parent: _featuresController,
      curve: AppTheme.futuristicCurve,
    ));
    
    // Button animation
    // _buttonController = AnimationController(
    //   duration: const Duration(milliseconds: 1000),
    //   vsync: this,
    // );
    // _buttonOpacity = Tween<double>(
    //   begin: 0.0,
    //   end: 1.0,
    // ).animate(CurvedAnimation(
    //   parent: _buttonController,
    //   curve: AppTheme.futuristicCurve,
    // ));
    // _buttonSlide = Tween<Offset>(
    //   begin: const Offset(0, 0.3),
    //   end: Offset.zero,
    // ).animate(CurvedAnimation(
    //   parent: _buttonController,
    //   curve: AppTheme.futuristicCurve,
    // ));
    
    // Typewriter animation
    // _typewriterController = AnimationController(
    //   duration: const Duration(milliseconds: 2000),
    //   vsync: this,
    // );
    
    // Start animations
    _startAnimations();
    _startTypewriter();
  }

  void _startAnimations() async {
    await Future.delayed(const Duration(milliseconds: 300));
    _backgroundController.forward();
    
    await Future.delayed(const Duration(milliseconds: 500));
    _headerController.forward();
    
    await Future.delayed(const Duration(milliseconds: 400));
    _heroController.forward();
    
    await Future.delayed(const Duration(milliseconds: 600));
    _featuresController.forward();
    
    await Future.delayed(const Duration(milliseconds: 400));
    // _buttonController.forward();
  }

  void _startTypewriter() {
    Future.delayed(const Duration(milliseconds: 1000), () {
      _typewriterLoop();
    });
  }

  void _typewriterLoop() {
    if (!mounted) return;
    
    if (!_isDeleting) {
      if (_currentIndex < _fullText.length) {
        setState(() {
          _displayText = _fullText.substring(0, _currentIndex + 1);
          _currentIndex++;
        });
        Future.delayed(const Duration(milliseconds: 200), _typewriterLoop);
      } else {
        Future.delayed(const Duration(milliseconds: 1000), () {
          setState(() {
            _isDeleting = true;
          });
          _typewriterLoop();
        });
      }
    } else {
      if (_currentIndex > 0) {
        setState(() {
          _displayText = _fullText.substring(0, _currentIndex);
          _currentIndex--;
        });
        Future.delayed(const Duration(milliseconds: 100), _typewriterLoop);
      } else {
        Future.delayed(const Duration(milliseconds: 500), () {
          setState(() {
            _isDeleting = false;
          });
          _typewriterLoop();
        });
      }
    }
  }

  @override
  void dispose() {
    _backgroundController.dispose();
    _headerController.dispose();
    _heroController.dispose();
    _featuresController.dispose();
    // _buttonController.dispose();
    // _typewriterController.dispose();
    super.dispose();
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
            FadeTransition(
              opacity: _backgroundOpacity,
              child: _buildAnimatedBackground(),
            ),
            
            // Main content
            SafeArea(
              child: SingleChildScrollView(
                padding: EdgeInsets.symmetric(
                  horizontal: isMobile ? 16 : isTablet ? 32 : 64,
                  vertical: 24,
                ),
                child: Column(
                  children: [
                    // Header
                    SlideTransition(
                      position: _headerSlide,
                      child: FadeTransition(
                        opacity: _headerOpacity,
                        child: _buildHeader(isMobile, isTablet),
                      ),
                    ),
                    
                    SizedBox(height: isMobile ? 32 : 48),
                    
                    // Hero section
                    SlideTransition(
                      position: _heroSlide,
                      child: FadeTransition(
                        opacity: _heroOpacity,
                        child: _buildHeroSection(isMobile, isTablet),
                      ),
                    ),
                    
                    SizedBox(height: isMobile ? 40 : 60),
                    
                    // Features section
                    SlideTransition(
                      position: _featuresSlide,
                      child: FadeTransition(
                        opacity: _featuresOpacity,
                        child: _buildFeaturesSection(isMobile, isTablet),
                      ),
                    ),
                    
                    SizedBox(height: isMobile ? 40 : 60),
                    
                    // Action buttons
                    _buildActionButtons(isMobile, isTablet),
                  ],
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildAnimatedBackground() {
    return CustomPaint(
      painter: SimpleBackgroundPainter(),
      size: Size.infinite,
    );
  }

  Widget _buildHeader(bool isMobile, bool isTablet) {
    return Padding(
      padding: const EdgeInsets.all(24),
      child: Row(
        children: [
          // ORBIT Logo with typewriter effect
          Text(
            _displayText,
            style: const TextStyle(
              fontSize: 32,
              fontWeight: FontWeight.bold,
              color: AppTheme.primaryNeon,
              letterSpacing: 4,
              shadows: [
                Shadow(
                  color: AppTheme.primaryNeon,
                  blurRadius: 15,
                ),
              ],
            ),
          ),
          
          const Spacer(),
          
          // JOIN ORBIT button
          FuturisticButton(
            text: 'JOIN ORBIT',
            onPressed: () => Navigator.pushNamed(context, '/services'),
            color: AppTheme.secondaryNeon,
          ),
          
          const SizedBox(width: 20),
          
          // REGISTER button
          FuturisticButton(
            text: 'REGISTER',
            onPressed: () {
              // Clear any existing challenge selection for fresh registration
              Provider.of<ChallengeProvider>(context, listen: false).clearForNewRegistration();
              Navigator.pushNamed(context, '/register');
            },
            color: AppTheme.accentNeon,
          ),
          
          const SizedBox(width: 20),
          
          // LAUNCH button
          FuturisticButton(
            text: 'LAUNCH',
            onPressed: () => Navigator.pushNamed(context, '/login'),
            color: AppTheme.primaryNeon,
          ),
          
          // DEMO DASHBOARD button - only show when logged in
          Consumer<AuthProvider>(
            builder: (context, authProvider, child) {
              if (authProvider.isLoggedIn) {
                return Row(
                  children: [
                    const SizedBox(width: 20),
                    FuturisticButton(
                      text: 'DEMO DASHBOARD',
                      onPressed: () => Navigator.pushNamed(context, '/'),
                      color: AppTheme.warningNeon,
                    ),
                  ],
                );
              }
              return const SizedBox.shrink();
            },
          ),
        ],
      ),
    );
  }

  Widget _buildHeroSection(bool isMobile, bool isTablet) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 40),
      child: Column(
        children: [
          const Text(
            'MASTER THE MARKETS WITH\nPROFESSIONAL TRADING TOOLS',
            textAlign: TextAlign.center,
            style: TextStyle(
              fontSize: 48,
              fontWeight: FontWeight.bold,
              color: AppTheme.textPrimary,
              height: 1.2,
              letterSpacing: 2,
            ),
          ),
          const SizedBox(height: 24),
          const Text(
            'Join thousands of traders using our advanced platform for funded challenges, copy trading, and algorithmic strategies.',
            textAlign: TextAlign.center,
            style: TextStyle(
              fontSize: 20,
              color: AppTheme.textSecondary,
              height: 1.5,
            ),
          ),
          
          const SizedBox(height: 40),
          
          // Hero Register Button
          FuturisticButton(
            text: 'START YOUR JOURNEY',
            onPressed: () {
              // Clear any existing challenge selection for fresh registration
              Provider.of<ChallengeProvider>(context, listen: false).clearForNewRegistration();
              Navigator.pushNamed(context, '/register');
            },
            color: AppTheme.secondaryNeon,
          ),
        ],
      ),
    );
  }

  Widget _buildFeaturesSection(bool isMobile, bool isTablet) {
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 24),
      child: Column(
        children: [
          const Text(
            'Why Choose ORBIT?',
            textAlign: TextAlign.center,
            style: TextStyle(
              fontSize: 36,
              fontWeight: FontWeight.bold,
              color: AppTheme.textPrimary,
              letterSpacing: 2,
            ),
          ),
          const SizedBox(height: 60),
          Row(
            children: [
              Expanded(
                child: _buildFeatureCard(
                  icon: Icons.rocket_launch,
                  title: 'Funded Challenges',
                  description: 'Prove your skills and get funded with our professional trading challenges. Start with small capital and scale up as you demonstrate consistent profitability.',
                  color: AppTheme.primaryNeon,
                  onTap: () => Navigator.pushNamed(context, '/funded-challenges'),
                ),
              ),
              const SizedBox(width: 24),
              Expanded(
                child: _buildFeatureCard(
                  icon: Icons.copy,
                  title: 'Copy Trading',
                  description: 'Follow successful traders and automatically copy their strategies. Access proven trading methods and diversify your portfolio with expert insights.',
                  color: AppTheme.secondaryNeon,
                  onTap: () => Navigator.pushNamed(context, '/copy-trading'),
                ),
              ),
              const SizedBox(width: 24),
              Expanded(
                child: _buildFeatureCard(
                  icon: Icons.auto_awesome,
                  title: 'AI-Driven Algo Trading',
                  description: 'Access our powerful AI-driven trading strategies. Leverage machine learning insights and backtested algorithms to trade smarter and maximize profits.',
                  color: AppTheme.accentNeon,
                  onTap: () => Navigator.pushNamed(context, '/algo-trading'),
                ),
              ),
            ],
          ),
          const SizedBox(height: 60),
          _buildHowItWorksSection(),
          const SizedBox(height: 60),
          _buildStatisticsSection(),
        ],
      ),
    );
  }

  Widget _buildFeatureCard({
    required IconData icon,
    required String title,
    required String description,
    required Color color,
    VoidCallback? onTap,
  }) {
    return GestureDetector(
      onTap: onTap,
      child: Container(
        padding: const EdgeInsets.all(32),
        decoration: BoxDecoration(
          color: AppTheme.cardBackground,
          borderRadius: BorderRadius.circular(20),
          border: Border.all(
            color: color.withOpacity(0.3),
            width: 1,
          ),
          boxShadow: [
            BoxShadow(
              color: color.withOpacity(0.2),
              blurRadius: 20,
              spreadRadius: 2,
            ),
          ],
        ),
        child: Column(
          children: [
            Container(
              width: 80,
              height: 80,
              decoration: BoxDecoration(
                color: color.withOpacity(0.1),
                borderRadius: BorderRadius.circular(20),
                border: Border.all(
                  color: color.withOpacity(0.3),
                  width: 1,
                ),
              ),
              child: Icon(
                icon,
                size: 40,
                color: color,
              ),
            ),
            const SizedBox(height: 24),
            Text(
              title,
              textAlign: TextAlign.center,
              style: TextStyle(
                fontSize: 24,
                fontWeight: FontWeight.bold,
                color: AppTheme.textPrimary,
                letterSpacing: 1,
              ),
            ),
            const SizedBox(height: 16),
            Text(
              description,
              textAlign: TextAlign.center,
              style: TextStyle(
                fontSize: 16,
                color: AppTheme.textSecondary,
                height: 1.5,
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildHowItWorksSection() {
    return Column(
      children: [
        const Text(
          'How It Works',
          textAlign: TextAlign.center,
          style: TextStyle(
            fontSize: 36,
            fontWeight: FontWeight.bold,
            color: AppTheme.textPrimary,
            letterSpacing: 2,
          ),
        ),
        const SizedBox(height: 60),
        
        Row(
          children: [
            Expanded(
              child: _buildStepCard(
                number: '1',
                title: 'Create Account',
                description: 'Sign up and complete your profile in minutes. Get verified and set up your trading preferences.',
              ),
            ),
            const SizedBox(width: 30),
            Expanded(
              child: _buildStepCard(
                number: '2',
                title: 'Choose Challenge',
                description: 'Select from our range of funded trading challenges. Start with the level that matches your experience.',
              ),
            ),
            const SizedBox(width: 30),
            Expanded(
              child: _buildStepCard(
                number: '3',
                title: 'Start Trading',
                description: 'Trade with our capital and prove your skills. Use our advanced tools and analytics.',
              ),
            ),
            const SizedBox(width: 30),
            Expanded(
              child: _buildStepCard(
                number: '4',
                title: 'Get Funded',
                description: 'Pass the challenge and receive funded account access. Scale up with larger capital allocations.',
              ),
            ),
          ],
        ),
      ],
    );
  }

  Widget _buildStepCard({
    required String number,
    required String title,
    required String description,
  }) {
    return Column(
      children: [
        Container(
          width: 60,
          height: 60,
          decoration: BoxDecoration(
            gradient: const LinearGradient(
              colors: [AppTheme.primaryNeon, AppTheme.secondaryNeon],
              begin: Alignment.topLeft,
              end: Alignment.bottomRight,
            ),
            borderRadius: BorderRadius.circular(30),
            boxShadow: [
              BoxShadow(
                color: AppTheme.primaryNeon.withOpacity(0.3),
                blurRadius: 15,
                spreadRadius: 2,
              ),
            ],
          ),
          child: Center(
            child: Text(
              number,
              style: const TextStyle(
                color: Colors.black,
                fontSize: 24,
                fontWeight: FontWeight.bold,
              ),
            ),
          ),
        ),
        const SizedBox(height: 24),
        Text(
          title,
          textAlign: TextAlign.center,
          style: TextStyle(
            fontSize: 20,
            fontWeight: FontWeight.bold,
            color: AppTheme.textPrimary,
            letterSpacing: 1,
          ),
        ),
        const SizedBox(height: 16),
        Text(
          description,
          textAlign: TextAlign.center,
          style: TextStyle(
            fontSize: 16,
            color: AppTheme.textSecondary,
            height: 1.5,
          ),
        ),
      ],
    );
  }

  Widget _buildStatisticsSection() {
    return Row(
      children: [
        Expanded(
          child: _buildStatCard(
            number: '10,000+',
            label: 'Active Traders',
          ),
        ),
        const SizedBox(width: 24),
        Expanded(
          child: _buildStatCard(
            number: '\$50M+',
            label: 'Total Funding',
          ),
        ),
        const SizedBox(width: 24),
        Expanded(
          child: _buildStatCard(
            number: '95%',
            label: 'Success Rate',
          ),
        ),
        const SizedBox(width: 24),
        Expanded(
          child: _buildStatCard(
            number: '24/7',
            label: 'Support',
          ),
        ),
      ],
    );
  }

  Widget _buildStatCard({
    required String number,
    required String label,
  }) {
    return Column(
      children: [
        Text(
          number,
          style: TextStyle(
            fontSize: 48,
            fontWeight: FontWeight.bold,
            color: AppTheme.primaryNeon,
            letterSpacing: 2,
            shadows: [
              Shadow(
                color: AppTheme.primaryNeon.withOpacity(0.3),
                blurRadius: 10,
              ),
            ],
          ),
        ),
        const SizedBox(height: 16),
        Text(
          label,
          style: TextStyle(
            fontSize: 18,
            color: AppTheme.textSecondary,
            fontWeight: FontWeight.w500,
            letterSpacing: 1,
          ),
        ),
      ],
    );
  }

  Widget _buildActionButtons(bool isMobile, bool isTablet) {
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 24),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          if (isMobile)
            Expanded(
              child: FuturisticButton(
                text: 'JOIN ORBIT',
                onPressed: () => Navigator.pushNamed(context, '/services'),
                color: AppTheme.secondaryNeon,
              ),
            ),
          const SizedBox(width: 20),
          if (isMobile)
            Expanded(
              child: FuturisticButton(
                text: 'REGISTER',
                onPressed: () {
                  // Clear any existing challenge selection for fresh registration
                  Provider.of<ChallengeProvider>(context, listen: false).clearForNewRegistration();
                  Navigator.pushNamed(context, '/register');
                },
                color: AppTheme.accentNeon,
              ),
            ),
          const SizedBox(width: 20),
          if (isMobile)
            Expanded(
              child: FuturisticButton(
                text: 'LAUNCH',
                onPressed: () => Navigator.pushNamed(context, '/login'),
                color: AppTheme.primaryNeon,
              ),
            ),
          const SizedBox(width: 20),
          if (!isMobile)
            Expanded(
              child: Row(
                children: [
                  FuturisticButton(
                    text: 'JOIN ORBIT',
                    onPressed: () => Navigator.pushNamed(context, '/services'),
                    color: AppTheme.secondaryNeon,
                  ),
                  const SizedBox(width: 20),
                  FuturisticButton(
                    text: 'REGISTER',
                    onPressed: () {
                      // Clear any existing challenge selection for fresh registration
                      Provider.of<ChallengeProvider>(context, listen: false).clearForNewRegistration();
                      Navigator.pushNamed(context, '/register');
                    },
                    color: AppTheme.accentNeon,
                  ),
                  const SizedBox(width: 20),
                  FuturisticButton(
                    text: 'LAUNCH',
                    onPressed: () => Navigator.pushNamed(context, '/login'),
                    color: AppTheme.primaryNeon,
                  ),
                ],
              ),
            ),
        ],
      ),
    );
  }
}

// Simple background painter without candlesticks
class SimpleBackgroundPainter extends CustomPainter {
  @override
  void paint(Canvas canvas, Size size) {
    final paint = Paint()
      ..color = AppTheme.primaryNeon.withOpacity(0.03)
      ..style = PaintingStyle.fill;

    // Draw simple grid lines
    final gridPaint = Paint()
      ..color = AppTheme.primaryNeon.withOpacity(0.02)
      ..strokeWidth = 0.5;

    for (int i = 0; i < size.width; i += 80) {
      canvas.drawLine(
        Offset(i.toDouble(), 0),
        Offset(i.toDouble(), size.height),
        gridPaint,
      );
    }

    for (int i = 0; i < size.height; i += 80) {
      canvas.drawLine(
        Offset(0, i.toDouble()),
        Offset(size.width, i.toDouble()),
        gridPaint,
      );
    }

    // Draw subtle floating dots
    final dotPaint = Paint()
      ..color = AppTheme.primaryNeon.withOpacity(0.05)
      ..style = PaintingStyle.fill;

    for (int i = 0; i < 30; i++) {
      final x = (i * 47) % size.width;
      final y = (i * 73) % size.height;
      final radius = (i % 2 + 1) * 0.5;
      
      canvas.drawCircle(Offset(x, y), radius, dotPaint);
    }
  }

  @override
  bool shouldRepaint(covariant CustomPainter oldDelegate) => false;
}
