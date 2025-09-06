import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../../../providers/trading_provider.dart';

class BalanceSummaryPanel extends StatelessWidget {
  const BalanceSummaryPanel({super.key});

  @override
  Widget build(BuildContext context) {
    return Container(
      decoration: BoxDecoration(
        color: const Color(0xFF1E222D),
        border: Border(
          right: BorderSide(
            color: const Color(0xFF2A2E39),
            width: 1,
          ),
        ),
      ),
      child: Column(
        children: [
          _buildHeader(),
          Expanded(
            child: Consumer<TradingProvider>(
              builder: (context, tradingProvider, child) {
                final summary = tradingProvider.dashboardSummary ?? {};
                return SingleChildScrollView(
                  padding: const EdgeInsets.all(16),
                  child: Column(
                    children: [
                      _buildBalanceCard(summary),
                      const SizedBox(height: 16),
                      _buildEquityCard(summary),
                    ],
                  ),
                );
              },
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildHeader() {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: const BoxDecoration(
        border: Border(
          bottom: BorderSide(
            color: Color(0xFF2A2E39),
            width: 1,
          ),
        ),
      ),
      child: Row(
        children: [
          const Icon(
            Icons.account_balance_wallet,
            color: Color(0xFF667eea),
            size: 20,
          ),
          const SizedBox(width: 8),
          const Expanded(
            child: Text(
              'Account Summary',
              style: TextStyle(
                color: Colors.white,
                fontSize: 16,
                fontWeight: FontWeight.w600,
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildBalanceCard(Map<String, dynamic> summary) {
    final balance = summary['available_balance'] ?? summary['balance'] ?? 0.0;
    final currency = summary['currency'] ?? 'INR';
    final currencySymbol = currency == 'USD' ? '\$' : '₹';
    
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: const Color(0xFF2a2a2a),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: const Color(0xFF667eea), width: 2),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Text(
            'Available Balance',
            style: TextStyle(
              color: Colors.grey,
              fontSize: 14,
            ),
          ),
          const SizedBox(height: 8),
          Text(
            '$currencySymbol${balance.toStringAsFixed(2)}',
            style: const TextStyle(
              color: Colors.white,
              fontSize: 24,
              fontWeight: FontWeight.bold,
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildEquityCard(Map<String, dynamic> summary) {
    return Consumer<TradingProvider>(
      builder: (context, tradingProvider, child) {
        // Use summary data primarily to avoid glitching, only use provider data for real-time updates
        final equity = summary['total_equity'] ?? summary['equity'] ?? 0.0;
        final pnl = summary['unrealized_pnl'] ?? 0.0;
        final currency = summary['currency'] ?? 'INR';
        final currencySymbol = currency == 'USD' ? '\$' : '₹';
        final isPositive = pnl >= 0;
        
        return Container(
          width: double.infinity,
          padding: const EdgeInsets.all(16),
          decoration: BoxDecoration(
            color: const Color(0xFF2a2a2a),
            borderRadius: BorderRadius.circular(12),
            border: Border.all(
              color: isPositive ? Colors.green : Colors.red,
              width: 1,
            ),
          ),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const Text(
                'Total Equity',
                style: TextStyle(
                  color: Colors.grey,
                  fontSize: 14,
                ),
              ),
              const SizedBox(height: 8),
              Text(
                '$currencySymbol${equity.toStringAsFixed(2)}',
                style: const TextStyle(
                  color: Colors.white,
                  fontSize: 20,
                  fontWeight: FontWeight.bold,
                ),
              ),
              const SizedBox(height: 12),
              // Live P&L Section
              Container(
                padding: const EdgeInsets.all(12),
                decoration: BoxDecoration(
                  color: const Color(0xFF1a1a1a),
                  borderRadius: BorderRadius.circular(8),
                  border: Border.all(
                    color: isPositive ? Colors.green.withOpacity(0.3) : Colors.red.withOpacity(0.3),
                    width: 1,
                  ),
                ),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      children: [
                        Icon(
                          Icons.trending_up,
                          color: isPositive ? Colors.green : Colors.red,
                          size: 16,
                        ),
                        const SizedBox(width: 4),
                        const Text(
                          'Live P&L',
                          style: TextStyle(
                            color: Colors.grey,
                            fontSize: 12,
                            fontWeight: FontWeight.w500,
                          ),
                        ),
                        const Spacer(),
                        // Refresh button
                        GestureDetector(
                          onTap: () => tradingProvider.refreshPositionPrices(),
                          child: Container(
                            padding: const EdgeInsets.all(4),
                            decoration: BoxDecoration(
                              color: const Color(0xFF333333),
                              borderRadius: BorderRadius.circular(4),
                            ),
                            child: const Icon(
                              Icons.refresh,
                              color: Colors.grey,
                              size: 12,
                            ),
                          ),
                        ),
                        const SizedBox(width: 4),
                        // Real-time indicator
                        Container(
                          width: 6,
                          height: 6,
                          decoration: BoxDecoration(
                            color: tradingProvider.isWebSocketConnected 
                                ? Colors.green 
                                : Colors.red,
                            shape: BoxShape.circle,
                          ),
                        ),
                      ],
                    ),
                    const SizedBox(height: 8),
                    Text(
                      '${isPositive ? '+' : ''}$currencySymbol${pnl.toStringAsFixed(2)}',
                      style: TextStyle(
                        color: isPositive ? Colors.green : Colors.red,
                        fontSize: 18,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                    const SizedBox(height: 4),
                    Text(
                      '${isPositive ? '+' : ''}${_calculatePnlPercentage(pnl, equity)}%',
                      style: TextStyle(
                        color: isPositive ? Colors.green : Colors.red,
                        fontSize: 12,
                        fontWeight: FontWeight.w500,
                      ),
                    ),
                  ],
                ),
              ),
            ],
          ),
        );
      },
    );
  }
  
  String _calculatePnlPercentage(double pnl, double equity) {
    final availableBalance = equity - pnl;
    if (availableBalance <= 0) return '0.00';
    return ((pnl / availableBalance) * 100).toStringAsFixed(2);
  }
}
