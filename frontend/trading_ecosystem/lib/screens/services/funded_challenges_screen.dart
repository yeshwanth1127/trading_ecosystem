import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../../utils/theme.dart';
import '../../providers/challenge_provider.dart';
import '../../models/challenge_template.dart';

class FundedChallengesScreen extends StatefulWidget {
  const FundedChallengesScreen({super.key});

  @override
  State<FundedChallengesScreen> createState() => _FundedChallengesScreenState();
}

class _FundedChallengesScreenState extends State<FundedChallengesScreen>
    with TickerProviderStateMixin {
  late AnimationController _backgroundController;
  late AnimationController _headerController;
  late AnimationController _contentController;
  
  late Animation<double> _backgroundOpacity;
  late Animation<double> _headerOpacity;
  late Animation<Offset> _headerSlide;
  late Animation<double> _contentOpacity;
  late Animation<Offset> _contentSlide;

  // Category toggle state
  ChallengeCategory _selectedCategory = ChallengeCategory.stocks;

  // Challenge data
  final List<Map<String, dynamic>> _challenges = [
    // Stock Challenges
    {
      'id': 'challenge_50k',
      'amount': '₹50,000',
      'price': '₹2,499',
      'profitTarget': '₹5,000',
      'maxDrawdown': '₹45,000',
      'dailyLimit': '₹2,500',
      'color': AppTheme.primaryNeon,
      'category': ChallengeCategory.stocks,
    },
    {
      'id': 'challenge_1_5l',
      'amount': '₹1.5 Lakh',
      'price': '₹5,499',
      'profitTarget': '₹15,000',
      'maxDrawdown': '₹1.35 Lakh',
      'dailyLimit': '₹7,500',
      'color': AppTheme.secondaryNeon,
      'category': ChallengeCategory.stocks,
    },
    {
      'id': 'challenge_2l',
      'amount': '₹2 Lakh',
      'price': '₹7,499',
      'profitTarget': '₹20,000',
      'maxDrawdown': '₹1.8 Lakh',
      'dailyLimit': '₹10,000',
      'color': AppTheme.accentNeon,
      'category': ChallengeCategory.stocks,
    },
    {
      'id': 'challenge_5l',
      'amount': '₹5 Lakh',
      'price': '₹9,999',
      'profitTarget': '₹50,000',
      'maxDrawdown': '₹4.5 Lakh',
      'dailyLimit': '₹25,000',
      'color': AppTheme.warningNeon,
      'category': ChallengeCategory.stocks,
    },
    {
      'id': 'challenge_15l',
      'amount': '₹15 Lakh',
      'price': '₹14,499',
      'profitTarget': '₹1.5 Lakh',
      'maxDrawdown': '₹13.5 Lakh',
      'dailyLimit': '₹75,000',
      'color': AppTheme.successNeon,
      'category': ChallengeCategory.stocks,
    },
    {
      'id': 'challenge_25l',
      'amount': '₹25 Lakh',
      'price': '₹24,999',
      'profitTarget': '₹2.5 Lakh',
      'maxDrawdown': '₹22.5 Lakh',
      'dailyLimit': '₹1.25 Lakh',
      'color': AppTheme.primaryNeon,
      'category': ChallengeCategory.stocks,
    },
    
    // Crypto Challenges
    {
      'id': 'crypto_5k',
      'amount': '\$5,000',
      'price': '\$39',
      'profitTarget': '\$500',
      'maxDrawdown': '\$4,500',
      'dailyLimit': '\$250',
      'color': AppTheme.primaryNeon,
      'category': ChallengeCategory.crypto,
    },
    {
      'id': 'crypto_10k',
      'amount': '\$10,000',
      'price': '\$89',
      'profitTarget': '\$1,000',
      'maxDrawdown': '\$9,000',
      'dailyLimit': '\$500',
      'color': AppTheme.secondaryNeon,
      'category': ChallengeCategory.crypto,
    },
    {
      'id': 'crypto_25k',
      'amount': '\$25,000',
      'price': '\$149',
      'profitTarget': '\$2,500',
      'maxDrawdown': '\$22,500',
      'dailyLimit': '\$1,250',
      'color': AppTheme.accentNeon,
      'category': ChallengeCategory.crypto,
    },
    {
      'id': 'crypto_50k',
      'amount': '\$50,000',
      'price': '\$249',
      'profitTarget': '\$5,000',
      'maxDrawdown': '\$45,000',
      'dailyLimit': '\$2,500',
      'color': AppTheme.warningNeon,
      'category': ChallengeCategory.crypto,
    },
    {
      'id': 'crypto_100k',
      'amount': '\$100,000',
      'price': '\$499',
      'profitTarget': '\$10,000',
      'maxDrawdown': '\$90,000',
      'dailyLimit': '\$5,000',
      'color': AppTheme.successNeon,
      'category': ChallengeCategory.crypto,
    },
  ];

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
        painter: FundedChallengesBackgroundPainter(),
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
                'FUNDED CHALLENGES',
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
                'Choose Your Challenge',
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
                'Select a funded account challenge that matches your trading style',
                textAlign: TextAlign.center,
                style: TextStyle(
                  fontSize: 20,
                  color: AppTheme.textSecondary,
                  height: 1.5,
                ),
              ),
              
              const SizedBox(height: 40),
              
              // Category toggle
              _buildCategoryToggle(),
              
              const SizedBox(height: 40),
              
              // Challenge cards
              _buildChallengeCards(),
              
              const SizedBox(height: 60),
              
              // Rules section
              _buildRulesSection(),
              
              const SizedBox(height: 40),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildCategoryToggle() {
    return Container(
      padding: const EdgeInsets.all(8),
      decoration: BoxDecoration(
        color: AppTheme.cardBackground,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(
          color: AppTheme.primaryNeon.withOpacity(0.3),
          width: 1,
        ),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          _buildToggleOption(
            'STOCKS',
            ChallengeCategory.stocks,
            Icons.trending_up,
          ),
          const SizedBox(width: 8),
          _buildToggleOption(
            'CRYPTO',
            ChallengeCategory.crypto,
            Icons.currency_bitcoin,
          ),
        ],
      ),
    );
  }

  Widget _buildToggleOption(String label, ChallengeCategory category, IconData icon) {
    final isSelected = _selectedCategory == category;
    
    return GestureDetector(
      onTap: () {
        setState(() {
          _selectedCategory = category;
        });
      },
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 12),
        decoration: BoxDecoration(
          color: isSelected ? AppTheme.primaryNeon : Colors.transparent,
          borderRadius: BorderRadius.circular(12),
          boxShadow: isSelected ? [
            BoxShadow(
              color: AppTheme.primaryNeon.withOpacity(0.3),
              blurRadius: 8,
              spreadRadius: 1,
            ),
          ] : null,
        ),
        child: Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(
              icon,
              color: isSelected ? Colors.black : AppTheme.primaryNeon,
              size: 20,
            ),
            const SizedBox(width: 8),
            Text(
              label,
              style: TextStyle(
                fontSize: 16,
                fontWeight: FontWeight.bold,
                color: isSelected ? Colors.black : AppTheme.primaryNeon,
                letterSpacing: 1,
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildChallengeCards() {
    // Filter challenges based on selected category
    final filteredChallenges = _challenges.where((challenge) {
      return challenge['category'] == _selectedCategory;
    }).toList();

    return Column(
      children: [
        // First row - 3 cards
        Row(
          children: [
            if (filteredChallenges.length > 0)
              Expanded(child: _buildChallengeCard(filteredChallenges[0])),
            if (filteredChallenges.length > 0) const SizedBox(width: 20),
            if (filteredChallenges.length > 1)
              Expanded(child: _buildChallengeCard(filteredChallenges[1])),
            if (filteredChallenges.length > 1) const SizedBox(width: 20),
            if (filteredChallenges.length > 2)
              Expanded(child: _buildChallengeCard(filteredChallenges[2])),
          ],
        ),
        
        if (filteredChallenges.length > 3) const SizedBox(height: 30),
        
        // Second row - remaining cards
        if (filteredChallenges.length > 3)
          Row(
            children: [
              if (filteredChallenges.length > 3)
                Expanded(child: _buildChallengeCard(filteredChallenges[3])),
              if (filteredChallenges.length > 3) const SizedBox(width: 20),
              if (filteredChallenges.length > 4)
                Expanded(child: _buildChallengeCard(filteredChallenges[4])),
              if (filteredChallenges.length > 4) const SizedBox(width: 20),
              if (filteredChallenges.length > 5)
                Expanded(child: _buildChallengeCard(filteredChallenges[5])),
            ],
          ),
      ],
    );
  }



  Widget _buildChallengeCard(Map<String, dynamic> challenge) {
    return Container(
      padding: const EdgeInsets.all(24),
      decoration: BoxDecoration(
        color: AppTheme.cardBackground,
        borderRadius: BorderRadius.circular(20),
        border: Border.all(
          color: challenge['color'].withOpacity(0.3),
          width: 2,
        ),
        boxShadow: [
          BoxShadow(
            color: challenge['color'].withOpacity(0.2),
            blurRadius: 20,
            spreadRadius: 2,
          ),
        ],
      ),
      child: Column(
        children: [
          // Bestseller tag for 1.5 Lakh stock challenge
          if (challenge['amount'] == '₹1.5 Lakh')
            Container(
              margin: const EdgeInsets.only(bottom: 12),
              padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
              decoration: BoxDecoration(
                color: AppTheme.secondaryNeon,
                borderRadius: BorderRadius.circular(20),
                boxShadow: [
                  BoxShadow(
                    color: AppTheme.secondaryNeon.withOpacity(0.3),
                    blurRadius: 8,
                    spreadRadius: 1,
                  ),
                ],
              ),
              child: const Text(
                'BESTSELLER',
                style: TextStyle(
                  fontSize: 10,
                  fontWeight: FontWeight.bold,
                  color: Colors.black,
                  letterSpacing: 1,
                ),
              ),
            ),
          
          // Bestseller tag for $10,000 crypto challenge
          if (challenge['amount'] == '\$10,000')
            Container(
              margin: const EdgeInsets.only(bottom: 12),
              padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
              decoration: BoxDecoration(
                color: AppTheme.secondaryNeon,
                borderRadius: BorderRadius.circular(20),
                boxShadow: [
                  BoxShadow(
                    color: AppTheme.secondaryNeon.withOpacity(0.3),
                    blurRadius: 8,
                    spreadRadius: 1,
                  ),
                ],
              ),
              child: const Text(
                'BESTSELLER',
                style: TextStyle(
                  fontSize: 10,
                  fontWeight: FontWeight.bold,
                  color: Colors.black,
                  letterSpacing: 1,
                ),
              ),
            ),
          
          // Amount
          Text(
            challenge['amount'],
            style: TextStyle(
              fontSize: 32,
              fontWeight: FontWeight.bold,
              color: challenge['color'],
              letterSpacing: 1,
            ),
          ),
          
          const SizedBox(height: 8),
          
          // Price
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
            decoration: BoxDecoration(
              color: challenge['color'].withOpacity(0.1),
              borderRadius: BorderRadius.circular(12),
              border: Border.all(
                color: challenge['color'].withOpacity(0.3),
                width: 1,
              ),
            ),
            child: Text(
              challenge['price'],
              style: TextStyle(
                fontSize: 18,
                fontWeight: FontWeight.bold,
                color: challenge['color'],
              ),
            ),
          ),
          
          const SizedBox(height: 20),
          
          // Details
          _buildDetailRow('Profit Target:', '${challenge['profitTarget']} (10%)'),
          const SizedBox(height: 8),
          _buildDetailRow('Daily Limit:', '${challenge['dailyLimit']} (5%)'),
          const SizedBox(height: 8),
          _buildDetailRow('Max Drawdown:', '${challenge['maxDrawdown']} (10%)'),
          
          const SizedBox(height: 24),
          
          // Start button
          FuturisticButton(
            text: 'START CHALLENGE',
            onPressed: () {
              _startChallenge(challenge);
            },
            color: challenge['color'],
          ),
        ],
      ),
    );
  }

  Widget _buildDetailRow(String label, String value) {
    return Row(
      mainAxisAlignment: MainAxisAlignment.spaceBetween,
      children: [
        Text(
          label,
          style: const TextStyle(
            fontSize: 12,
            color: AppTheme.textSecondary,
          ),
        ),
        Text(
          value,
          style: const TextStyle(
            fontSize: 12,
            fontWeight: FontWeight.bold,
            color: AppTheme.textPrimary,
          ),
        ),
      ],
    );
  }

  Widget _buildRulesSection() {
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
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Text(
            'Challenge Rules',
            style: TextStyle(
              fontSize: 28,
              fontWeight: FontWeight.bold,
              color: AppTheme.primaryNeon,
              letterSpacing: 2,
            ),
          ),
          
          const SizedBox(height: 24),
          
          _buildRuleItem(
            'Profit Target',
            '10% of starting balance (e.g., ₹50k → ₹5,000 target)',
            Icons.trending_up,
          ),
          
          const SizedBox(height: 16),
          
          _buildRuleItem(
            'Maximum Drawdown',
            '10% trailing (account fails if balance falls below 90% of peak)',
            Icons.trending_down,
          ),
          
          const SizedBox(height: 16),
          
          _buildRuleItem(
            'Daily Loss Limit',
            '5% of starting balance per day',
            Icons.schedule,
          ),
        ],
      ),
    );
  }

  Widget _buildRuleItem(String title, String description, IconData icon) {
    return Row(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Container(
          padding: const EdgeInsets.all(8),
          decoration: BoxDecoration(
            color: AppTheme.primaryNeon.withOpacity(0.1),
            borderRadius: BorderRadius.circular(8),
          ),
          child: Icon(
            icon,
            color: AppTheme.primaryNeon,
            size: 20,
          ),
        ),
        
        const SizedBox(width: 16),
        
        Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                title,
                style: const TextStyle(
                  fontSize: 16,
                  fontWeight: FontWeight.bold,
                  color: AppTheme.textPrimary,
                ),
              ),
              
              const SizedBox(height: 4),
              
              Text(
                description,
                style: const TextStyle(
                  fontSize: 14,
                  color: AppTheme.textSecondary,
                  height: 1.4,
                ),
              ),
            ],
          ),
        ),
      ],
    );
  }

  void _startChallenge(Map<String, dynamic> challenge) {
    // Get the ChallengeProvider
    final challengeProvider = Provider.of<ChallengeProvider>(context, listen: false);
    
    // Create ChallengeData object
    final challengeData = ChallengeData(
      challengeId: challenge['id'],
      amount: challenge['amount'],
      price: challenge['price'],
      profitTarget: challenge['profitTarget'],
      maxDrawdown: challenge['maxDrawdown'],
      dailyLimit: challenge['dailyLimit'],
      category: challenge['category'] as ChallengeCategory,
    );
    
    // Debug logging
    print('Starting challenge: ${challenge['id']}');
    print('Challenge data: ${challengeData.toJson()}');
    
    // Store the selected challenge
    challengeProvider.selectChallenge(challengeData);
    
    // Verify the challenge was stored
    print('Stored challenge: ${challengeProvider.selectedChallenge?.toJson()}');
    
    // Navigate to registration screen
    Navigator.pushNamed(context, '/register');
  }
}

