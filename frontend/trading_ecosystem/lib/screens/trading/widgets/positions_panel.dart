import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../../../models/position.dart';
import '../../../providers/trading_provider.dart';
import '../../../services/api_service.dart';

class PositionsPanel extends StatelessWidget {
  final List<Position> positions;
  final String title;
  final String type; // 'open' or 'closed'
  final String currency; // Add currency parameter
  final double? totalBalance; // Add total balance for percentage calculation

  const PositionsPanel({
    super.key,
    required this.positions,
    required this.title,
    required this.type,
    this.currency = 'INR', // Default to INR
    this.totalBalance,
  });

  @override
  Widget build(BuildContext context) {
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
                Icon(
                  type == 'open' ? Icons.open_in_new : Icons.check_circle,
                  color: type == 'open' ? Colors.blue : Colors.green,
                  size: 16,
                ),
                const SizedBox(width: 6),
                Expanded(
                  child: Text(
                    title,
                    style: const TextStyle(
                      color: Colors.white,
                      fontSize: 14,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                ),
                Text(
                  '${positions.length}',
                  style: const TextStyle(
                    color: Colors.grey,
                    fontSize: 12,
                  ),
                ),
              ],
            ),
          ),
          
          // Positions List (no internal scrolling, let it expand)
          positions.isEmpty
              ? _buildEmptyState()
              : Column(
                  children: positions.map((position) => _buildPositionItem(context, position)).toList(),
                ),
        ],
      ),
    );
  }

  Widget _buildEmptyState() {
    return Container(
      padding: const EdgeInsets.all(8),
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(
            type == 'open' ? Icons.open_in_new : Icons.check_circle,
            size: 20,
            color: Colors.grey,
          ),
          const SizedBox(height: 4),
          Text(
            type == 'open' ? 'No Positions' : 'No Closed',
            style: const TextStyle(
              color: Colors.grey,
              fontSize: 10,
              fontWeight: FontWeight.bold,
            ),
            textAlign: TextAlign.center,
          ),
        ],
      ),
    );
  }

  Widget _buildPositionItem(BuildContext context, Position position) {
    final isPositive = (position.unrealizedPnl ?? 0) >= 0;
    final pnlColor = isPositive ? Colors.green : Colors.red;
    final currencySymbol = currency == 'USD' ? '\$' : '₹';
    
    // Calculate percentage of balance
    double? percentageOfBalance;
    if (totalBalance != null && totalBalance! > 0 && position.unrealizedPnl != null) {
      percentageOfBalance = (position.unrealizedPnl! / totalBalance!) * 100;
    }
    
    return Container(
      margin: const EdgeInsets.symmetric(horizontal: 6, vertical: 1),
      decoration: BoxDecoration(
        color: const Color(0xFF2a2a2a),
        borderRadius: BorderRadius.circular(8),
        border: Border.all(
          color: position.side == PositionSide.LONG ? Colors.blue : Colors.orange,
          width: 1,
        ),
      ),
      child: Padding(
        padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 6),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          mainAxisSize: MainAxisSize.min,
          children: [
            // First row: Side, Symbol, Quantity
            Row(
              children: [
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 4, vertical: 1),
                  decoration: BoxDecoration(
                    color: position.side == PositionSide.LONG ? Colors.blue : Colors.orange,
                    borderRadius: BorderRadius.circular(2),
                  ),
                  child: Text(
                    position.side.value.toUpperCase(),
                    style: const TextStyle(
                      color: Colors.white,
                      fontSize: 8,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                ),
                const SizedBox(width: 4),
                // Show instrument symbol if available
                if (position.instrumentSymbol != null)
                  Text(
                    position.instrumentSymbol!,
                    style: const TextStyle(
                      color: Colors.cyan,
                      fontSize: 9,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                const SizedBox(width: 4),
                Expanded(
                  child: Text(
                    '${position.quantity.toStringAsFixed(2)}',
                    style: const TextStyle(
                      color: Colors.white,
                      fontSize: 10,
                      fontWeight: FontWeight.w600,
                    ),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 2),
            // Second row: Open Price and Current PnL
            Row(
              children: [
                Expanded(
                  child: Text(
                    'Open: $currencySymbol${position.averageEntryPrice.toStringAsFixed(2)}',
                    style: const TextStyle(
                      color: Colors.grey,
                      fontSize: 8,
                    ),
                  ),
                ),
                if (type == 'open' && position.unrealizedPnl != null)
                  Builder(
                    builder: (context) {
                      final pnl = position.unrealizedPnl!;
                      final displayPnl = pnl.isFinite && pnl.abs() < 1000000 ? pnl : 0.0;
                      return Text(
                        'PnL: $currencySymbol${displayPnl.toStringAsFixed(2)}',
                        style: TextStyle(
                          color: displayPnl >= 0 ? Colors.green : Colors.red,
                          fontWeight: FontWeight.bold,
                          fontSize: 9,
                        ),
                      );
                    },
                  ),
              ],
            ),
            // Third row: Current Price and Percentage
            if (position.currentPrice != null) ...[
              const SizedBox(height: 1),
              Row(
                children: [
                  Expanded(
                    child: Text(
                      'Current: $currencySymbol${position.currentPrice!.toStringAsFixed(2)}',
                      style: const TextStyle(
                        color: Colors.grey,
                        fontSize: 8,
                      ),
                    ),
                  ),
                  if (percentageOfBalance != null)
                    Text(
                      '${percentageOfBalance >= 0 ? '+' : ''}${percentageOfBalance.toStringAsFixed(1)}%',
                      style: TextStyle(
                        color: pnlColor,
                        fontSize: 8,
                        fontWeight: FontWeight.w500,
                      ),
                    ),
                ],
              ),
            ],
            // Fourth row: Leverage (if available)
            if (position.leverage != null) ...[
              const SizedBox(height: 1),
              Text(
                'Leverage: ${position.leverage!.toStringAsFixed(1)}x',
                style: const TextStyle(
                  color: Colors.grey,
                  fontSize: 8,
                ),
              ),
            ],
            // Action buttons for open positions
            if (type == 'open') ...[
              const SizedBox(height: 4),
              Row(
                mainAxisAlignment: MainAxisAlignment.end,
                children: [
                  GestureDetector(
                    onTap: () => _closePosition(context, position),
                    child: Container(
                      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
                      decoration: BoxDecoration(
                        color: Colors.red.withOpacity(0.2),
                        borderRadius: BorderRadius.circular(4),
                        border: Border.all(color: Colors.red, width: 1),
                      ),
                      child: const Text(
                        'Close',
                        style: TextStyle(
                          color: Colors.red,
                          fontSize: 8,
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                    ),
                  ),
                ],
              ),
            ],
          ],
        ),
      ),
    );
  }

  Future<void> _closePosition(BuildContext context, Position position) async {
    try {
      // Show confirmation dialog
      final confirmed = await showDialog<bool>(
        context: context,
        builder: (context) => AlertDialog(
          backgroundColor: const Color(0xFF1a1a1a),
          title: const Text(
            'Close Position',
            style: TextStyle(color: Colors.white),
          ),
          content: Text(
            'Are you sure you want to close this ${position.side.value} position of ${position.quantity.toStringAsFixed(2)} ${position.instrumentSymbol ?? 'units'}?',
            style: const TextStyle(color: Colors.grey),
          ),
          actions: [
            TextButton(
              onPressed: () => Navigator.of(context).pop(false),
              child: const Text('Cancel', style: TextStyle(color: Colors.grey)),
            ),
            TextButton(
              onPressed: () => Navigator.of(context).pop(true),
              child: const Text('Close', style: TextStyle(color: Colors.red)),
            ),
          ],
        ),
      );

      if (confirmed == true) {
        // Show loading indicator
        showDialog(
          context: context,
          barrierDismissible: false,
          builder: (context) => const Center(
            child: CircularProgressIndicator(color: Colors.blue),
          ),
        );

        // Close the position
        final apiService = ApiService();
        final result = await apiService.closePosition(position.positionId);

        // Hide loading indicator
        Navigator.of(context).pop();

        if (result.isSuccess) {
          // Refresh the trading data
          final tradingProvider = Provider.of<TradingProvider>(context, listen: false);
          await tradingProvider.loadUserPositionsData();
          await tradingProvider.loadUserBalance();

          // Show success message with better formatting
          final realizedPnl = result.data?['realized_pnl'] ?? 0;
          final pnlText = realizedPnl >= 0 ? '+${realizedPnl.toStringAsFixed(2)}' : realizedPnl.toStringAsFixed(2);
          
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(
              content: Text('Position closed successfully. PnL: $pnlText'),
              backgroundColor: Colors.green,
              duration: const Duration(seconds: 3),
            ),
          );
        } else {
          // Show detailed error message
          String errorMessage = result.error ?? 'Unknown error occurred';
          
          // Handle specific error cases
          if (errorMessage.contains('Authentication')) {
            errorMessage = 'Your session has expired. Please login again.';
          } else if (errorMessage.contains('timeout')) {
            errorMessage = 'Request timed out. Please check your connection and try again.';
          } else if (errorMessage.contains('Connection error')) {
            errorMessage = 'Cannot connect to server. Please check if the backend is running.';
          }
          
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(
              content: Text('Failed to close position: $errorMessage'),
              backgroundColor: Colors.red,
              duration: const Duration(seconds: 5),
              action: SnackBarAction(
                label: 'Retry',
                textColor: Colors.white,
                onPressed: () => _closePosition(context, position),
              ),
            ),
          );
        }
      }
    } catch (e) {
      // Hide loading indicator if it's still showing
      if (Navigator.of(context).canPop()) {
        Navigator.of(context).pop();
      }
      
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text('Error closing position: $e'),
          backgroundColor: Colors.red,
        ),
      );
    }
  }


}
