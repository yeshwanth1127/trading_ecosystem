import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../../../providers/trading_provider.dart';
import '../../../providers/auth_provider.dart';

enum OrderType {
  market,
  limit,
  stopMarket,
  stopLimit,
}

enum MarginMultiplier {
  x5(5),
  x10(10),
  x25(25),
  x50(50),
  x100(100);

  const MarginMultiplier(this.value);
  final int value;
}

class OrderPlacementPanel extends StatefulWidget {
  final Map<String, dynamic>? balanceSummary;
  
  const OrderPlacementPanel({
    super.key,
    this.balanceSummary,
  });

  @override
  State<OrderPlacementPanel> createState() => _OrderPlacementPanelState();
}

class _OrderPlacementPanelState extends State<OrderPlacementPanel> {
  bool _isLong = true;
  OrderType _selectedOrderType = OrderType.market;
  MarginMultiplier _selectedMargin = MarginMultiplier.x5;
  final TextEditingController _priceController = TextEditingController();
  final TextEditingController _stopPriceController = TextEditingController();
  final TextEditingController _quantityController = TextEditingController();
  
  // Slider state
  double _sliderValue = 0.0;
  double _maxSliderValue = 100.0;
  
  // Available balance from provider
  double get _availableBalance {
    if (widget.balanceSummary != null) {
      return (widget.balanceSummary!['available_balance'] ?? 
              widget.balanceSummary!['balance'] ?? 0.0).toDouble();
    }
    return 0.0;
  }

  @override
  void initState() {
    super.initState();
    _updateMaxSliderValue();
    _quantityController.addListener(_onQuantityChanged);
  }

  @override
  void didUpdateWidget(OrderPlacementPanel oldWidget) {
    super.didUpdateWidget(oldWidget);
    // Update max slider value when balance changes
    if (oldWidget.balanceSummary != widget.balanceSummary) {
      _updateMaxSliderValue();
    }
  }

  @override
  void dispose() {
    _priceController.dispose();
    _stopPriceController.dispose();
    _quantityController.dispose();
    super.dispose();
  }

  void _updateMaxSliderValue() {
    setState(() {
      _maxSliderValue = _availableBalance * _selectedMargin.value;
      print('OrderPlacementPanel: Available Balance: $_availableBalance');
      print('OrderPlacementPanel: Selected Margin: ${_selectedMargin.value}x');
      print('OrderPlacementPanel: Max Slider Value: $_maxSliderValue');
    });
  }

  void _onQuantityChanged() {
    // This prevents infinite loops when slider updates quantity
    if (_quantityController.text.isNotEmpty) {
      final quantity = double.tryParse(_quantityController.text) ?? 0.0;
      if (quantity != _sliderValue) {
        setState(() {
          _sliderValue = quantity.clamp(0.0, _maxSliderValue);
        });
      }
    }
  }

  void _onSliderChanged(double value) {
    setState(() {
      _sliderValue = value;
      _quantityController.text = value.toStringAsFixed(2);
    });
  }

  void _onMarginChanged(MarginMultiplier? newMargin) {
    if (newMargin != null) {
      setState(() {
        _selectedMargin = newMargin;
        _updateMaxSliderValue();
        // Adjust slider value if it exceeds new max
        if (_sliderValue > _maxSliderValue) {
          _sliderValue = _maxSliderValue;
          _quantityController.text = _sliderValue.toStringAsFixed(2);
        }
      });
    }
  }

  // Validation methods
  String? _validateQuantity(String? value) {
    if (value == null || value.isEmpty) {
      return 'Quantity is required';
    }
    
    final quantity = double.tryParse(value);
    if (quantity == null) {
      return 'Invalid quantity format';
    }
    
    if (quantity <= 0) {
      return 'Quantity must be greater than 0';
    }
    
    if (quantity > _maxSliderValue) {
      return 'Quantity cannot exceed ${_maxSliderValue.toStringAsFixed(2)}';
    }
    
    // Check minimum quantity (e.g., 0.01 for most instruments)
    if (quantity < 0.01) {
      return 'Minimum quantity is 0.01';
    }
    
    return null;
  }

