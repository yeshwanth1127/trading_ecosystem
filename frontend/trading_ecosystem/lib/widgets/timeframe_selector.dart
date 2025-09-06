import 'package:flutter/material.dart';

class TimeframeSelector extends StatelessWidget {
  final String selectedInterval;
  final Function(String) onIntervalChanged;
  final List<TimeframeOption> intervals;

  const TimeframeSelector({
    Key? key,
    required this.selectedInterval,
    required this.onIntervalChanged,
    this.intervals = const [
      TimeframeOption("1", "1m"),
      TimeframeOption("3", "3m"),
      TimeframeOption("5", "5m"),
      TimeframeOption("15", "15m"),
      TimeframeOption("30", "30m"),
      TimeframeOption("60", "1h"),
      TimeframeOption("240", "4h"),
      TimeframeOption("1D", "1d"),
      TimeframeOption("1W", "1w"),
      TimeframeOption("1M", "1M"),
    ],
  }) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
      decoration: BoxDecoration(
        color: const Color(0xFF1E222D),
        borderRadius: BorderRadius.circular(8),
        border: Border.all(
          color: const Color(0xFF2A2E39),
          width: 1,
        ),
      ),
      child: SingleChildScrollView(
        scrollDirection: Axis.horizontal,
        child: Row(
          mainAxisSize: MainAxisSize.min,
          children: intervals.map((interval) {
            final isSelected = interval.value == selectedInterval;
            return Padding(
              padding: const EdgeInsets.only(right: 8),
              child: _buildTimeframeChip(interval, isSelected),
            );
          }).toList(),
        ),
      ),
    );
  }

  Widget _buildTimeframeChip(TimeframeOption interval, bool isSelected) {
    return GestureDetector(
      onTap: () => onIntervalChanged(interval.value),
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
        decoration: BoxDecoration(
          color: isSelected ? const Color(0xFF2962FF) : Colors.transparent,
          borderRadius: BorderRadius.circular(16),
          border: Border.all(
            color: isSelected ? const Color(0xFF2962FF) : const Color(0xFF2A2E39),
            width: 1,
          ),
        ),
        child: Text(
          interval.label,
          style: TextStyle(
            color: isSelected ? Colors.white : const Color(0xFFB2B5BE),
            fontSize: 12,
            fontWeight: isSelected ? FontWeight.w600 : FontWeight.w500,
          ),
        ),
      ),
    );
  }
}

class TimeframeOption {
  final String value;
  final String label;

  const TimeframeOption(this.value, this.label);
}
