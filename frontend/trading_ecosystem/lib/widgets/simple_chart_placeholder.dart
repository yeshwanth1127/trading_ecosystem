import 'package:flutter/material.dart';

class SimpleChartPlaceholder extends StatelessWidget {
  final String symbol;
  final String interval;

  const SimpleChartPlaceholder({
    Key? key,
    required this.symbol,
    required this.interval,
  }) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return Container(
      width: double.infinity,
      height: double.infinity,
      decoration: BoxDecoration(
        color: const Color(0xFF131722),
        borderRadius: BorderRadius.circular(4),
      ),
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          const Icon(
            Icons.show_chart,
            color: Colors.blue,
            size: 64,
          ),
          const SizedBox(height: 16),
          Text(
            'Chart Placeholder',
            style: const TextStyle(
              color: Colors.white,
              fontSize: 18,
              fontWeight: FontWeight.bold,
            ),
          ),
          const SizedBox(height: 8),
          Text(
            'Symbol: $symbol',
            style: const TextStyle(
              color: Colors.grey,
              fontSize: 14,
            ),
          ),
          const SizedBox(height: 4),
          Text(
            'Interval: $interval',
            style: const TextStyle(
              color: Colors.grey,
              fontSize: 14,
            ),
          ),
          const SizedBox(height: 24),
          Container(
            padding: const EdgeInsets.all(16),
            decoration: BoxDecoration(
              color: const Color(0xFF1E222D),
              borderRadius: BorderRadius.circular(8),
              border: Border.all(
                color: const Color(0xFF2A2E39),
                width: 1,
              ),
            ),
            child: const Column(
              children: [
                Text(
                  'TradingView Chart',
                  style: TextStyle(
                    color: Colors.white,
                    fontSize: 16,
                    fontWeight: FontWeight.w500,
                  ),
                ),
                SizedBox(height: 8),
                Text(
                  'This is a placeholder for the TradingView chart.\nIf you see this, the WebView is working but TradingView failed to load.',
                  textAlign: TextAlign.center,
                  style: TextStyle(
                    color: Colors.grey,
                    fontSize: 12,
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}
