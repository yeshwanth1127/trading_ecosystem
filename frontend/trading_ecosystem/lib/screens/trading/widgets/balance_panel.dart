import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'order_placement_panel.dart';
import '../../../providers/trading_provider.dart';

class BalancePanel extends StatelessWidget {
  final Map<String, dynamic> summary;
  final bool isCompact;

  const BalancePanel({
    super.key,
    required this.summary,
    this.isCompact = false,
  });

  @override
  Widget build(BuildContext context) {
    if (isCompact) {
      return _buildCompactLayout();
    }
    
    return Container(
      decoration: const BoxDecoration(
        color: Color(0xFF1a1a1a),
        border: Border(
          left: BorderSide(color: Color(0xFF333333), width: 1),
        ),
      ),
      child: Column(
        children: [
          // Header
          Container(
            padding: const EdgeInsets.all(16),
            decoration: const BoxDecoration(
              color: Color(0xFF2a2a2a),
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
                    'Account Balance',
                    style: TextStyle(
                      color: Colors.white,
                      fontSize: 16,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                ),
                // Real-time indicator
                Consumer<TradingProvider>(
                  builder: (context, tradingProvider, child) {
                    return Container(
                      width: 8,
                      height: 8,
                      decoration: BoxDecoration(
                        color: tradingProvider.isWebSocketConnected 
                            ? Colors.green 
                            : Colors.red,
                        shape: BoxShape.circle,
                      ),
                    );
                  },
                ),
              ],
            ),
          ),
          
          // Order Placement Section
          Expanded(
            child: SingleChildScrollView(
              padding: const EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  OrderPlacementPanel(
                    balanceSummary: summary,
                  ),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildCompactLayout() {
    return Consumer<TradingProvider>(
      builder: (context, tradingProvider, child) {
        // Use summary data primarily to avoid glitching
        final balance = summary['available_balance'] ?? summary['balance'] ?? 0.0;
        final equity = summary['total_equity'] ?? summary['equity'] ?? 0.0;
        final pnl = summary['unrealized_pnl'] ?? 0.0;
        final currency = summary['currency'] ?? 'INR';
        final currencySymbol = currency == 'USD' ? '\$' : '₹';
        final isPositive = pnl >= 0;
    
    return Container(
      margin: const EdgeInsets.all(8),
      decoration: BoxDecoration(
        color: const Color(0xFF1a1a1a),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: const Color(0xFF333333), width: 1),
      ),
      child: Column(
        children: [
          // Header
          Container(
            padding: const EdgeInsets.all(12),
            decoration: const BoxDecoration(
              color: Color(0xFF2a2a2a),
              borderRadius: BorderRadius.only(
                topLeft: Radius.circular(12),
                topRight: Radius.circular(12),
              ),
            ),
            child: Row(
              children: [
                const Icon(
                  Icons.account_balance_wallet,
                  color: Color(0xFF667eea),
                  size: 16,
                ),
                const SizedBox(width: 6),
                const Expanded(
                  child: Text(
                    'Balance',
                    style: TextStyle(
                      color: Colors.white,
                      fontSize: 14,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                ),
              ],
            ),
          ),
          
          // Compact Balance Info
          Expanded(
            child: Padding(
              padding: const EdgeInsets.all(12),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  Text(
                    'Available: $currencySymbol${balance.toStringAsFixed(2)}',
                    style: const TextStyle(
                      color: Colors.white,
                      fontSize: 12,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                  const SizedBox(height: 4),
                  Text(
                    'Equity: $currencySymbol${equity.toStringAsFixed(2)}',
                    style: const TextStyle(
                      color: Colors.grey,
                      fontSize: 10,
                    ),
                  ),
                  if (pnl != 0) ...[
                    const SizedBox(height: 4),
                    Row(
                      children: [
                        Icon(
                          isPositive ? Icons.trending_up : Icons.trending_down,
                          color: isPositive ? Colors.green : Colors.red,
                          size: 12,
                        ),
                        const SizedBox(width: 2),
                                                 Text(
                           '${isPositive ? '+' : ''}$currencySymbol${pnl.toStringAsFixed(2)}',
                           style: TextStyle(
                             color: isPositive ? Colors.green : Colors.red,
                             fontSize: 10,
                             fontWeight: FontWeight.w500,
                           ),
                         ),
                      ],
                    ),
                  ],
                ],
              ),
            ),
          ),
        ],
      ),
    );
      },
    );
  }
}