  String? _validatePrice(String? value, String fieldName) {
    if (value == null || value.isEmpty) {
      return '$fieldName is required';
    }
    
    final price = double.tryParse(value);
    if (price == null) {
      return 'Invalid $fieldName format';
    }
    
    if (price <= 0) {
      return '$fieldName must be greater than 0';
    }
    
    return null;
  }

  bool _isOrderValid() {
    // Check quantity validation
    final quantityError = _validateQuantity(_quantityController.text);
    if (quantityError != null) return false;
    
    // Check price validation based on order type
    switch (_selectedOrderType) {
      case OrderType.limit:
        final priceError = _validatePrice(_priceController.text, 'Limit Price');
        if (priceError != null) return false;
        break;
      case OrderType.stopMarket:
        final stopPriceError = _validatePrice(_stopPriceController.text, 'Stop Price');
        if (stopPriceError != null) return false;
        break;
      case OrderType.stopLimit:
        final stopPriceError = _validatePrice(_stopPriceController.text, 'Stop Price');
        final limitPriceError = _validatePrice(_priceController.text, 'Limit Price');
        if (stopPriceError != null || limitPriceError != null) return false;
        break;
      case OrderType.market:
        // Market orders don't need price validation
        break;
    }
    
    // Check if user has sufficient balance
    final quantity = double.tryParse(_quantityController.text) ?? 0.0;
    final marginRequired = quantity / _selectedMargin.value;
    if (marginRequired > _availableBalance) {
      return false;
    }
    
    return true;
  }

  String? _getValidationError() {
    // Check quantity validation
    final quantityError = _validateQuantity(_quantityController.text);
    if (quantityError != null) return quantityError;
    
    // Check price validation based on order type
    switch (_selectedOrderType) {
      case OrderType.limit:
        return _validatePrice(_priceController.text, 'Limit Price');
      case OrderType.stopMarket:
        return _validatePrice(_stopPriceController.text, 'Stop Price');
      case OrderType.stopLimit:
        final stopPriceError = _validatePrice(_stopPriceController.text, 'Stop Price');
        if (stopPriceError != null) return stopPriceError;
        return _validatePrice(_priceController.text, 'Limit Price');
      case OrderType.market:
        break;
    }
    
    // Check if user has sufficient balance
    final quantity = double.tryParse(_quantityController.text) ?? 0.0;
    final marginRequired = quantity / _selectedMargin.value;
    if (marginRequired > _availableBalance) {
      return 'Insufficient balance. Required: ${marginRequired.toStringAsFixed(2)}, Available: ${_availableBalance.toStringAsFixed(2)}';
    }
    
    return null;
  }

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            const Text(
              'Place Order',
              style: TextStyle(
                color: Colors.white,
                fontSize: 16,
                fontWeight: FontWeight.bold,
              ),
            ),
            // Real-time connection indicator
            Consumer<TradingProvider>(
              builder: (context, tradingProvider, child) {
                return Row(
                  mainAxisSize: MainAxisSize.min,
                  children: [
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
                    const SizedBox(width: 4),
                    Text(
                      tradingProvider.isWebSocketConnected ? 'LIVE' : 'OFFLINE',
                      style: TextStyle(
                        color: tradingProvider.isWebSocketConnected 
                            ? Colors.green 
                            : Colors.red,
                        fontSize: 10,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                  ],
                );
              },
            ),
          ],
        ),
        const SizedBox(height: 16),
        
        // Long/Short Toggle
        _buildLongShortToggle(),
        const SizedBox(height: 16),
        
        // Order Type Dropdown
        _buildOrderTypeDropdown(),
        const SizedBox(height: 16),
        
        // Conditional Fields based on Order Type
        _buildConditionalFields(),
        const SizedBox(height: 16),
        
        // Margin Selection
        _buildMarginSelection(),
        const SizedBox(height: 16),
        
        // Quantity Slider
        _buildQuantitySlider(),
        const SizedBox(height: 12),
        
        // Quantity Input
        _buildQuantityInput(),
        const SizedBox(height: 12),
        
