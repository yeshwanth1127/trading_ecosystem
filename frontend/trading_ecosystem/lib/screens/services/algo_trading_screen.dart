import 'package:flutter/material.dart';
import '../../utils/theme.dart';

class AlgoTradingScreen extends StatefulWidget {
  const AlgoTradingScreen({super.key});

  @override
  State<AlgoTradingScreen> createState() => _AlgoTradingScreenState();
}

class _AlgoTradingScreenState extends State<AlgoTradingScreen>
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
        painter: AlgoTradingBackgroundPainter(),
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
                  color: AppTheme.accentNeon,
                ),
                onPressed: () => Navigator.pop(context),
              ),
              const SizedBox(width: 16),
              const Text(
                'AI-DRIVEN ALGO TRADING',
                style: TextStyle(
                  fontSize: 28,
                  fontWeight: FontWeight.bold,
                  color: AppTheme.accentNeon,
                  letterSpacing: 3,
                  shadows: [
                    Shadow(
                      color: AppTheme.accentNeon,
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
                'AI-Driven Algo Trading',
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
                'Automated trading strategies powered by artificial intelligence',
                textAlign: TextAlign.center,
                style: TextStyle(
                  fontSize: 20,
                  color: AppTheme.textSecondary,
                  height: 1.5,
                ),
              ),
              
              const SizedBox(height: 60),
              
              // Coming soon placeholder
              _buildComingSoonSection(),
              
              const SizedBox(height: 40),
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
          color: AppTheme.accentNeon.withOpacity(0.3),
          width: 1,
        ),
      ),
      child: Column(
        children: [
          const Icon(
            Icons.auto_awesome,
            size: 64,
            color: AppTheme.accentNeon,
          ),
          
          const SizedBox(height: 24),
          
          const Text(
            'AI-Driven Algo Trading Coming Soon',
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
            'We\'re developing cutting-edge AI algorithms for automated trading. Experience the future of trading!',
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
            color: AppTheme.accentNeon,
          ),
        ],
      ),
    );
  }
}

// Custom painter for algo trading background
class AlgoTradingBackgroundPainter extends CustomPainter {
  @override
  void paint(Canvas canvas, Size size) {
    final paint = Paint()
      ..color = AppTheme.accentNeon.withOpacity(0.05)
      ..style = PaintingStyle.fill;

    // Draw AI neural network pattern
    final nodes = [
      {'x': 100, 'y': 120, 'size': 16},
      {'x': 250, 'y': 100, 'size': 20},
      {'x': 400, 'y': 140, 'size': 18},
      {'x': 150, 'y': 300, 'size': 22},
      {'x': 350, 'y': 280, 'size': 14},
    ];

    for (final node in nodes) {
      final x = node['x'] as double;
      final y = node['y'] as double;
      final size = node['size'] as double;
      
      canvas.drawCircle(Offset(x, y), size, paint);
    }

    // Draw connections between nodes
    final linePaint = Paint()
      ..color = AppTheme.accentNeon.withOpacity(0.03)
      ..strokeWidth = 1;

    for (int i = 0; i < nodes.length - 1; i++) {
      final node1 = nodes[i];
      final node2 = nodes[i + 1];
      canvas.drawLine(
        Offset(node1['x'] as double, node1['y'] as double),
        Offset(node2['x'] as double, node2['y'] as double),
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
