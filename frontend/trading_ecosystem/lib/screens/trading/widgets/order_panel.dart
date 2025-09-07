import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../../../models/order.dart';
import '../../../providers/trading_provider.dart';

class OrderPanel extends StatelessWidget {
  final List<Order> orders;
  final String title;

  const OrderPanel({
    super.key,
    required this.orders,
    required this.title,
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
                const Icon(
                  Icons.pending_actions,
                  color: Colors.orange,
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
                // Real-time indicator
                Consumer<TradingProvider>(
                  builder: (context, tradingProvider, child) {
                    return Container(
                      margin: const EdgeInsets.only(right: 8),
                      width: 6,
                      height: 6,
                      decoration: BoxDecoration(
                        color: tradingProvider.isWebSocketConnected 
                            ? Colors.green 
                            : Colors.red,
                        shape: BoxShape.circle,
                      ),
                    );
                  },
                ),
                Text(
                  '${orders.length}',
                  style: const TextStyle(
                    color: Colors.grey,
                    fontSize: 12,
                  ),
                ),
              ],
            ),
          ),
          
          // Orders List (no internal scrolling, let it expand)
          orders.isEmpty
              ? _buildEmptyState()
              : Column(
                  children: orders.map((order) => _buildOrderItem(order)).toList(),
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
          const Icon(
            Icons.pending_actions,
            size: 20,
            color: Colors.grey,
          ),
          const SizedBox(height: 4),
          const Text(
            'No Orders',
            style: TextStyle(
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

  Widget _buildOrderItem(Order order) {
    final sideColor = order.side == OrderSide.BUY ? Colors.green : Colors.red;
    
    return Container(
      margin: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
      decoration: BoxDecoration(
        color: const Color(0xFF2a2a2a),
        borderRadius: BorderRadius.circular(8),
        border: Border.all(color: sideColor, width: 1),
      ),
      child: Padding(
        padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          mainAxisSize: MainAxisSize.min,
          children: [
            // First row: Side, Type, Amount
            Row(
              children: [
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                  decoration: BoxDecoration(
                    color: sideColor,
                    borderRadius: BorderRadius.circular(3),
                  ),
                  child: Text(
                    order.side.value.toUpperCase(),
                    style: const TextStyle(
                      color: Colors.white,
                      fontSize: 9,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                ),
                const SizedBox(width: 6),
                Text(
                  order.orderType.value.toUpperCase(),
                  style: const TextStyle(
                    color: Colors.grey,
                    fontSize: 9,
                    fontWeight: FontWeight.bold,
                  ),
                ),
                const Spacer(),
                Text(
                  '\$${order.totalAmount.toStringAsFixed(2)}',
                  style: const TextStyle(
                    color: Colors.white,
                    fontWeight: FontWeight.bold,
                    fontSize: 12,
                  ),
                ),
              ],
            ),
            const SizedBox(height: 2),
            // Second row: Quantity and Price
            Row(
              children: [
                Expanded(
                  child: Text(
                    'Qty: ${order.quantity.toStringAsFixed(2)}',
                    style: const TextStyle(
                      color: Colors.grey,
                      fontSize: 10,
                    ),
                  ),
                ),
                if (order.price != null)
                  Text(
                    'Price: \$${order.price!.toStringAsFixed(2)}',
                    style: const TextStyle(
                      color: Colors.grey,
                      fontSize: 10,
                    ),
                  ),
              ],
            ),
            // Third row: Filled and Status
            Row(
              children: [
                Expanded(
                  child: Text(
                    'Filled: ${order.filledQuantity.toStringAsFixed(2)}',
                    style: const TextStyle(
                      color: Colors.grey,
                      fontSize: 10,
                    ),
                  ),
                ),
                Text(
                  order.filledQuantity > 0 ? 'FILLED' : 'PENDING',
                  style: TextStyle(
                    color: order.filledQuantity > 0 ? Colors.green : Colors.orange,
                    fontSize: 10,
                    fontWeight: FontWeight.bold,
                  ),
                ),
              ],
            ),
            // Fourth row: Notes (if available)
            if (order.notes != null && order.notes!.isNotEmpty) ...[
              const SizedBox(height: 2),
              Text(
                'Note: ${order.notes}',
                style: const TextStyle(
                  color: Colors.grey,
                  fontSize: 9,
                ),
                maxLines: 1,
                overflow: TextOverflow.ellipsis,
              ),
            ],
            // Action buttons for active orders
            if (order.filledQuantity <= 0) ...[
              const SizedBox(height: 4),
              Row(
                mainAxisAlignment: MainAxisAlignment.end,
                children: [
                  GestureDetector(
                    onTap: () {
                      // TODO: Implement cancel order
                    },
                    child: Container(
                      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
                      decoration: BoxDecoration(
                        color: Colors.red.withOpacity(0.2),
                        borderRadius: BorderRadius.circular(4),
                        border: Border.all(color: Colors.red, width: 1),
                      ),
                      child: const Text(
                        'Cancel',
                        style: TextStyle(
                          color: Colors.red,
                          fontSize: 10,
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
}