// Custom painter for funded challenges background
class FundedChallengesBackgroundPainter extends CustomPainter {
  @override
  void paint(Canvas canvas, Size size) {
    final paint = Paint()
      ..color = AppTheme.primaryNeon.withOpacity(0.05)
      ..style = PaintingStyle.fill;

    // Draw rocket pattern
    final rockets = [
      {'x': 100, 'y': 100, 'size': 20},
      {'x': 300, 'y': 150, 'size': 15},
      {'x': 500, 'y': 100, 'size': 25},
    ];

    for (final rocket in rockets) {
      final x = rocket['x'] as double;
      final y = rocket['y'] as double;
      final size = rocket['size'] as double;
      
      canvas.drawCircle(Offset(x, y), size, paint);
    }

    // Draw grid
    final gridPaint = Paint()
      ..color = AppTheme.primaryNeon.withOpacity(0.02)
      ..strokeWidth = 0.5;

    for (int i = 0; i < size.width; i += 60) {
      canvas.drawLine(
        Offset(i.toDouble(), 0),
        Offset(i.toDouble(), size.height),
        gridPaint,
      );
    }

    for (int i = 0; i < size.height; i += 60) {
      canvas.drawLine(
        Offset(0, i.toDouble()),
        Offset(size.width, i.toDouble()),
        gridPaint,
      );
    }
  }

  @override
  bool shouldRepaint(covariant CustomPainter oldDelegate) => false;
}
