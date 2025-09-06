import 'package:flutter/material.dart';
import 'package:flutter/foundation.dart';
import 'package:flutter_inappwebview/flutter_inappwebview.dart';

class TradingViewChart extends StatefulWidget {
  final String symbol;
  final String interval;
  final String theme;

  const TradingViewChart({
    Key? key,
    required this.symbol,
    this.interval = '1D',
    this.theme = 'dark',
  }) : super(key: key);

  @override
  State<TradingViewChart> createState() => _TradingViewChartState();
}

class _TradingViewChartState extends State<TradingViewChart> {
  InAppWebViewController? _controller;
  bool _isLoading = true;
  bool _hasError = false;

  @override
  void initState() {
    super.initState();
    print('TradingViewChart: Initializing for ${widget.symbol} with interval ${widget.interval}');
    
    // Auto-hide loading after 10 seconds
    Future.delayed(const Duration(seconds: 10), () {
      if (mounted && _isLoading) {
        setState(() {
          _isLoading = false;
        });
        print('TradingViewChart: Auto-hiding loading spinner after timeout');
      }
    });
  }

  String _getChartHtml() {
    return '''
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>TradingView Chart</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        html, body {
            width: 100%;
            height: 100%;
            background-color: #131722;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            overflow: hidden;
        }
        
        #tradingview_widget {
            width: 100%;
            height: 100%;
        }
        
        .loading {
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            color: #ffffff;
            font-size: 14px;
            text-align: center;
        }
    </style>
</head>
<body>
    <div id="tradingview_widget">
        <div class="loading">Loading TradingView chart...</div>
    </div>
    
    <script type="text/javascript" src="https://s3.tradingview.com/tv.js"></script>
    <script type="text/javascript">
        console.log('TradingView script loaded');
        
        function initChart() {
            try {
                console.log('Initializing TradingView widget for ${widget.symbol}');
                
                // Remove loading message
                const loadingEl = document.querySelector('.loading');
                if (loadingEl) {
                    loadingEl.remove();
                }
                
                new TradingView.widget({
                    "width": "100%",
                    "height": "100%",
                    "symbol": "${widget.symbol}",
                    "interval": "${widget.interval}",
                    "timezone": "Asia/Kolkata",
                    "theme": "${widget.theme}",
                    "style": "1",
                    "locale": "en",
                    "toolbar_bg": "#f1f3f6",
                    "enable_publishing": false,
                    "hide_side_toolbar": false,
                    "allow_symbol_change": true,
                    "container_id": "tradingview_widget",
                    "studies": [
                        "RSI@tv-basicstudies",
                        "MACD@tv-basicstudies"
                    ],
                    "show_popup_button": true,
                    "popup_width": "1000",
                    "popup_height": "650"
                });
                
                console.log('TradingView widget initialized successfully');
                
                // Notify Flutter that chart is ready
                if (window.flutter_inappwebview) {
                    window.flutter_inappwebview.callHandler('onChartReady');
                }
                
            } catch (error) {
                console.error('Error initializing TradingView widget:', error);
                showError('Failed to initialize chart: ' + error.message);
            }
        }
        
        function showError(message) {
            const container = document.getElementById('tradingview_widget');
            if (container) {
                container.innerHTML = '<div style="color: #ff6b6b; text-align: center; padding: 20px;">' + message + '<br><button onclick="location.reload()">Retry</button></div>';
            }
        }
        
        // Wait for TradingView to load
        if (typeof TradingView !== 'undefined') {
            initChart();
        } else {
            // If TradingView is not loaded yet, wait for it
            window.addEventListener('load', function() {
                setTimeout(initChart, 2000);
            });
        }
    </script>
</body>
</html>
    ''';
  }

  @override
  Widget build(BuildContext context) {
    return Container(
      width: double.infinity,
      height: double.infinity,
      decoration: BoxDecoration(
        color: const Color(0xFF131722),
        borderRadius: BorderRadius.circular(4),
      ),
      child: Stack(
        children: [
          InAppWebView(
            initialData: InAppWebViewInitialData(
              data: _getChartHtml(),
              mimeType: 'text/html',
              encoding: 'utf-8',
            ),
            initialSettings: InAppWebViewSettings(
              javaScriptEnabled: true,
              mediaPlaybackRequiresUserGesture: false,
              allowsInlineMediaPlayback: true,
              transparentBackground: true,
              useWideViewPort: true,
              loadWithOverviewMode: true,
              domStorageEnabled: true,
              databaseEnabled: true,
              clearCache: false,
              cacheEnabled: true,
              javaScriptCanOpenWindowsAutomatically: false,
              supportZoom: false,
              displayZoomControls: false,
              builtInZoomControls: false,
              verticalScrollBarEnabled: false,
              horizontalScrollBarEnabled: false,
            ),
            onWebViewCreated: (controller) {
              _controller = controller;
              print('TradingViewChart: WebView created');
              
              // Add JavaScript handler for chart ready (only on non-web platforms)
              if (!kIsWeb) {
                controller.addJavaScriptHandler(
                  handlerName: 'onChartReady',
                  callback: (args) {
                    print('TradingViewChart: Chart ready callback received');
                    if (mounted) {
                      setState(() {
                        _isLoading = false;
                      });
                    }
                  },
                );
              }
            },
            onLoadStart: (controller, url) {
              setState(() {
                _isLoading = true;
                _hasError = false;
              });
              print('TradingViewChart: Load started');
            },
            onLoadStop: (controller, url) {
              print('TradingViewChart: Load completed');
              // Don't hide loading here, wait for chart ready callback
            },
            onLoadError: (controller, url, code, message) {
              setState(() {
                _isLoading = false;
                _hasError = true;
              });
              print('TradingViewChart: Load error - $code: $message');
            },
            onConsoleMessage: (controller, consoleMessage) {
              print('TradingViewChart: Console - ${consoleMessage.message}');
            },
          ),
          if (_isLoading)
            Container(
              color: const Color(0xFF131722),
              child: const Center(
                child: Column(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    CircularProgressIndicator(
                      valueColor: AlwaysStoppedAnimation<Color>(Colors.blue),
                    ),
                    SizedBox(height: 16),
                    Text(
                      'Loading TradingView Chart...',
                      style: TextStyle(
                        color: Colors.white,
                        fontSize: 14,
                      ),
                    ),
                    SizedBox(height: 8),
                    Text(
                      'This may take a few seconds',
                      style: TextStyle(
                        color: Colors.grey,
                        fontSize: 12,
                      ),
                    ),
                  ],
                ),
              ),
            ),
          if (_hasError)
            Container(
              color: const Color(0xFF131722),
              child: Center(
                child: Column(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    const Icon(
                      Icons.error_outline,
                      color: Colors.red,
                      size: 48,
                    ),
                    const SizedBox(height: 16),
                    const Text(
                      'Failed to load chart',
                      style: TextStyle(
                        color: Colors.white,
                        fontSize: 16,
                        fontWeight: FontWeight.w500,
                      ),
                    ),
                    const SizedBox(height: 8),
                    const Text(
                      'Please check your internet connection\nand try again',
                      textAlign: TextAlign.center,
                      style: TextStyle(
                        color: Colors.grey,
                        fontSize: 14,
                      ),
                    ),
                    const SizedBox(height: 16),
                    ElevatedButton(
                      onPressed: () {
                        setState(() {
                          _isLoading = true;
                          _hasError = false;
                        });
                        _controller?.reload();
                      },
                      child: const Text('Retry'),
                    ),
                  ],
                ),
              ),
            ),
        ],
      ),
    );
  }
}
