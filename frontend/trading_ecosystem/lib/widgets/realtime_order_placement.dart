import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../providers/trading_provider.dart';
import '../utils/theme.dart';

class RealtimeOrderPlacement extends StatefulWidget {
  const RealtimeOrderPlacement({Key? key}) : super(key: key);

  @override
  State<RealtimeOrderPlacement> createState() => _RealtimeOrderPlacementState();
}

class _RealtimeOrderPlacementState extends State<RealtimeOrderPlacement> {
  final _formKey = GlobalKey<FormState>();
  final _quantityController = TextEditingController();
  final _priceController = TextEditingController();
  
  String _selectedSide = 'BUY';
  String _selectedOrderType = 'MARKET';
  String _selectedInstrument = 'BTCUSDT';
  
  @override
  void dispose() {
    _quantityController.dispose();
    _priceController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Consumer<TradingProvider>(
      builder: (context, tradingProvider, child) {
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
          child: Form(
            key: _formKey,
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                _buildHeader(tradingProvider),
                const SizedBox(height: 16),
                _buildOrderForm(tradingProvider),
                const SizedBox(height: 16),
                _buildPlaceOrderButton(tradingProvider),
              ],
            ),
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
          'Place Order',
          style: AppTheme.headingStyle.copyWith(
            color: Colors.white,
            fontSize: 18,
          ),
        ),
        Row(
          children: [
            Container(
              width: 6,
              height: 6,
              decoration: BoxDecoration(
                color: provider.isWebSocketConnected 
                    ? Colors.green 
                    : Colors.red,
                shape: BoxShape.circle,
              ),
            ),
            const SizedBox(width: 4),
            Text(
              provider.isWebSocketConnected ? 'LIVE' : 'OFFLINE',
              style: AppTheme.bodyStyle.copyWith(
                color: provider.isWebSocketConnected 
                    ? Colors.green 
                    : Colors.red,
                fontSize: 10,
                fontWeight: FontWeight.bold,
              ),
            ),
          ],
        ),
      ],
    );
  }

  Widget _buildOrderForm(TradingProvider provider) {
    return Column(
      children: [
        // Side Selection
        Row(
          children: [
            Expanded(
              child: _buildSideButton('BUY', Colors.green),
            ),
            const SizedBox(width: 8),
            Expanded(
              child: _buildSideButton('SELL', Colors.red),
            ),
          ],
        ),
        const SizedBox(height: 12),
        
        // Order Type Selection
        DropdownButtonFormField<String>(
          value: _selectedOrderType,
          decoration: InputDecoration(
            labelText: 'Order Type',
            labelStyle: const TextStyle(color: Colors.white70),
            border: OutlineInputBorder(
              borderRadius: BorderRadius.circular(8),
              borderSide: BorderSide(color: AppTheme.primaryColor.withOpacity(0.3)),
            ),
            enabledBorder: OutlineInputBorder(
              borderRadius: BorderRadius.circular(8),
              borderSide: BorderSide(color: AppTheme.primaryColor.withOpacity(0.3)),
            ),
            focusedBorder: OutlineInputBorder(
              borderRadius: BorderRadius.circular(8),
              borderSide: BorderSide(color: AppTheme.primaryColor),
            ),
          ),
          dropdownColor: AppTheme.darkBackground,
          style: const TextStyle(color: Colors.white),
          items: ['MARKET', 'LIMIT', 'STOP', 'STOP_LIMIT']
              .map((type) => DropdownMenuItem(
                    value: type,
                    child: Text(type),
                  ))
              .toList(),
          onChanged: (value) {
            setState(() {
              _selectedOrderType = value!;
            });
          },
        ),
        const SizedBox(height: 12),
        
        // Instrument Selection
        DropdownButtonFormField<String>(
          value: _selectedInstrument,
          decoration: InputDecoration(
            labelText: 'Instrument',
            labelStyle: const TextStyle(color: Colors.white70),
            border: OutlineInputBorder(
              borderRadius: BorderRadius.circular(8),
              borderSide: BorderSide(color: AppTheme.primaryColor.withOpacity(0.3)),
            ),
            enabledBorder: OutlineInputBorder(
              borderRadius: BorderRadius.circular(8),
              borderSide: BorderSide(color: AppTheme.primaryColor.withOpacity(0.3)),
            ),
            focusedBorder: OutlineInputBorder(
              borderRadius: BorderRadius.circular(8),
              borderSide: BorderSide(color: AppTheme.primaryColor),
            ),
          ),
          dropdownColor: AppTheme.darkBackground,
          style: const TextStyle(color: Colors.white),
          items: ['BTCUSDT', 'ETHUSDT', 'ADAUSDT', 'DOTUSDT']
              .map((symbol) => DropdownMenuItem(
                    value: symbol,
                    child: Text(symbol),
                  ))
              .toList(),
          onChanged: (value) {
            setState(() {
              _selectedInstrument = value!;
            });
          },
        ),
        const SizedBox(height: 12),
        
        // Quantity Input
        TextFormField(
          controller: _quantityController,
          decoration: InputDecoration(
            labelText: 'Quantity',
            labelStyle: const TextStyle(color: Colors.white70),
            border: OutlineInputBorder(
              borderRadius: BorderRadius.circular(8),
              borderSide: BorderSide(color: AppTheme.primaryColor.withOpacity(0.3)),
            ),
            enabledBorder: OutlineInputBorder(
              borderRadius: BorderRadius.circular(8),
              borderSide: BorderSide(color: AppTheme.primaryColor.withOpacity(0.3)),
            ),
            focusedBorder: OutlineInputBorder(
              borderRadius: BorderRadius.circular(8),
              borderSide: BorderSide(color: AppTheme.primaryColor),
            ),
          ),
          style: const TextStyle(color: Colors.white),
          keyboardType: TextInputType.number,
          validator: (value) {
            if (value == null || value.isEmpty) {
              return 'Please enter quantity';
            }
            if (double.tryParse(value) == null) {
              return 'Please enter a valid number';
            }
            return null;
          },
        ),
        const SizedBox(height: 12),
        
        // Price Input (for limit orders)
        if (_selectedOrderType == 'LIMIT' || _selectedOrderType == 'STOP_LIMIT')
          TextFormField(
            controller: _priceController,
            decoration: InputDecoration(
              labelText: 'Price',
              labelStyle: const TextStyle(color: Colors.white70),
              border: OutlineInputBorder(
                borderRadius: BorderRadius.circular(8),
                borderSide: BorderSide(color: AppTheme.primaryColor.withOpacity(0.3)),
              ),
              enabledBorder: OutlineInputBorder(
                borderRadius: BorderRadius.circular(8),
                borderSide: BorderSide(color: AppTheme.primaryColor.withOpacity(0.3)),
              ),
              focusedBorder: OutlineInputBorder(
                borderRadius: BorderRadius.circular(8),
                borderSide: BorderSide(color: AppTheme.primaryColor),
              ),
            ),
            style: const TextStyle(color: Colors.white),
            keyboardType: TextInputType.number,
            validator: (value) {
              if (_selectedOrderType == 'LIMIT' || _selectedOrderType == 'STOP_LIMIT') {
                if (value == null || value.isEmpty) {
                  return 'Please enter price';
                }
                if (double.tryParse(value) == null) {
                  return 'Please enter a valid number';
                }
              }
              return null;
            },
          ),
      ],
    );
  }

  Widget _buildSideButton(String side, Color color) {
    final isSelected = _selectedSide == side;
    
    return GestureDetector(
      onTap: () {
        setState(() {
          _selectedSide = side;
        });
      },
      child: Container(
        padding: const EdgeInsets.symmetric(vertical: 12),
        decoration: BoxDecoration(
          color: isSelected ? color.withOpacity(0.2) : Colors.transparent,
          borderRadius: BorderRadius.circular(8),
          border: Border.all(
            color: isSelected ? color : color.withOpacity(0.3),
            width: 1,
          ),
        ),
        child: Text(
          side,
          textAlign: TextAlign.center,
          style: TextStyle(
            color: isSelected ? color : color.withOpacity(0.7),
            fontWeight: FontWeight.bold,
            fontSize: 14,
          ),
        ),
      ),
    );
  }

  Widget _buildPlaceOrderButton(TradingProvider provider) {
    return SizedBox(
      width: double.infinity,
      child: ElevatedButton(
        onPressed: provider.isLoading ? null : () => _placeOrder(provider),
        style: ElevatedButton.styleFrom(
          backgroundColor: _selectedSide == 'BUY' ? Colors.green : Colors.red,
          padding: const EdgeInsets.symmetric(vertical: 16),
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(8),
          ),
        ),
        child: provider.isLoading
            ? const SizedBox(
                height: 20,
                width: 20,
                child: CircularProgressIndicator(
                  strokeWidth: 2,
                  valueColor: AlwaysStoppedAnimation<Color>(Colors.white),
                ),
              )
            : Text(
                'Place ${_selectedSide} Order',
                style: const TextStyle(
                  color: Colors.white,
                  fontWeight: FontWeight.bold,
                  fontSize: 16,
                ),
              ),
      ),
    );
  }

  Future<void> _placeOrder(TradingProvider provider) async {
    if (!_formKey.currentState!.validate()) {
      return;
    }

    if (!provider.isWebSocketConnected) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('Cannot place order: Not connected to real-time data'),
          backgroundColor: Colors.red,
        ),
      );
      return;
    }

    try {
      final orderData = {
        'instrument_symbol': _selectedInstrument,
        'side': _selectedSide,
        'order_type': _selectedOrderType,
        'quantity': double.parse(_quantityController.text),
        'price': _priceController.text.isNotEmpty 
            ? double.parse(_priceController.text) 
            : null,
        'time_in_force': 'GTC',
      };

      await provider.placeOrder(orderData, 'dummy_token'); // TODO: Use real token
      
      // Clear form
      _quantityController.clear();
      _priceController.clear();
      
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text('${_selectedSide} order placed successfully!'),
          backgroundColor: Colors.green,
        ),
      );
      
    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text('Failed to place order: $e'),
          backgroundColor: Colors.red,
        ),
      );
    }
  }
}
