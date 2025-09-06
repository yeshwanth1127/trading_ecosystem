import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../providers/trading_provider.dart';
import '../utils/theme.dart';

class RealtimeDashboard extends StatefulWidget {
  const RealtimeDashboard({Key? key}) : super(key: key);

  @override
  State<RealtimeDashboard> createState() => _RealtimeDashboardState();
}

class _RealtimeDashboardState extends State<RealtimeDashboard>
    with TickerProviderStateMixin {
  late AnimationController _pulseController;
  late AnimationController _flashController;
  late Animation<double> _pulseAnimation;
  late Animation<double> _flashAnimation;

  @override
  void initState() {
    super.initState();
    
    // Pulse animation for live data indicator
    _pulseController = AnimationController(
      duration: const Duration(seconds: 2),
      vsync: this,
    );
    _pulseAnimation = Tween<double>(begin: 0.8, end: 1.0).animate(
      CurvedAnimation(parent: _pulseController, curve: Curves.easeInOut),
    );
    _pulseController.repeat(reverse: true);
    
    // Flash animation for P&L changes
    _flashController = AnimationController(
      duration: const Duration(milliseconds: 500),
      vsync: this,
    );
    _flashAnimation = Tween<double>(begin: 0.0, end: 1.0).animate(
      CurvedAnimation(parent: _flashController, curve: Curves.easeInOut),
    );
  }

  @override
  void dispose() {
    _pulseController.dispose();
    _flashController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Consumer<TradingProvider>(
      builder: (context, tradingProvider, child) {
        return Container(
          padding: const EdgeInsets.all(16),
          decoration: BoxDecoration(
            gradient: LinearGradient(
              begin: Alignment.topLeft,
              end: Alignment.bottomRight,
              colors: [
                AppTheme.darkBackground,
                AppTheme.darkBackground.withOpacity(0.8),
              ],
            ),
            borderRadius: BorderRadius.circular(12),
            border: Border.all(
              color: AppTheme.primaryColor.withOpacity(0.3),
              width: 1,
            ),
          ),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              _buildHeader(tradingProvider),
              const SizedBox(height: 16),
              _buildBalanceSection(tradingProvider),
              const SizedBox(height: 16),
              _buildPositionsSection(tradingProvider),
              const SizedBox(height: 16),
              _buildOrdersSection(tradingProvider),
            ],
          ),
        );
      },
    );
  }

  Widget _buildHeader(TradingProvider provider) {
    return Row(
      mainAxisAlignment: MainAxisAlignment.spaceBetween,
      children: [
        Text(
          'Live Trading Dashboard',
          style: AppTheme.headingStyle.copyWith(
            color: Colors.white,
            fontSize: 20,
          ),
        ),
        Row(
          children: [
            AnimatedBuilder(
              animation: _pulseAnimation,
              builder: (context, child) {
                return Transform.scale(
                  scale: _pulseAnimation.value,
                  child: Container(
                    width: 8,
                    height: 8,
                    decoration: BoxDecoration(
                      color: provider.isWebSocketConnected 
                          ? Colors.green 
                          : Colors.red,
                      shape: BoxShape.circle,
                    ),
                  ),
                );
              },
            ),
            const SizedBox(width: 8),
            Text(
              provider.isWebSocketConnected ? 'LIVE' : 'OFFLINE',
              style: AppTheme.bodyStyle.copyWith(
                color: provider.isWebSocketConnected 
                    ? Colors.green 
                    : Colors.red,
                fontWeight: FontWeight.bold,
                fontSize: 12,
              ),
            ),
          ],
        ),
      ],
    );
  }

  Widget _buildBalanceSection(TradingProvider provider) {
    final balance = provider.accountBalance;
    final totalEquity = provider.totalEquity;
    final unrealizedPnl = provider.unrealizedPnl;
    final realizedPnl = provider.realizedPnl;

    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: AppTheme.cardBackground,
        borderRadius: BorderRadius.circular(8),
        border: Border.all(
          color: AppTheme.primaryColor.withOpacity(0.2),
          width: 1,
        ),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            'Account Balance',
            style: AppTheme.subheadingStyle.copyWith(
              color: Colors.white70,
              fontSize: 14,
            ),
          ),
          const SizedBox(height: 12),
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              _buildBalanceCard(
                'Total Equity',
                totalEquity,
                Colors.blue,
                Icons.account_balance_wallet,
              ),
              _buildBalanceCard(
                'Unrealized P&L',
                unrealizedPnl,
                unrealizedPnl >= 0 ? Colors.green : Colors.red,
                Icons.trending_up,
              ),
              _buildBalanceCard(
                'Realized P&L',
                realizedPnl,
                realizedPnl >= 0 ? Colors.green : Colors.red,
                Icons.check_circle,
              ),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildBalanceCard(String title, double value, Color color, IconData icon) {
    return Expanded(
      child: Container(
        margin: const EdgeInsets.symmetric(horizontal: 4),
        padding: const EdgeInsets.all(12),
        decoration: BoxDecoration(
          color: color.withOpacity(0.1),
          borderRadius: BorderRadius.circular(8),
          border: Border.all(
            color: color.withOpacity(0.3),
            width: 1,
          ),
        ),
        child: Column(
          children: [
            Icon(
              icon,
              color: color,
              size: 20,
            ),
            const SizedBox(height: 8),
            Text(
              title,
              style: AppTheme.bodyStyle.copyWith(
                color: Colors.white70,
                fontSize: 12,
              ),
              textAlign: TextAlign.center,
            ),
            const SizedBox(height: 4),
            AnimatedBuilder(
              animation: _flashAnimation,
              builder: (context, child) {
                return Container(
                  padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                  decoration: BoxDecoration(
                    color: color.withOpacity(_flashAnimation.value * 0.2),
                    borderRadius: BorderRadius.circular(4),
                  ),
                  child: Text(
                    '\$${value.toStringAsFixed(2)}',
                    style: AppTheme.bodyStyle.copyWith(
                      color: color,
                      fontWeight: FontWeight.bold,
                      fontSize: 14,
                    ),
                  ),
                );
              },
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildPositionsSection(TradingProvider provider) {
    final openPositions = provider.getOpenPositions();

    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: AppTheme.cardBackground,
        borderRadius: BorderRadius.circular(8),
        border: Border.all(
          color: AppTheme.primaryColor.withOpacity(0.2),
          width: 1,
        ),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Text(
                'Open Positions',
                style: AppTheme.subheadingStyle.copyWith(
                  color: Colors.white70,
                  fontSize: 14,
                ),
              ),
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                decoration: BoxDecoration(
                  color: AppTheme.primaryColor.withOpacity(0.2),
                  borderRadius: BorderRadius.circular(12),
                ),
                child: Text(
                  '${openPositions.length}',
                  style: AppTheme.bodyStyle.copyWith(
                    color: AppTheme.primaryColor,
                    fontWeight: FontWeight.bold,
                    fontSize: 12,
                  ),
                ),
              ),
            ],
          ),
          const SizedBox(height: 12),
          if (openPositions.isEmpty)
            Center(
              child: Text(
                'No open positions',
                style: AppTheme.bodyStyle.copyWith(
                  color: Colors.white54,
                  fontSize: 14,
                ),
              ),
            )
          else
            ...openPositions.take(3).map((position) => _buildPositionCard(position)),
        ],
      ),
    );
  }

  Widget _buildPositionCard(dynamic position) {
    final symbol = position.instrumentSymbol ?? 'N/A';
    final side = position.side ?? 'N/A';
    final quantity = position.quantity ?? 0.0;
    final unrealizedPnl = position.unrealizedPnl ?? 0.0;
    final currentPrice = position.currentPrice ?? 0.0;
    final entryPrice = position.averageEntryPrice ?? 0.0;

    final isLong = side.toUpperCase() == 'LONG';
    final pnlColor = unrealizedPnl >= 0 ? Colors.green : Colors.red;

    return Container(
      margin: const EdgeInsets.only(bottom: 8),
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: AppTheme.darkBackground.withOpacity(0.5),
        borderRadius: BorderRadius.circular(8),
        border: Border.all(
          color: isLong ? Colors.green.withOpacity(0.3) : Colors.red.withOpacity(0.3),
          width: 1,
        ),
      ),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                children: [
                  Container(
                    padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                    decoration: BoxDecoration(
                      color: isLong ? Colors.green.withOpacity(0.2) : Colors.red.withOpacity(0.2),
                      borderRadius: BorderRadius.circular(4),
                    ),
                    child: Text(
                      side.toUpperCase(),
                      style: AppTheme.bodyStyle.copyWith(
                        color: isLong ? Colors.green : Colors.red,
                        fontWeight: FontWeight.bold,
                        fontSize: 10,
                      ),
                    ),
                  ),
                  const SizedBox(width: 8),
                  Text(
                    symbol,
                    style: AppTheme.bodyStyle.copyWith(
                      color: Colors.white,
                      fontWeight: FontWeight.bold,
                      fontSize: 14,
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 4),
              Text(
                'Qty: ${quantity.toStringAsFixed(4)}',
                style: AppTheme.bodyStyle.copyWith(
                  color: Colors.white70,
                  fontSize: 12,
                ),
              ),
            ],
          ),
          Column(
            crossAxisAlignment: CrossAxisAlignment.end,
            children: [
              Text(
                '\$${currentPrice.toStringAsFixed(2)}',
                style: AppTheme.bodyStyle.copyWith(
                  color: Colors.white,
                  fontWeight: FontWeight.bold,
                  fontSize: 14,
                ),
              ),
              const SizedBox(height: 4),
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                decoration: BoxDecoration(
                  color: pnlColor.withOpacity(0.2),
                  borderRadius: BorderRadius.circular(4),
                ),
                child: Text(
                  '${unrealizedPnl >= 0 ? '+' : ''}\$${unrealizedPnl.toStringAsFixed(2)}',
                  style: AppTheme.bodyStyle.copyWith(
                    color: pnlColor,
                    fontWeight: FontWeight.bold,
                    fontSize: 12,
                  ),
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildOrdersSection(TradingProvider provider) {
    final pendingOrders = provider.getPendingOrders();

    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: AppTheme.cardBackground,
        borderRadius: BorderRadius.circular(8),
        border: Border.all(
          color: AppTheme.primaryColor.withOpacity(0.2),
          width: 1,
        ),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Text(
                'Pending Orders',
                style: AppTheme.subheadingStyle.copyWith(
                  color: Colors.white70,
                  fontSize: 14,
                ),
              ),
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                decoration: BoxDecoration(
                  color: AppTheme.primaryColor.withOpacity(0.2),
                  borderRadius: BorderRadius.circular(12),
                ),
                child: Text(
                  '${pendingOrders.length}',
                  style: AppTheme.bodyStyle.copyWith(
                    color: AppTheme.primaryColor,
                    fontWeight: FontWeight.bold,
                    fontSize: 12,
                  ),
                ),
              ),
            ],
          ),
          const SizedBox(height: 12),
          if (pendingOrders.isEmpty)
            Center(
              child: Text(
                'No pending orders',
                style: AppTheme.bodyStyle.copyWith(
                  color: Colors.white54,
                  fontSize: 14,
                ),
              ),
            )
          else
            ...pendingOrders.take(3).map((order) => _buildOrderCard(order)),
        ],
      ),
    );
  }

  Widget _buildOrderCard(dynamic order) {
    final symbol = order.instrumentSymbol ?? 'N/A';
    final side = order.side ?? 'N/A';
    final orderType = order.orderType ?? 'N/A';
    final quantity = order.quantity ?? 0.0;
    final price = order.price ?? 0.0;
    final status = order.status ?? 'N/A';

    final isLong = side.toUpperCase() == 'BUY';
    final sideColor = isLong ? Colors.green : Colors.red;

    return Container(
      margin: const EdgeInsets.only(bottom: 8),
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: AppTheme.darkBackground.withOpacity(0.5),
        borderRadius: BorderRadius.circular(8),
        border: Border.all(
          color: sideColor.withOpacity(0.3),
          width: 1,
        ),
      ),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                children: [
                  Container(
                    padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                    decoration: BoxDecoration(
                      color: sideColor.withOpacity(0.2),
                      borderRadius: BorderRadius.circular(4),
                    ),
                    child: Text(
                      side.toUpperCase(),
                      style: AppTheme.bodyStyle.copyWith(
                        color: sideColor,
                        fontWeight: FontWeight.bold,
                        fontSize: 10,
                      ),
                    ),
                  ),
                  const SizedBox(width: 8),
                  Text(
                    symbol,
                    style: AppTheme.bodyStyle.copyWith(
                      color: Colors.white,
                      fontWeight: FontWeight.bold,
                      fontSize: 14,
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 4),
              Text(
                '$orderType • Qty: ${quantity.toStringAsFixed(4)}',
                style: AppTheme.bodyStyle.copyWith(
                  color: Colors.white70,
                  fontSize: 12,
                ),
              ),
            ],
          ),
          Column(
            crossAxisAlignment: CrossAxisAlignment.end,
            children: [
              Text(
                '\$${price.toStringAsFixed(2)}',
                style: AppTheme.bodyStyle.copyWith(
                  color: Colors.white,
                  fontWeight: FontWeight.bold,
                  fontSize: 14,
                ),
              ),
              const SizedBox(height: 4),
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                decoration: BoxDecoration(
                  color: AppTheme.primaryColor.withOpacity(0.2),
                  borderRadius: BorderRadius.circular(4),
                ),
                child: Text(
                  status.toUpperCase(),
                  style: AppTheme.bodyStyle.copyWith(
                    color: AppTheme.primaryColor,
                    fontWeight: FontWeight.bold,
                    fontSize: 10,
                  ),
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }
}
