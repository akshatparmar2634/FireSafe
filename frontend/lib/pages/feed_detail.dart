import 'dart:async';
import 'dart:convert';
import 'dart:typed_data';
import 'package:flutter/material.dart';
import 'package:web_socket_channel/io.dart';
import 'package:shared_preferences/shared_preferences.dart';

class FeedDetailPage extends StatefulWidget {
  const FeedDetailPage({Key? key}) : super(key: key);

  @override
  _FeedDetailPageState createState() => _FeedDetailPageState();
}

class _FeedDetailPageState extends State<FeedDetailPage> with SingleTickerProviderStateMixin {
  late AnimationController _animationController;
  late Animation<double> _fadeAnimation;
  IOWebSocketChannel? _channel;
  StreamController<Uint8List>? _streamController;
  bool _isLoading = true;
  String? _errorMessage;
  Map<String, dynamic>? _feed;

  @override
  void initState() {
    super.initState();
    _animationController = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 800),
    );
    _fadeAnimation = Tween<double>(begin: 0.0, end: 1.0).animate(
      CurvedAnimation(parent: _animationController, curve: Curves.easeInOut),
    );
    _animationController.forward();
    _streamController = StreamController<Uint8List>();
  }

  @override
  void didChangeDependencies() {
    super.didChangeDependencies();
    if (_feed == null) {
      final feedData = ModalRoute.of(context)?.settings.arguments as Map<String, dynamic>?;
      if (feedData == null) {
        setState(() {
          _errorMessage = 'No feed data provided';
          _isLoading = false;
        });
      } else {
        _feed = feedData;
        _startVideoStream();
      }
    }
  }

  Future<void> _startVideoStream() async {
    try {
      final feedId = _feed!['id'].toString();
      final prefs = await SharedPreferences.getInstance();
      final token = prefs.getString('token');
      if (token == null) {
        setState(() {
          _errorMessage = 'Not authenticated. Please log in.';
          _isLoading = false;
        });
        Navigator.pushReplacementNamed(context, '/login');
        return;
      }

      // The WebSocket URL; for an Android emulator, use 10.0.2.2.
      final wsUrl = 'ws://10.0.2.2:8765/feeds/$feedId';
      print('[FLUTTER DEBUG] Connecting to WebSocket: $wsUrl with token: $token');
      // Provide both the Authorization token and feed_id as headers.
      _channel = IOWebSocketChannel.connect(
        Uri.parse(wsUrl),
        headers: {
          'Authorization': 'Bearer $token',
          'feed_id': feedId,
        },
      );

      _channel!.stream.listen(
        (data) {
          print('[FLUTTER DEBUG] Received data of type: ${data.runtimeType}');
          if (data is String) {
            try {
              // Data is a base64-encoded string.
              Uint8List imageBytes = base64Decode(data);
              _streamController?.add(imageBytes);
              if (_isLoading) setState(() => _isLoading = false);
            } catch (e) {
              print('[FLUTTER DEBUG] Error decoding base64 frame: $e');
              setState(() {
                _errorMessage = 'Error decoding frame: $e';
                _isLoading = false;
              });
            }
          } else {
            print('[FLUTTER DEBUG] Received unexpected data type.');
          }
        },
        onError: (e) {
          print('[FLUTTER DEBUG] WebSocket error: $e');
          setState(() {
            _errorMessage = 'WebSocket error: $e';
            _isLoading = false;
          });
        },
        onDone: () {
          print('[FLUTTER DEBUG] WebSocket closed');
          setState(() {
            _errorMessage = 'WebSocket connection closed';
            _isLoading = false;
          });
          _streamController?.close();
        },
      );
    } catch (e) {
      print('[FLUTTER DEBUG] Stream startup error: $e');
      setState(() {
        _errorMessage = 'Failed to start stream: $e';
        _isLoading = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text('${_feed?['name'] ?? "Unknown Feed"}'),
        backgroundColor: Colors.blue[800],
        foregroundColor: Colors.white,
      ),
      body: FadeTransition(
        opacity: _fadeAnimation,
        child: Padding(
          padding: const EdgeInsets.all(16.0),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text('${_feed?['name'] ?? "No Name"}',
                  style: TextStyle(fontSize: 28, fontWeight: FontWeight.bold, color: Colors.blue[800])),
              const SizedBox(height: 8),
              Text('Location: ${_feed?['location'] ?? "Unknown"} | Status: ${_feed?['status'] ?? "Unknown"}',
                  style: TextStyle(fontSize: 16, color: Colors.grey[700])),
              const SizedBox(height: 20),
              _isLoading
                  ? const Center(child: CircularProgressIndicator())
                  : _errorMessage != null
                      ? _errorWidget(_errorMessage!)
                      : _videoWidget(),
              if (_feed?['fireDetected'] == true)
                Padding(
                  padding: const EdgeInsets.only(top: 10),
                  child: Container(
                    padding: const EdgeInsets.all(8),
                    color: Colors.red.withOpacity(0.8),
                    child: const Text(
                      'FIRE DETECTED',
                      style: TextStyle(color: Colors.white, fontWeight: FontWeight.bold, fontSize: 16),
                    ),
                  ),
                ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _videoWidget() {
  return StreamBuilder<Uint8List>(
    stream: _streamController?.stream,
    builder: (context, snapshot) {
      if (snapshot.hasData) {
        // Provide a UniqueKey to force Flutter to rebuild the widget.
        return Image.memory(
          snapshot.data!,
          key: UniqueKey(),
          fit: BoxFit.cover,
          width: double.infinity,
          height: 200,
          gaplessPlayback: true,
          errorBuilder: (context, error, stackTrace) => _errorWidget("Invalid image data"),
        );
      } else if (snapshot.hasError) {
        return _errorWidget("Stream error: ${snapshot.error}");
      }
      return Container(
        width: double.infinity,
        height: 200,
        color: Colors.grey[300],
        child: const Center(child: Text('Waiting for video feed...')),
      );
    },
  );
}


  Widget _errorWidget(String message) {
    return Container(
      width: double.infinity,
      height: 200,
      color: Colors.grey[300],
      child: Center(child: Text(message, style: const TextStyle(color: Colors.red))),
    );
  }

  @override
  void dispose() {
    _channel?.sink.close();
    _streamController?.close();
    _animationController.dispose();
    super.dispose();
  }
}
