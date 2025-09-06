import 'package:flutter/material.dart';
import '../../utils/theme.dart';

class ServicesScreen extends StatefulWidget {
  const ServicesScreen({super.key});

  @override
  State<ServicesScreen> createState() => _ServicesScreenState();
}

class _ServicesScreenState extends State<ServicesScreen>
    with TickerProviderStateMixin {
  late AnimationController _backgroundController;
  late AnimationController _headerController;
  late AnimationController _contentController;
  
  late Animation<double> _backgroundOpacity;
  late Animation<double> _headerOpacity;
  late Animation<Offset> _headerSlide;
  late Animation<double> _contentOpacity;
  late Animation<Offset> _contentSlide;

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
      begin: const Offset(0, -0.5),
      end: Offset.zero,
    ).animate(CurvedAnimation(
      parent: _headerController,
      curve: AppTheme.futuristicCurve,
    ));
    
    // Content animation
    _contentController = AnimationController(
      duration: const Duration(milliseconds: 1200),
      vsync: this,
    );
    _contentOpacity = Tween<double>(
      begin: 0.0,
      end: 1.0,
    ).animate(CurvedAnimation(
      parent: _contentController,
      curve: AppTheme.futuristicCurve,
    ));
    _contentSlide = Tween<Offset>(
      begin: const Offset(0, 0.3),
      end: Offset.zero,
    ).animate(CurvedAnimation(
      parent: _contentController,
      curve: AppTheme.futuristicCurve,
    ));
    
    // Start animations
    _startAnimations();
  }

  void _startAnimations() async {
    await Future.delayed(const Duration(milliseconds: 300));
    _backgroundController.forward();
    
    await Future.delayed(const Duration(milliseconds: 500));
    _headerController.forward();
    
    await Future.delayed(const Duration(milliseconds: 400));
    _contentController.forward();
  }

  @override
  void dispose() {
    _backgroundController.dispose();
    _headerController.dispose();
    _contentController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
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
              child: Column(
                children: [
                  // Header
                  _buildHeader(),
                  
                  // Content
                  Expanded(child: _buildContent()),
                ],
              ),
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
        painter: ServicesBackgroundPainter(),
        size: Size.infinite,
      ),
    );
  }

  Widget _buildHeader() {
    return FadeTransition(
      opacity: _headerOpacity,
      child: SlideTransition(
        position: _headerSlide,
        child: Container(
          padding: const EdgeInsets.all(24),
          child: Row(
            children: [
              IconButton(
                icon: const Icon(
                  Icons.arrow_back,
                  color: AppTheme.primaryNeon,
                ),
                onPressed: () => Navigator.pop(context),
              ),
              const SizedBox(width: 16),
              const Text(
                'ORBIT SERVICES',
                style: TextStyle(
                  fontSize: 28,
                  fontWeight: FontWeight.bold,
                  color: AppTheme.primaryNeon,
                  letterSpacing: 3,
                  shadows: [
                    Shadow(
                      color: AppTheme.primaryNeon,
                      blurRadius: 15,
                    ),
                  ],
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildContent() {
    return FadeTransition(
      opacity: _contentOpacity,
      child: SlideTransition(
        position: _contentSlide,
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(24),
          child: Column(
            children: [
              // Main heading
              const Text(
                'Our Services',
                textAlign: TextAlign.center,
                style: TextStyle(
                  fontSize: 48,
                  fontWeight: FontWeight.bold,
                  color: AppTheme.textPrimary,
                  letterSpacing: 2,
                ),
              ),
              
              const SizedBox(height: 20),
              
              const Text(
                'Discover the full range of ORBIT trading solutions',
                textAlign: TextAlign.center,
                style: TextStyle(
                  fontSize: 20,
                  color: AppTheme.textSecondary,
                  height: 1.5,
                ),
              ),
              
              const SizedBox(height: 60),
              
              // Services row
              _buildServicesRow(),
              
              const SizedBox(height: 60),
              
              // Coming soon section
              _buildComingSoonSection(),
              
              const SizedBox(height: 40),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildServicesRow() {
    return Row(
      children: [
        Expanded(
          child: _buildServiceCard(
            icon: Icons.rocket_launch,
            title: 'Funded Challenges',
            description: 'Professional trading challenges with funding opportunities',
            color: AppTheme.primaryNeon,
            onTap: () => Navigator.pushNamed(context, '/funded-challenges'),
          ),
        ),
        const SizedBox(width: 24),
        Expanded(
          child: _buildServiceCard(
            icon: Icons.copy,
            title: 'Copy Trading',
            description: 'Follow and copy successful traders automatically',
            color: AppTheme.secondaryNeon,
            onTap: () => Navigator.pushNamed(context, '/copy-trading'),
          ),
        ),
        const SizedBox(width: 24),
        Expanded(
          child: _buildServiceCard(
            icon: Icons.auto_awesome,
            title: 'AI-Driven Algo Trading',
            description: 'Automated trading strategies and backtesting',
            color: AppTheme.accentNeon,
            onTap: () => Navigator.pushNamed(context, '/algo-trading'),
          ),
        ),
      ],
    );
  }

  Widget _buildServiceCard({
    required IconData icon,
    required String title,
    required String description,
    required Color color,
    required VoidCallback onTap,
  }) {
    return GestureDetector(
      onTap: onTap,
      child: Container(
        height: 200,
        decoration: BoxDecoration(
          color: AppTheme.cardBackground,
          borderRadius: BorderRadius.circular(16),
          border: Border.all(
            color: color.withOpacity(0.3),
            width: 1,
          ),
          boxShadow: [
            BoxShadow(
              color: color.withOpacity(0.2),
              blurRadius: 15,
              spreadRadius: 1,
            ),
          ],
        ),
        child: Padding(
          padding: const EdgeInsets.all(20),
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Container(
                width: 60,
                height: 60,
                decoration: BoxDecoration(
                  color: color.withOpacity(0.1),
                  borderRadius: BorderRadius.circular(15),
                  border: Border.all(
                    color: color.withOpacity(0.3),
                    width: 1,
                  ),
                ),
                child: Icon(
                  icon,
                  color: color,
                  size: 30,
                ),
              ),
              
              const SizedBox(height: 16),
              
              Text(
                title,
                textAlign: TextAlign.center,
                style: TextStyle(
                  fontSize: 18,
                  fontWeight: FontWeight.bold,
                  color: AppTheme.textPrimary,
                  letterSpacing: 1,
                ),
              ),
              
              const SizedBox(height: 12),
              
              Text(
                description,
                textAlign: TextAlign.center,
                style: TextStyle(
                  fontSize: 14,
                  color: AppTheme.textSecondary,
                  height: 1.4,
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildComingSoonSection() {
    return Container(
      padding: const EdgeInsets.all(32),
      decoration: BoxDecoration(
        color: AppTheme.cardBackground,
        borderRadius: BorderRadius.circular(20),
        border: Border.all(
          color: AppTheme.primaryNeon.withOpacity(0.3),
          width: 1,
        ),
      ),
      child: Column(
        children: [
          const Icon(
            Icons.construction,
            size: 64,
            color: AppTheme.primaryNeon,
          ),
          
          const SizedBox(height: 24),
          
          const Text(
            'More Services Coming Soon',
            textAlign: TextAlign.center,
            style: TextStyle(
              fontSize: 28,
              fontWeight: FontWeight.bold,
              color: AppTheme.textPrimary,
              letterSpacing: 2,
            ),
          ),
          
          const SizedBox(height: 16),
          
          const Text(
            'We\'re constantly expanding our platform with new features and services. Stay tuned for updates!',
            textAlign: TextAlign.center,
            style: TextStyle(
              fontSize: 16,
              color: AppTheme.textSecondary,
              height: 1.5,
            ),
          ),
          
          const SizedBox(height: 32),
          
          FuturisticButton(
            text: 'GET NOTIFIED',
            onPressed: () {},
            color: AppTheme.primaryNeon,
          ),
        ],
      ),
    );
  }
}

// Custom painter for services background
class ServicesBackgroundPainter extends CustomPainter {
  @override
  void paint(Canvas canvas, Size size) {
    final paint = Paint()
      ..color = AppTheme.primaryNeon.withOpacity(0.05)
      ..style = PaintingStyle.fill;

    // Draw service icons pattern
    final icons = [
      {'x': 100, 'y': 100, 'size': 20},
      {'x': 300, 'y': 150, 'size': 15},
      {'x': 500, 'y': 100, 'size': 25},
      {'x': 200, 'y': 300, 'size': 18},
      {'x': 400, 'y': 350, 'size': 22},
      {'x': 150, 'y': 500, 'size': 16},
      {'x': 350, 'y': 450, 'size': 20},
    ];

    for (final icon in icons) {
      final x = icon['x'] as double;
      final y = icon['y'] as double;
      final size = icon['size'] as double;
      
      canvas.drawCircle(Offset(x, y), size, paint);
    }

    // Draw connecting lines
    final linePaint = Paint()
      ..color = AppTheme.primaryNeon.withOpacity(0.03)
      ..strokeWidth = 1;

    for (int i = 0; i < icons.length - 1; i++) {
      final icon1 = icons[i];
      final icon2 = icons[i + 1];
      canvas.drawLine(
        Offset(icon1['x'] as double, icon1['y'] as double),
        Offset(icon2['x'] as double, icon2['y'] as double),
        linePaint,
      );
    }

    // Draw grid
    for (int i = 0; i < size.width; i += 60) {
      canvas.drawLine(
        Offset(i.toDouble(), 0),
        Offset(i.toDouble(), size.height),
        linePaint,
      );
    }

    for (int i = 0; i < size.height; i += 60) {
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