        // Margin Requirement Display
        _buildMarginRequirement(),
        const SizedBox(height: 20),
        
        // Buy/Sell Button
        _buildOrderButton(),
      ],
    );
  }

  Widget _buildLongShortToggle() {
    return Container(
      decoration: BoxDecoration(
        color: const Color(0xFF2a2a2a),
        borderRadius: BorderRadius.circular(8),
        border: Border.all(color: const Color(0xFF333333), width: 1),
      ),
      child: Row(
        children: [
          Expanded(
            child: GestureDetector(
              onTap: () => setState(() => _isLong = true),
              child: Container(
                padding: const EdgeInsets.symmetric(vertical: 12),
                decoration: BoxDecoration(
                  color: _isLong ? Colors.green : Colors.transparent,
                  borderRadius: const BorderRadius.only(
                    topLeft: Radius.circular(8),
                    bottomLeft: Radius.circular(8),
                  ),
                ),
                child: Text(
                  'LONG',
                  textAlign: TextAlign.center,
                  style: TextStyle(
                    color: _isLong ? Colors.white : Colors.grey,
                    fontSize: 14,
                    fontWeight: FontWeight.bold,
                  ),
                ),
              ),
            ),
          ),
          Expanded(
            child: GestureDetector(
              onTap: () => setState(() => _isLong = false),
              child: Container(
                padding: const EdgeInsets.symmetric(vertical: 12),
                decoration: BoxDecoration(
                  color: !_isLong ? Colors.red : Colors.transparent,
                  borderRadius: const BorderRadius.only(
                    topRight: Radius.circular(8),
                    bottomRight: Radius.circular(8),
                  ),
                ),
                child: Text(
                  'SHORT',
                  textAlign: TextAlign.center,
                  style: TextStyle(
                    color: !_isLong ? Colors.white : Colors.grey,
                    fontSize: 14,
                    fontWeight: FontWeight.bold,
                  ),
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildMarginSelection() {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const Text(
          'Margin',
          style: TextStyle(
            color: Colors.grey,
            fontSize: 12,
            fontWeight: FontWeight.w500,
          ),
        ),
        const SizedBox(height: 4),
        Container(
          decoration: BoxDecoration(
            color: const Color(0xFF2a2a2a),
            borderRadius: BorderRadius.circular(8),
            border: Border.all(color: const Color(0xFF333333), width: 1),
          ),
          child: DropdownButtonHideUnderline(
            child: DropdownButton<MarginMultiplier>(
              value: _selectedMargin,
              isExpanded: true,
              dropdownColor: const Color(0xFF2a2a2a),
              style: const TextStyle(color: Colors.white),
              icon: const Icon(Icons.arrow_drop_down, color: Colors.white),
              onChanged: _onMarginChanged,
              items: MarginMultiplier.values.map<DropdownMenuItem<MarginMultiplier>>((MarginMultiplier margin) {
                return DropdownMenuItem<MarginMultiplier>(
                  value: margin,
                  child: Padding(
                    padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
                    child: Text(
                      '${margin.value}x',
                      style: const TextStyle(
                        color: Colors.white,
                        fontSize: 14,
                        fontWeight: FontWeight.w500,
                      ),
                    ),
                  ),
                );
              }).toList(),
            ),
          ),
        ),
        const SizedBox(height: 4),
        Text(
          _availableBalance > 0 
            ? 'Max Position: ${_maxSliderValue.toStringAsFixed(2)}'
            : 'No balance available',
          style: TextStyle(
            color: _availableBalance > 0 ? Colors.grey : Colors.red,
            fontSize: 10,
          ),
        ),
      ],
    );
  }

  Widget _buildQuantitySlider() {
    final isDisabled = _availableBalance <= 0;
    // Use a fixed width that works well within the panel
    const double sliderTrackWidth = 250.0; // Fixed width for the slider track
    const double handleRadius = 15.0; // Half of handle width (30/2)
    
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            const Text(
              'Position Size',
              style: TextStyle(
                color: Colors.grey,
                fontSize: 12,
                fontWeight: FontWeight.w500,
              ),
            ),
            Text(
              '${_sliderValue.toStringAsFixed(2)}',
              style: const TextStyle(
                color: Colors.white,
                fontSize: 12,
                fontWeight: FontWeight.bold,
              ),
            ),
          ],
        ),
        const SizedBox(height: 8),
        
        // Slider Container with fixed width
        Center(
          child: Container(
            width: sliderTrackWidth,
            height: 40,
            decoration: BoxDecoration(
              color: isDisabled ? const Color(0xFF0a0a0a) : const Color(0xFF1a1a1a),
              borderRadius: BorderRadius.circular(20),
              border: Border.all(
                color: isDisabled ? const Color(0xFF222222) : const Color(0xFF333333), 
                width: 1
              ),
            ),
            child: Stack(
              children: [
                // Background track
                Container(
                  height: 40,
                  decoration: BoxDecoration(
                    borderRadius: BorderRadius.circular(20),
                    gradient: LinearGradient(
                      colors: [
                        Colors.grey.withOpacity(0.3),
                        Colors.grey.withOpacity(0.1),
                      ],
                      stops: const [0.0, 1.0],
                    ),
                  ),
                ),
                
                // Active track
                if (!isDisabled)
                  Container(
                    height: 40,
                    width: _maxSliderValue > 0 
                      ? (_sliderValue / _maxSliderValue) * sliderTrackWidth
                      : 0,
                    decoration: BoxDecoration(
                      borderRadius: BorderRadius.circular(20),
                      gradient: LinearGradient(
                        colors: _isLong 
                            ? [Colors.green.withOpacity(0.8), Colors.green.withOpacity(0.4)]
                            : [Colors.red.withOpacity(0.8), Colors.red.withOpacity(0.4)],
                        stops: const [0.0, 1.0],
                      ),
                    ),
                  ),
                
                // Slider Handle
                if (!isDisabled)
                  Positioned(
                    left: _maxSliderValue > 0 
                      ? (_sliderValue / _maxSliderValue) * sliderTrackWidth - handleRadius
                      : -handleRadius,
                    top: 0,
                    child: GestureDetector(
                      onPanUpdate: (details) {
                        final RenderBox box = context.findRenderObject() as RenderBox;
                        final localPosition = box.globalToLocal(details.globalPosition);
                        
                        // Clamp the position to stay within slider bounds
                        final clampedX = localPosition.dx.clamp(handleRadius, sliderTrackWidth - handleRadius);
                        final newValue = ((clampedX - handleRadius) / (sliderTrackWidth - (2 * handleRadius)) * _maxSliderValue).clamp(0.0, _maxSliderValue);
                        _onSliderChanged(newValue);
                      },
                      child: Container(
                        width: 30,
                        height: 40,
                        decoration: BoxDecoration(
                          color: _isLong ? Colors.green : Colors.red,
                          borderRadius: BorderRadius.circular(15),
                          border: Border.all(color: Colors.white, width: 2),
                          boxShadow: [
                            BoxShadow(
                              color: (_isLong ? Colors.green : Colors.red).withOpacity(0.5),
                              blurRadius: 8,
                              spreadRadius: 2,
                            ),
                          ],
                        ),
                        child: const Icon(
                          Icons.drag_indicator,
                          color: Colors.white,
                          size: 16,
                        ),
                      ),
                    ),
                  ),
              ],
            ),
          ),
        ),
        const SizedBox(height: 4),
        Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            Text(
              '0',
              style: const TextStyle(
                color: Colors.grey,
                fontSize: 10,
              ),
            ),
            Text(
              '${_maxSliderValue.toStringAsFixed(0)}',
              style: const TextStyle(
                color: Colors.grey,
                fontSize: 10,
              ),
            ),
          ],
        ),
      ],
    );
  }

  Widget _buildOrderTypeDropdown() {
    return Container(
      decoration: BoxDecoration(
        color: const Color(0xFF2a2a2a),
        borderRadius: BorderRadius.circular(8),
        border: Border.all(color: const Color(0xFF333333), width: 1),
      ),
      child: DropdownButtonHideUnderline(
        child: DropdownButton<OrderType>(
          value: _selectedOrderType,
          isExpanded: true,
          dropdownColor: const Color(0xFF2a2a2a),
          style: const TextStyle(color: Colors.white),
          icon: const Icon(Icons.arrow_drop_down, color: Colors.white),
          onChanged: (OrderType? newValue) {
            if (newValue != null) {
              setState(() {
                _selectedOrderType = newValue;
                // Clear fields when order type changes
                _priceController.clear();
                _stopPriceController.clear();
              });
            }
          },
          items: OrderType.values.map<DropdownMenuItem<OrderType>>((OrderType type) {
            String label;
            switch (type) {
              case OrderType.market:
                label = 'Market Order';
                break;
              case OrderType.limit:
                label = 'Limit Order';
                break;
              case OrderType.stopMarket:
                label = 'Stop Market';
                break;
              case OrderType.stopLimit:
                label = 'Stop Limit';
                break;
            }
            return DropdownMenuItem<OrderType>(
              value: type,
              child: Padding(
                padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
                child: Text(
                  label,
                  style: const TextStyle(
                    color: Colors.white,
                    fontSize: 14,
                  ),
                ),
              ),
            );
          }).toList(),
        ),
      ),
    );
  }

  Widget _buildConditionalFields() {
    switch (_selectedOrderType) {
      case OrderType.market:
        return const SizedBox.shrink(); // No additional fields for market orders
      
      case OrderType.limit:
        return _buildPriceInput('Limit Price', _priceController);
      
      case OrderType.stopMarket:
        return _buildPriceInput('Stop Price', _stopPriceController);
      
      case OrderType.stopLimit:
        return Column(
          children: [
            _buildPriceInput('Stop Price', _stopPriceController),
            const SizedBox(height: 12),
            _buildPriceInput('Limit Price', _priceController),
          ],
        );
    }
  }

  Widget _buildPriceInput(String label, TextEditingController controller) {
    final priceError = _validatePrice(controller.text, label);
    final hasError = priceError != null && controller.text.isNotEmpty;
    
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          label,
          style: const TextStyle(
            color: Colors.grey,
            fontSize: 12,
            fontWeight: FontWeight.w500,
          ),
        ),
        const SizedBox(height: 4),
        Container(
          decoration: BoxDecoration(
            color: const Color(0xFF2a2a2a),
            borderRadius: BorderRadius.circular(8),
            border: Border.all(
              color: hasError ? Colors.red : const Color(0xFF333333), 
              width: 1
            ),
          ),
          child: TextField(
            controller: controller,
            style: const TextStyle(color: Colors.white),
            keyboardType: const TextInputType.numberWithOptions(decimal: true),
            decoration: const InputDecoration(
              border: InputBorder.none,
              contentPadding: EdgeInsets.symmetric(horizontal: 12, vertical: 12),
              hintText: '0.00',
              hintStyle: TextStyle(color: Colors.grey),
            ),
          ),
        ),
        if (hasError) ...[
          const SizedBox(height: 4),
          Text(
            priceError,
            style: const TextStyle(
              color: Colors.red,
              fontSize: 10,
            ),
          ),
        ],
      ],
    );
  }

  Widget _buildMarginRequirement() {
    final quantity = double.tryParse(_quantityController.text) ?? 0.0;
    final marginRequired = quantity / _selectedMargin.value;
    final isInsufficient = marginRequired > _availableBalance;
    
    return Container(
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: isInsufficient 
          ? Colors.red.withOpacity(0.1)
          : Colors.blue.withOpacity(0.1),
        borderRadius: BorderRadius.circular(8),
        border: Border.all(
          color: isInsufficient 
            ? Colors.red.withOpacity(0.3)
            : Colors.blue.withOpacity(0.3),
          width: 1,
        ),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Icon(
                isInsufficient ? Icons.warning : Icons.info_outline,
                color: isInsufficient ? Colors.red : Colors.blue,
                size: 16,
              ),
              const SizedBox(width: 8),
              Text(
                'Margin Requirement',
                style: TextStyle(
                  color: isInsufficient ? Colors.red : Colors.blue,
                  fontSize: 12,
                  fontWeight: FontWeight.bold,
                ),
              ),
            ],
          ),
          const SizedBox(height: 8),
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              const Text(
                'Required:',
                style: TextStyle(
                  color: Colors.grey,
                  fontSize: 11,
                ),
              ),
              Text(
                '${marginRequired.toStringAsFixed(2)}',
                style: TextStyle(
                  color: isInsufficient ? Colors.red : Colors.white,
                  fontSize: 11,
                  fontWeight: FontWeight.bold,
                ),
              ),
            ],
          ),
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              const Text(
                'Available:',
                style: TextStyle(
                  color: Colors.grey,
                  fontSize: 11,
                ),
              ),
              Text(
                '${_availableBalance.toStringAsFixed(2)}',
                style: const TextStyle(
                  color: Colors.white,
                  fontSize: 11,
                  fontWeight: FontWeight.bold,
                ),
              ),
            ],
          ),
          if (isInsufficient) ...[
            const SizedBox(height: 4),
            Text(
              'Insufficient balance for this position',
              style: const TextStyle(
                color: Colors.red,
                fontSize: 10,
                fontStyle: FontStyle.italic,
              ),
            ),
          ],
        ],
      ),
    );
  }

  Widget _buildQuantityInput() {
    final quantityError = _validateQuantity(_quantityController.text);
    final hasError = quantityError != null && _quantityController.text.isNotEmpty;
    
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const Text(
          'Quantity',
          style: TextStyle(
            color: Colors.grey,
            fontSize: 12,
            fontWeight: FontWeight.w500,
          ),
        ),
        const SizedBox(height: 4),
        Container(
          decoration: BoxDecoration(
            color: const Color(0xFF2a2a2a),
            borderRadius: BorderRadius.circular(8),
            border: Border.all(
              color: hasError ? Colors.red : const Color(0xFF333333), 
              width: 1
            ),
          ),
          child: TextField(
            controller: _quantityController,
            style: const TextStyle(color: Colors.white),
            keyboardType: const TextInputType.numberWithOptions(decimal: true),
            onChanged: (value) {
              setState(() {
                // Update slider when quantity is manually entered
                final quantity = double.tryParse(value) ?? 0.0;
                _sliderValue = quantity.clamp(0.0, _maxSliderValue);
              });
            },
            decoration: InputDecoration(
              border: InputBorder.none,
              contentPadding: const EdgeInsets.symmetric(horizontal: 12, vertical: 12),
              hintText: '0',
              hintStyle: const TextStyle(color: Colors.grey),
              suffixText: _availableBalance > 0 
                ? 'Max: ${_maxSliderValue.toStringAsFixed(0)}'
                : null,
              suffixStyle: const TextStyle(
                color: Colors.grey,
                fontSize: 10,
              ),
            ),
          ),
        ),
        if (hasError) ...[
          const SizedBox(height: 4),
          Text(
            quantityError,
            style: const TextStyle(
              color: Colors.red,
              fontSize: 10,
            ),
          ),
        ],
      ],
    );
  }

  Widget _buildOrderButton() {
    final buttonText = _isLong ? 'BUY' : 'SELL';
    final buttonColor = _isLong ? Colors.green : Colors.red;
    final isOrderValid = _isOrderValid();
    final validationError = _getValidationError();
    
    return Column(
      children: [
        // Validation error message
        if (validationError != null) ...[
          Container(
            width: double.infinity,
            padding: const EdgeInsets.all(12),
            margin: const EdgeInsets.only(bottom: 12),
            decoration: BoxDecoration(
              color: Colors.red.withOpacity(0.1),
              borderRadius: BorderRadius.circular(8),
              border: Border.all(color: Colors.red.withOpacity(0.3), width: 1),
            ),
            child: Row(
              children: [
                const Icon(
                  Icons.error_outline,
                  color: Colors.red,
                  size: 16,
                ),
                const SizedBox(width: 8),
                Expanded(
                  child: Text(
                    validationError,
                    style: const TextStyle(
                      color: Colors.red,
                      fontSize: 12,
                    ),
                  ),
                ),
              ],
            ),
          ),
        ],
        
        // Order button
        Consumer<TradingProvider>(
          builder: (context, tradingProvider, child) {
            final isLoading = tradingProvider.isLoading;
            final isConnected = tradingProvider.isWebSocketConnected;
            
            return SizedBox(
              width: double.infinity,
              child: ElevatedButton(
                onPressed: (isOrderValid && !isLoading && isConnected) ? () {
                  _placeOrder(tradingProvider);
                } : null,
                style: ElevatedButton.styleFrom(
                  backgroundColor: (isOrderValid && !isLoading && isConnected) 
                      ? buttonColor 
                      : Colors.grey,
                  foregroundColor: Colors.white,
                  padding: const EdgeInsets.symmetric(vertical: 16),
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(8),
                  ),
                  elevation: 0,
                ),
                child: isLoading
                    ? const SizedBox(
                        height: 20,
                        width: 20,
                        child: CircularProgressIndicator(
                          strokeWidth: 2,
                          valueColor: AlwaysStoppedAnimation<Color>(Colors.white),
                        ),
                      )
                    : Text(
                        !isConnected 
                            ? 'OFFLINE' 
                            : isOrderValid 
                                ? buttonText 
                                : 'Invalid Order',
                        style: const TextStyle(
                          fontSize: 16,
                          fontWeight: FontWeight.bold,
                          letterSpacing: 1,
                        ),
                      ),
              ),
            );
          },
        ),
      ],
    );
  }

  Future<void> _placeOrder(TradingProvider tradingProvider) async {
    try {
      // Get auth token
      final authProvider = context.read<AuthProvider>();
      if (!authProvider.isAuthenticated || authProvider.token == null) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text('Please login to place orders'),
            backgroundColor: Colors.red,
          ),
        );
        return;
      }

      // Prepare order data
      final orderData = {
        'instrument_symbol': 'BTCUSDT', // TODO: Get from selected instrument
        'side': _isLong ? 'buy' : 'sell',
        'order_type': _getOrderTypeString(),
        'quantity': double.parse(_quantityController.text),
        'leverage': _selectedMargin.value.toDouble(),
        'is_margin_order': _selectedMargin.value > 1.0,
      };

      // Add price fields based on order type
      switch (_selectedOrderType) {
        case OrderType.limit:
          if (_priceController.text.isNotEmpty) {
            orderData['price'] = double.parse(_priceController.text);
          }
          break;
        case OrderType.stopMarket:
          if (_stopPriceController.text.isNotEmpty) {
            orderData['stop_price'] = double.parse(_stopPriceController.text);
          }
          break;
        case OrderType.stopLimit:
          if (_priceController.text.isNotEmpty) {
            orderData['price'] = double.parse(_priceController.text);
          }
          if (_stopPriceController.text.isNotEmpty) {
            orderData['stop_price'] = double.parse(_stopPriceController.text);
          }
          break;
        case OrderType.market:
          // Market orders don't need price
          break;
      }

      // Place order through TradingProvider
      await tradingProvider.placeOrder(orderData, authProvider.token!);
      
      // Show success message
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text('${_isLong ? 'BUY' : 'SELL'} order placed successfully!'),
          backgroundColor: _isLong ? Colors.green : Colors.red,
          duration: const Duration(seconds: 2),
        ),
      );
      
      // Clear form after successful order placement
      setState(() {
        _sliderValue = 0.0;
        _quantityController.clear();
        _priceController.clear();
        _stopPriceController.clear();
      });
      
    } catch (e) {
      // Show error message
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text('Failed to place order: $e'),
          backgroundColor: Colors.red,
          duration: const Duration(seconds: 3),
        ),
      );
    }
  }

  String _getOrderTypeString() {
    switch (_selectedOrderType) {
      case OrderType.market:
        return 'market';
      case OrderType.limit:
        return 'limit';
      case OrderType.stopMarket:
        return 'stop';
      case OrderType.stopLimit:
        return 'stop_limit';
    }
  }
}
