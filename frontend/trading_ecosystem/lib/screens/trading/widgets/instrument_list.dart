import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'dart:async';
import '../../../models/instrument.dart';
import '../../../providers/trading_provider.dart';
import '../../../widgets/trading_view_chart.dart';

class InstrumentList extends StatefulWidget {
  const InstrumentList({Key? key}) : super(key: key);

  @override
  State<InstrumentList> createState() => _InstrumentListState();
}

class _InstrumentListState extends State<InstrumentList> {
  String _selectedType = 'crypto';
  String _searchQuery = '';
  Timer? _refreshTimer;

  @override
  void initState() {
    super.initState();
    _startAutoRefresh();
  }

  @override
  void dispose() {
    _refreshTimer?.cancel();
    super.dispose();
  }

  void _startAutoRefresh() {
    _refreshTimer = Timer.periodic(const Duration(minutes: 1), (timer) {
      if (mounted) {
        final tradingProvider = context.read<TradingProvider>();
        tradingProvider.refreshMarketData();
      }
    });
  }

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
          _buildTypeSelector(),
          _buildSearchBar(),
          Expanded(
            child: _buildInstrumentList(),
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
            Icons.show_chart,
            color: Colors.white,
            size: 20,
          ),
          const SizedBox(width: 8),
          const Expanded(
            child: Text(
              'Live Markets',
              style: TextStyle(
                color: Colors.white,
                fontSize: 16,
                fontWeight: FontWeight.w600,
              ),
            ),
          ),
          Consumer<TradingProvider>(
            builder: (context, tradingProvider, child) {
              return IconButton(
                onPressed: () => tradingProvider.refreshMarketData(),
                icon: tradingProvider.isLoading
                    ? const SizedBox(
                        width: 16,
                        height: 16,
                        child: CircularProgressIndicator(
                          strokeWidth: 2,
                          valueColor: AlwaysStoppedAnimation<Color>(Colors.white),
                        ),
                      )
                    : const Icon(
                        Icons.refresh,
                        color: Colors.white,
                        size: 20,
                      ),
                tooltip: 'Refresh Market Data',
              );
            },
          ),
        ],
      ),
    );
  }

  Widget _buildTypeSelector() {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
      child: Row(
        children: [
          Expanded(
            child: _buildTypeButton('crypto', 'Crypto'),
          ),
          const SizedBox(width: 8),
          Expanded(
            child: _buildTypeButton('stock', 'Stocks'),
          ),
        ],
      ),
    );
  }

  Widget _buildTypeButton(String type, String label) {
    final isSelected = _selectedType == type;
    return GestureDetector(
      onTap: () {
        setState(() {
          _selectedType = type;
        });
      },
      child: Container(
        padding: const EdgeInsets.symmetric(vertical: 8),
        decoration: BoxDecoration(
          color: isSelected ? const Color(0xFF2962FF) : Colors.transparent,
          borderRadius: BorderRadius.circular(6),
          border: Border.all(
            color: isSelected ? const Color(0xFF2962FF) : const Color(0xFF2A2E39),
            width: 1,
          ),
        ),
        child: Text(
          label,
          textAlign: TextAlign.center,
          style: TextStyle(
            color: isSelected ? Colors.white : const Color(0xFFB2B5BE),
            fontSize: 12,
            fontWeight: isSelected ? FontWeight.w600 : FontWeight.w500,
          ),
        ),
      ),
    );
  }

  Widget _buildSearchBar() {
    return Container(
      padding: const EdgeInsets.all(16),
      child: TextField(
        onChanged: (value) {
          setState(() {
            _searchQuery = value;
          });
        },
        style: const TextStyle(color: Colors.white),
        decoration: InputDecoration(
          hintText: 'Search instruments...',
          hintStyle: const TextStyle(color: Color(0xFF6B7280)),
          prefixIcon: const Icon(Icons.search, color: Color(0xFF6B7280)),
          filled: true,
          fillColor: const Color(0xFF2A2E39),
          border: OutlineInputBorder(
            borderRadius: BorderRadius.circular(8),
            borderSide: BorderSide.none,
          ),
          contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
        ),
      ),
    );
  }

  Widget _buildInstrumentList() {
    return Consumer<TradingProvider>(
      builder: (context, tradingProvider, child) {
        if (tradingProvider.isLoading) {
          return const Center(
            child: CircularProgressIndicator(
              valueColor: AlwaysStoppedAnimation<Color>(Colors.white),
            ),
          );
        }

        if (tradingProvider.error != null) {
          return Center(
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                const Icon(
                  Icons.error_outline,
                  color: Colors.red,
                  size: 48,
                ),
                const SizedBox(height: 16),
                Text(
                  'Error loading instruments',
                  style: const TextStyle(
                    color: Colors.white,
                    fontSize: 16,
                    fontWeight: FontWeight.w600,
                  ),
                ),
                const SizedBox(height: 8),
                Text(
                  tradingProvider.error!,
                  style: const TextStyle(
                    color: Colors.grey,
                    fontSize: 14,
                  ),
                  textAlign: TextAlign.center,
                ),
                const SizedBox(height: 16),
                ElevatedButton(
                  onPressed: () => tradingProvider.loadInstruments(),
                  style: ElevatedButton.styleFrom(
                    backgroundColor: Colors.blue,
                    foregroundColor: Colors.white,
                  ),
                  child: const Text('Retry'),
                ),
              ],
            ),
          );
        }

        final instruments = tradingProvider.getInstrumentsByType(_selectedType);
        final filteredInstruments = instruments.where((instrument) {
          if (_searchQuery.isEmpty) return true;
          return instrument.symbol.toLowerCase().contains(_searchQuery.toLowerCase()) ||
                 instrument.name.toLowerCase().contains(_searchQuery.toLowerCase());
        }).toList();

        if (filteredInstruments.isEmpty) {
          return const Center(
            child: Text(
              'No instruments found',
              style: TextStyle(
                color: Colors.grey,
                fontSize: 16,
              ),
            ),
          );
        }

        return ListView.builder(
          itemCount: filteredInstruments.length,
          itemBuilder: (context, index) {
            final instrument = filteredInstruments[index];
            return _buildInstrumentItem(instrument, tradingProvider);
          },
        );
      },
    );
  }

  Widget _buildInstrumentItem(Instrument instrument, TradingProvider tradingProvider) {
    final isSelected =
        tradingProvider.selectedInstrumentId == instrument.instrumentId;
    
    return ListTile(
      selected: isSelected,
      onTap: () {
        tradingProvider.setSelectedInstrument(instrument.instrumentId);
        if (instrument.tvSymbol != null) {
          tradingProvider.setTvSymbol(instrument.tvSymbol!);
        } else {
          tradingProvider.setTvSymbol(
            tradingProvider.inferTvSymbol(
              symbol: instrument.symbol,
              type: instrument.type.value,
            ),
          );
        }
        
        // Open TradingView chart
        Navigator.of(context).push(
          MaterialPageRoute(
            builder: (context) => TradingViewChart(
              symbol: instrument.tvSymbol ?? 'BINANCE:${instrument.symbol}INR',
              interval: tradingProvider.selectedInterval,
            ),
          ),
        );
      },
      title: Text(
        instrument.symbol,
        style: TextStyle(
          color: isSelected ? Colors.white : const Color(0xFFE5E7EB),
          fontSize: 14,
          fontWeight: FontWeight.w600,
        ),
      ),
      subtitle: Text(
        instrument.name,
        style: const TextStyle(
          color: Color(0xFF9CA3AF),
          fontSize: 12,
        ),
        maxLines: 1,
        overflow: TextOverflow.ellipsis,
      ),
      trailing: Column(
        crossAxisAlignment: CrossAxisAlignment.end,
        children: [
                     Text(
             '₹${instrument.currentPrice.toStringAsFixed(2)}',
             style: TextStyle(
               color: isSelected ? Colors.white : const Color(0xFFE5E7EB),
               fontSize: 14,
               fontWeight: FontWeight.w600,
             ),
           ),
          if (instrument.priceChange24h != null) ...[
            const SizedBox(height: 4),
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
              decoration: BoxDecoration(
                color: instrument.priceChange24h! >= 0 
                    ? const Color(0xFF10B981).withOpacity(0.2)
                    : const Color(0xFFEF4444).withOpacity(0.2),
                borderRadius: BorderRadius.circular(4),
              ),
              child: Text(
                '${instrument.priceChange24h! >= 0 ? '+' : ''}${instrument.priceChange24h!.toStringAsFixed(2)}%',
                style: TextStyle(
                  color: instrument.priceChange24h! >= 0 
                      ? const Color(0xFF10B981)
                      : const Color(0xFFEF4444),
                  fontSize: 10,
                  fontWeight: FontWeight.w600,
                ),
              ),
            ),
          ],
        ],
      ),
    );
  }
}
