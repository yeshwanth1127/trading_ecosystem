import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../../providers/trading_provider.dart';
import '../../providers/auth_provider.dart';
import '../../widgets/trading_view_chart.dart';
import '../../widgets/timeframe_selector.dart';
import 'widgets/positions_panel.dart';
import 'widgets/order_panel.dart';
import 'widgets/balance_panel.dart';
import 'widgets/balance_summary_panel.dart';

class TradingScreen extends StatefulWidget {
  const TradingScreen({Key? key}) : super(key: key);

  @override
  State<TradingScreen> createState() => _TradingScreenState();
}

class _TradingScreenState extends State<TradingScreen> {
  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      _loadInitialData();
    });
  }

  Future<void> _loadInitialData() async {
    final tradingProvider = context.read<TradingProvider>();
    final authProvider = context.read<AuthProvider>();
    
    print('TradingScreen: Loading initial data...');
    
    // Wait for AuthProvider to initialize
    await authProvider.waitForInitialization();
    
    print('TradingScreen: Auth status - isAuthenticated: ${authProvider.isAuthenticated}, token: ${authProvider.token != null}');
    
    if (authProvider.isAuthenticated && authProvider.token != null) {
      print('TradingScreen: User is authenticated, loading full data...');
      // Load initial data with WebSocket connection
      await tradingProvider.loadInitialData(userId: authProvider.user?['id']);
      print('TradingScreen: Initial data loaded, now loading balance...');
      // Load balance for the current user's active challenge
      await tradingProvider.loadUserBalance();
      print('TradingScreen: Balance loaded successfully');
    } else {
      print('TradingScreen: User not authenticated, loading public data only...');
      // Load only public data
      await tradingProvider.loadInstruments();
      await tradingProvider.loadMarketData();
    }
  }

  @override
  Widget build(BuildContext context) {
    final screenSize = MediaQuery.of(context).size;
    final isMobile = screenSize.width < 600;
    
    return Scaffold(
      backgroundColor: const Color(0xFF0E1116),
      appBar: AppBar(
        backgroundColor: const Color(0xFF1E222D),
        foregroundColor: Colors.white,
        title: const Text(
          'Trading Dashboard',
          style: TextStyle(
            color: Colors.white,
            fontWeight: FontWeight.w600,
          ),
        ),
        actions: [
          // Real-time connection indicator
          Consumer<TradingProvider>(
            builder: (context, tradingProvider, child) {
              return Container(
                margin: const EdgeInsets.only(right: 8),
                padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                decoration: BoxDecoration(
                  color: tradingProvider.isWebSocketConnected 
                      ? Colors.green.withOpacity(0.2) 
                      : Colors.red.withOpacity(0.2),
                  borderRadius: BorderRadius.circular(12),
                  border: Border.all(
                    color: tradingProvider.isWebSocketConnected 
                        ? Colors.green 
                        : Colors.red,
                    width: 1,
                  ),
                ),
                child: Row(
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
                ),
              );
            },
          ),
          IconButton(
            onPressed: () => Navigator.pushNamed(context, '/account'),
            icon: const Icon(Icons.account_circle),
            tooltip: 'Account Details',
          ),
          IconButton(
            onPressed: _loadInitialData,
            icon: const Icon(Icons.refresh),
            tooltip: 'Refresh Data',
          ),
        ],
      ),
      body: SafeArea(
        child: isMobile ? _buildMobileLayout() : _buildDesktopLayout(),
      ),
    );
  }
  
  Widget _buildMobileLayout() {
    return SingleChildScrollView(
      child: Column(
        children: [
          // Balance Summary (collapsible)
          ExpansionTile(
            title: const Text('Account Summary', style: TextStyle(color: Colors.white)),
            backgroundColor: const Color(0xFF1E222D),
            children: [
              SizedBox(
                height: 200,
                child: const BalanceSummaryPanel(),
              ),
            ],
          ),
          
          // Chart Area
          Container(
            height: 400, // Fixed height for chart
            margin: const EdgeInsets.all(8),
            decoration: BoxDecoration(
              color: const Color(0xFF1E222D),
              borderRadius: BorderRadius.circular(8),
              border: Border.all(
                color: const Color(0xFF2A2E39),
                width: 1,
              ),
            ),
            child: Column(
              children: [
                // Timeframe Selector
                Container(
                  padding: const EdgeInsets.all(8),
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
                      const Text(
                        'Timeframe:',
                        style: TextStyle(
                          color: Colors.white,
                          fontSize: 12,
                          fontWeight: FontWeight.w500,
                        ),
                      ),
                      const SizedBox(width: 8),
                      Expanded(
                        child: Consumer<TradingProvider>(
                          builder: (context, tradingProvider, child) {
                            return TimeframeSelector(
                              selectedInterval: tradingProvider.selectedInterval,
                              onIntervalChanged: (interval) {
                                tradingProvider.setInterval(interval);
                              },
                            );
                          },
                        ),
                      ),
                    ],
                  ),
                ),
                
                // TradingView Chart
                Expanded(
                  child: Consumer<TradingProvider>(
                    builder: (context, tradingProvider, child) {
                      return TradingViewChart(
                        symbol: tradingProvider.selectedTvSymbol,
                        interval: tradingProvider.selectedInterval,
                      );
                    },
                  ),
                ),
              ],
            ),
          ),
          
          // Bottom Panels (expandable, no fixed height)
          Padding(
            padding: const EdgeInsets.all(8.0),
            child: Column(
              children: [
                // Open Positions
                Consumer<TradingProvider>(
                  builder: (context, tradingProvider, child) {
                    return PositionsPanel(
                      title: 'Open Positions',
                      positions: tradingProvider.getOpenPositions(),
                      type: 'open',
                      currency: tradingProvider.currency,
                      totalBalance: tradingProvider.totalEquity,
                    );
                  },
                ),
                
                const SizedBox(height: 8),
                
                // Pending Orders
                Consumer<TradingProvider>(
                  builder: (context, tradingProvider, child) {
                    return OrderPanel(
                      title: 'Pending Orders',
                      orders: tradingProvider.getPendingOrders(),
                    );
                  },
                ),
                
                const SizedBox(height: 8),
                
                // Closed Positions
                Consumer<TradingProvider>(
                  builder: (context, tradingProvider, child) {
                    return PositionsPanel(
                      title: 'Closed Positions',
                      positions: tradingProvider.getClosedPositions(),
                      type: 'closed',
                      currency: tradingProvider.currency,
                      totalBalance: tradingProvider.totalEquity,
                    );
                  },
                ),
                
                const SizedBox(height: 8),
                
                // Balance Panel
                Consumer<TradingProvider>(
                  builder: (context, tradingProvider, child) {
                    return BalancePanel(
                      summary: tradingProvider.dashboardSummary ?? {},
                      isCompact: true,
                    );
                  },
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
  
  Widget _buildDesktopLayout() {
    return Row(
      children: [
        // Left Panel - Balance Summary
        Container(
          width: 300,
          color: const Color(0xFF1E222D),
          child: const BalanceSummaryPanel(),
        ),
        
        // Center Panel - Chart and Panels
        Expanded(
          child: SingleChildScrollView(
            child: Column(
              children: [
                // Chart Area with Timeframe Selector
                Container(
                  height: 500, // Fixed height for chart
                  margin: const EdgeInsets.all(16),
                  decoration: BoxDecoration(
                    color: const Color(0xFF1E222D),
                    borderRadius: BorderRadius.circular(8),
                    border: Border.all(
                      color: const Color(0xFF2A2E39),
                      width: 1,
                    ),
                  ),
                  child: Column(
                    children: [
                      // Timeframe Selector
                      Container(
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
                            const Text(
                              'Timeframe:',
                              style: TextStyle(
                                color: Colors.white,
                                fontSize: 14,
                                fontWeight: FontWeight.w500,
                              ),
                            ),
                            const SizedBox(width: 16),
                            Expanded(
                              child: Consumer<TradingProvider>(
                                builder: (context, tradingProvider, child) {
                                  return TimeframeSelector(
                                    selectedInterval: tradingProvider.selectedInterval,
                                    onIntervalChanged: (interval) {
                                      tradingProvider.setInterval(interval);
                                    },
                                  );
                                },
                              ),
                            ),
                          ],
                        ),
                      ),
                      
                      // TradingView Chart
                      Expanded(
                        child: Consumer<TradingProvider>(
                          builder: (context, tradingProvider, child) {
                            return TradingViewChart(
                              symbol: tradingProvider.selectedTvSymbol,
                              interval: tradingProvider.selectedInterval,
                            );
                          },
                        ),
                      ),
                    ],
                  ),
                ),
                
                // Bottom Panels (expandable, no fixed height)
                Padding(
                  padding: const EdgeInsets.all(16.0),
                  child: Column(
                    children: [
                      // Open Positions
                      Consumer<TradingProvider>(
                        builder: (context, tradingProvider, child) {
                          return PositionsPanel(
                            title: 'Open Positions',
                            positions: tradingProvider.getOpenPositions(),
                            type: 'open',
                            currency: tradingProvider.currency,
                            totalBalance: tradingProvider.totalEquity,
                          );
                        },
                      ),
                      
                      const SizedBox(height: 16),
                      
                      // Pending Orders
                      Consumer<TradingProvider>(
                        builder: (context, tradingProvider, child) {
                          return OrderPanel(
                            title: 'Pending Orders',
                            orders: tradingProvider.getPendingOrders(),
                          );
                        },
                      ),
                      
                      const SizedBox(height: 16),
                      
                      // Closed Positions
                      Consumer<TradingProvider>(
                        builder: (context, tradingProvider, child) {
                          return PositionsPanel(
                            title: 'Closed Positions',
                            positions: tradingProvider.getClosedPositions(),
                            type: 'closed',
                            currency: tradingProvider.currency,
                            totalBalance: tradingProvider.totalEquity,
                          );
                        },
                      ),
                    ],
                  ),
                ),
              ],
            ),
          ),
        ),
        
        // Right Panel - Balance
        Container(
          width: 300,
          color: const Color(0xFF1E222D),
          child: Consumer<TradingProvider>(
            builder: (context, tradingProvider, child) {
              return BalancePanel(
                summary: tradingProvider.dashboardSummary ?? {},
              );
            },
          ),
        ),
      ],
    );
  }
}
