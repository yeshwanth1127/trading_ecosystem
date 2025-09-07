import 'package:flutter/material.dart';
import '../../../models/order.dart';

class TradesPanel extends StatelessWidget {
  final List<Order> orders;
  final String title;

  const TradesPanel({
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
                const Icon(Icons.history, color: Colors.lightBlue, size: 16),
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
                  '${orders.length}',
                  style: const TextStyle(color: Colors.grey, fontSize: 12),
                ),
              ],
            ),
          ),
          orders.isEmpty
              ? _buildEmpty()
              : Column(children: orders.map(_buildItem).toList()),
        ],
      ),
    );
  }

  Widget _buildEmpty() {
    return Padding(
      padding: const EdgeInsets.all(12),
      child: Column(
        children: const [
          Icon(Icons.history, color: Colors.grey, size: 20),
          SizedBox(height: 4),
          Text('No Trades', style: TextStyle(color: Colors.grey, fontSize: 10, fontWeight: FontWeight.bold)),
        ],
      ),
    );
  }

  Widget _buildItem(Order o) {
    final sideColor = o.side == OrderSide.BUY ? Colors.green : Colors.red;
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
          children: [
            Row(
              children: [
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                  decoration: BoxDecoration(color: sideColor, borderRadius: BorderRadius.circular(3)),
                  child: Text(
                    o.side.value.toUpperCase(),
                    style: const TextStyle(color: Colors.white, fontSize: 9, fontWeight: FontWeight.bold),
                  ),
                ),
                const SizedBox(width: 6),
                Expanded(
                  child: Text(
                    o.instrumentId,
                    style: const TextStyle(color: Colors.white, fontSize: 12, fontWeight: FontWeight.bold),
                  ),
                ),
                Text(
                  '\$${o.totalAmount.toStringAsFixed(2)}',
                  style: const TextStyle(color: Colors.white, fontSize: 12, fontWeight: FontWeight.bold),
                ),
              ],
            ),
            const SizedBox(height: 2),
            Row(
              children: [
                Expanded(
                  child: Text(
                    'Qty: ${o.quantity.toStringAsFixed(4)}',
                    style: const TextStyle(color: Colors.grey, fontSize: 10),
                  ),
                ),
                if (o.price != null)
                  Text('Entry: ${o.price!.toStringAsFixed(6)}', style: const TextStyle(color: Colors.grey, fontSize: 10)),
                if (o.notes != null) ...[
                  const SizedBox(width: 8),
                  Text('Exit: ${o.notes!.replaceFirst('exit:', '')}', style: const TextStyle(color: Colors.grey, fontSize: 10)),
                ],
              ],
            ),
          ],
        ),
      ),
    );
  }
}


