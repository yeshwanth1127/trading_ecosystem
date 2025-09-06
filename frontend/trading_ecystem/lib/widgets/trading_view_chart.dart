import 'package:flutter/material.dart';
import 'package:flutter/foundation.dart';
import 'package:flutter_inappwebview/flutter_inappwebview.dart';
import 'dart:html' as html if (dart.library.io) 'dart:io' as html;
import 'dart:convert' as json;

class TradingViewChart extends StatefulWidget {
  final String initialTvSymbol;
  final String initialInterval;
  final VoidCallback? onReady;
  final Function(String)? onSymbolChanged;
  final Function(String)? onIntervalChanged;
  final Function(String)? onError;

  const TradingViewChart({
    Key? key,
    required this.initialTvSymbol,
    this.initialInterval = "60",
    this.onReady,
    this.onSymbolChanged,
    this.onIntervalChanged,
    this.onError,
  }) : super(key: key);

  @override
  State<TradingViewChart> createState() => _TradingViewChartState();
}

class _TradingViewChartState extends State<TradingViewChart> {
  InAppWebViewController? _controller;
  late String _tvSymbol;
  late String _interval;
  bool _isLoading = true;
  String? _errorMessage;

  @override
  void initState() {
    super.initState();
    _tvSymbol = widget.initialTvSymbol;
    _interval = widget.initialInterval;
  }

  @override
  Widget build(BuildContext context) {
    if (_errorMessage != null) {
      return _buildErrorWidget();
    }

    return Container(
      decoration: BoxDecoration(
        color: const Color(0xFF0E1116),
        borderRadius: BorderRadius.circular(8),
      ),
      child: ClipRRect(
        borderRadius: BorderRadius.circular(8),
        child: Stack(
          children: [
            if (kIsWeb)
              _buildWebChart()
            else
              _buildMobileChart(),
            if (_isLoading) _buildLoadingOverlay(),
          ],
        ),
      ),
    );
  }

  Widget _buildWebChart() {
    return HtmlElementView(
      viewType: 'tradingview-chart',
      onPlatformViewCreated: _onWebViewCreated,
    );
  }

  Widget _buildMobileChart() {
    return InAppWebView(
      key: const ValueKey('tradingview_chart'),
      initialFile: 'assets/tradingview/tv_chart.html',
      initialSettings: InAppWebViewSettings(
        javaScriptEnabled: true,
        mediaPlaybackRequiresUserGesture: false,
        allowsInlineMediaPlayback: true,
        transparentBackground: true,
        useShouldOverrideUrlLoading: true,
        allowsBackForwardNavigationGestures: false,
        useOnLoadResource: true,
        useShouldInterceptAjaxRequest: false,
        useShouldInterceptFetchRequest: false,
        clearCache: false,
        cacheEnabled: true,
        domStorageEnabled: true,
        databaseEnabled: true,
        supportZoom: false,
        builtInZoomControls: false,
        displayZoomControls: false,
        mixedContentMode: MixedContentMode.MIXED_CONTENT_ALWAYS_ALLOW,
        useWideViewPort: true,
        loadWithOverviewMode: true,
        safeBrowsingEnabled: false,
        disableDefaultErrorPage: true,
      ),
      onWebViewCreated: (controller) {
        _controller = controller;
        _setupJavaScriptHandlers();
      },
      onLoadStart: (controller, url) {
        setState(() {
          _isLoading = true;
          _errorMessage = null;
        });
      },
      onLoadStop: (controller, url) async {
        setState(() {
          _isLoading = false;
        });
        
        // Apply initial settings after load
        await _applyInitialSettings();
      },
      onReceivedError: (controller, request, errorResponse) {
        setState(() {
          _isLoading = false;
          _errorMessage = 'Failed to load chart: ${errorResponse.reasonPhrase}';
        });
        widget.onError?.call('Load error: ${errorResponse.reasonPhrase}');
      },
      onConsoleMessage: (controller, consoleMessage) {
        debugPrint("[TradingView] ${consoleMessage.message}");
      },
    );
  }

  void _onWebViewCreated(int id) {
    // For web platform, we'll use JavaScript to control the chart
    setState(() {
      _isLoading = false;
    });
    
    // Apply initial settings
    _applyWebInitialSettings();
  }

  Widget _buildLoadingOverlay() {
    return Container(
      color: const Color(0xFF0E1116),
      child: const Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            CircularProgressIndicator(
              valueColor: AlwaysStoppedAnimation<Color>(Colors.white),
            ),
            SizedBox(height: 16),
            Text(
              'Loading TradingView Chart...',
              style: TextStyle(
                color: Colors.white,
                fontSize: 16,
                fontWeight: FontWeight.w500,
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildErrorWidget() {
    return Container(
      decoration: BoxDecoration(
        color: const Color(0xFF0E1116),
        borderRadius: BorderRadius.circular(8),
      ),
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
              'Chart Loading Failed',
              style: TextStyle(
                color: Colors.white,
                fontSize: 18,
                fontWeight: FontWeight.w600,
              ),
            ),
            const SizedBox(height: 8),
            Text(
              _errorMessage ?? 'Unknown error occurred',
              style: const TextStyle(
                color: Colors.grey,
                fontSize: 14,
              ),
              textAlign: TextAlign.center,
            ),
            const SizedBox(height: 16),
            ElevatedButton(
              onPressed: _retryLoad,
              style: ElevatedButton.styleFrom(
                backgroundColor: Colors.blue,
                foregroundColor: Colors.white,
              ),
              child: const Text('Retry'),
            ),
          ],
        ),
      ),
    );
  }

  void _setupJavaScriptHandlers() {
    if (!kIsWeb) {
      _controller?.addJavaScriptHandler(
        handlerName: "tv_ready",
        callback: (args) {
          debugPrint("TradingView chart ready: $args");
          widget.onReady?.call();
          return {"ok": true};
        },
      );

      _controller?.addJavaScriptHandler(
        handlerName: "tv_error",
        callback: (args) {
          final error = args.isNotEmpty ? args[0].toString() : 'Unknown error';
          debugPrint("TradingView chart error: $error");
          setState(() {
            _errorMessage = error;
          });
          widget.onError?.call(error);
          return {"ok": true};
        },
      );
    }
  }

  Future<void> _applyInitialSettings() async {
    try {
      await _invokeJS('''
        if (window.TVDart && window.TVDart.initWidget) {
          window.TVDart.initWidget("$_tvSymbol", "$_interval");
        }
      ''');
    } catch (e) {
      debugPrint("Error applying initial settings: $e");
    }
  }

  void _applyWebInitialSettings() {
    try {
      // For web platform, use JavaScript directly
      html.window.eval('''
        if (window.TVDart && window.TVDart.initWidget) {
          window.TVDart.initWidget("$_tvSymbol", "$_interval");
        }
      ''');
    } catch (e) {
      debugPrint("Error applying web initial settings: $e");
    }
  }

  Future<void> _invokeJS(String js) async {
    try {
      if (_controller != null) {
        await _controller!.evaluateJavascript(source: js);
      }
    } catch (e) {
      debugPrint("JavaScript execution error: $e");
    }
  }

  // Public API methods
  Future<void> setSymbol(String tvSymbol) async {
    if (tvSymbol == _tvSymbol) return;
    
    _tvSymbol = tvSymbol;
    debugPrint("Setting TradingView symbol to: $tvSymbol");
    
    if (kIsWeb) {
      // Web platform
      try {
        html.window.eval('''
          if (window.TVDart && window.TVDart.setSymbol) {
            window.TVDart.setSymbol("$tvSymbol");
          }
        ''');
      } catch (e) {
        debugPrint("Web JavaScript execution error: $e");
      }
    } else {
      // Mobile platform
      await _invokeJS('''
        if (window.TVDart && window.TVDart.setSymbol) {
          window.TVDart.setSymbol("$tvSymbol");
        }
      ''');
    }
    
    widget.onSymbolChanged?.call(tvSymbol);
  }

  Future<void> setInterval(String interval) async {
    if (interval == _interval) return;
    
    _interval = interval;
    debugPrint("Setting TradingView interval to: $interval");
    
    if (kIsWeb) {
      // Web platform
      try {
        html.window.eval('''
          if (window.TVDart && window.TVDart.setInterval) {
            window.TVDart.setInterval("$interval");
          }
        ''');
      } catch (e) {
        debugPrint("Web JavaScript execution error: $e");
      }
    } else {
      // Mobile platform
      await _invokeJS('''
        if (window.TVDart && window.TVDart.setInterval) {
          window.TVDart.setInterval("$interval");
        }
      ''');
    }
    
    widget.onIntervalChanged?.call(interval);
  }

  Future<Map<String, dynamic>?> getChartState() async {
    try {
      if (kIsWeb) {
        // Web platform - return local state
        return {
          'symbol': _tvSymbol,
          'interval': _interval,
          'isReady': !_isLoading && _errorMessage == null,
        };
      } else {
        // Mobile platform
        final result = await _invokeJS('''
          if (window.TVDart && window.TVDart.getChartState) {
            JSON.stringify(window.TVDart.getChartState());
          } else {
            null;
          }
        ''');
        
        if (result != null && result.toString() != 'null') {
          return json.decode(result.toString());
        }
      }
    } catch (e) {
      debugPrint("Error getting chart state: $e");
    }
    return null;
  }

  void _retryLoad() {
    setState(() {
      _errorMessage = null;
      _isLoading = true;
    });
    
    if (kIsWeb) {
      // For web, just reload the widget
      _applyWebInitialSettings();
      setState(() {
        _isLoading = false;
      });
    } else {
      // For mobile, reload the WebView
      _controller?.reload();
    }
  }

  @override
  void dispose() {
    _controller?.dispose();
    super.dispose();
  }
}
