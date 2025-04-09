import 'dart:async';
import 'dart:typed_data';
import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'package:shared_preferences/shared_preferences.dart';

class FeedDetailPage extends StatefulWidget {
  final Map<String, dynamic> feed;
  FeedDetailPage({required this.feed});

  @override
  _FeedDetailPageState createState() => _FeedDetailPageState();
}

class _FeedDetailPageState extends State<FeedDetailPage> with SingleTickerProviderStateMixin {
  late AnimationController _animationController;
  late Animation<double> _fadeAnimation;
  StreamController<Uint8List>? _streamController;
  bool _isLoading = true;
  String? _errorMessage;
  Map<String, dynamic>? get feed => widget.feed;
  http.Client? _client;

  @override
  void initState() {
    super.initState();
    _animationController = AnimationController(
      vsync: this,
      duration: Duration(milliseconds: 800),
    );
    _fadeAnimation = Tween<double>(begin: 0.0, end: 1.0).animate(
      CurvedAnimation(parent: _animationController, curve: Curves.easeInOut),
    );
    _animationController.forward();
    _startVideoStream();
  }

  Future<void> _startVideoStream() async {
    try {
      final feedId = feed!['id'].toString();
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

      final url = Uri.parse('http://10.0.2.2:5000/feeds/$feedId/stream');
      _streamController = StreamController<Uint8List>();
      _client = http.Client();

      final request = http.Request('GET', url)
        ..headers['Authorization'] = 'Bearer $token';

      final response = await _client!.send(request).timeout(Duration(seconds: 10));
      if (response.statusCode != 200) {
        setState(() {
          _errorMessage = 'Failed to load stream: ${response.statusCode}';
          _isLoading = false;
        });
        return;
      }

      final boundary = response.headers['content-type']?.split('boundary=')[1]?.trim() ?? 'frame';
      List<int> buffer = [];
      int lastBoundaryTime = DateTime.now().millisecondsSinceEpoch;

      response.stream.listen(
        (data) {
          buffer.addAll(data);
          while (true) {
            final boundaryIndex = _findBoundary(buffer, 0, boundary);
            if (boundaryIndex == -1) break;

            final headerEndIndex = _findHeaderEnd(buffer, boundaryIndex);
            if (headerEndIndex == -1) break;

            final frameStart = headerEndIndex + 4;
            final nextBoundaryIndex = _findBoundary(buffer, frameStart, boundary);
            if (nextBoundaryIndex == -1) break;

            final frameData = buffer.sublist(frameStart, nextBoundaryIndex);

            // Validate JPEG SOI/EOI
            if (frameData.length >= 4 &&
                frameData[0] == 0xFF &&
                frameData[1] == 0xD8 &&
                frameData[frameData.length - 2] == 0xFF &&
                frameData[frameData.length - 1] == 0xD9) {
              _streamController?.add(Uint8List.fromList(frameData));
              if (_isLoading) setState(() => _isLoading = false);
            }

            buffer = buffer.sublist(nextBoundaryIndex);
            lastBoundaryTime = DateTime.now().millisecondsSinceEpoch;
          }

          if (buffer.length > 128 * 1024 ||
              DateTime.now().millisecondsSinceEpoch - lastBoundaryTime > 5000) {
            buffer = buffer.length > 64 * 1024
                ? buffer.sublist(buffer.length - 64 * 1024)
                : [];
            lastBoundaryTime = DateTime.now().millisecondsSinceEpoch;
          }
        },
        onError: (e) {
          setState(() {
            _errorMessage = 'Stream error: $e';
            _isLoading = false;
          });
        },
        onDone: () {
          _client?.close();
          _streamController?.close();
        },
      );
    } catch (e) {
      setState(() {
        _errorMessage = 'Failed to start stream: $e';
        _isLoading = false;
      });
    }
  }

  int _findBoundary(List<int> buffer, int startIndex, String boundary) {
    final boundaryBytes = '--$boundary'.codeUnits;
    for (int i = startIndex; i <= buffer.length - boundaryBytes.length; i++) {
      if (buffer.sublist(i, i + boundaryBytes.length).equals(boundaryBytes)) {
        return i;
      }
    }
    return -1;
  }

  int _findHeaderEnd(List<int> buffer, int startIndex) {
    const headerEnd = [13, 10, 13, 10]; // \r\n\r\n
    for (int i = startIndex; i <= buffer.length - 4; i++) {
      if (buffer.sublist(i, i + 4).equals(headerEnd)) return i;
    }
    return -1;
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text('${feed?['name'] ?? "Unknown Feed"}'),
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
              Text('${feed?['name'] ?? "No Name"}',
                  style: TextStyle(fontSize: 28, fontWeight: FontWeight.bold, color: Colors.blue[800])),
              SizedBox(height: 8),
              Text('Location: ${feed?['location'] ?? "Unknown"} | Status: ${feed?['status'] ?? "Unknown"}',
                  style: TextStyle(fontSize: 16, color: Colors.grey[700])),
              SizedBox(height: 20),
              _isLoading
                  ? Center(child: CircularProgressIndicator())
                  : _errorMessage != null
                      ? _errorWidget(_errorMessage!)
                      : _videoWidget(),
              if (feed?['fireDetected'] == true)
                Padding(
                  padding: const EdgeInsets.only(top: 10),
                  child: Container(
                    padding: EdgeInsets.all(8),
                    color: Colors.red.withOpacity(0.8),
                    child: Text(
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
          return Image.memory(
            snapshot.data!,
            fit: BoxFit.cover,
            width: double.infinity,
            height: 200,
            gaplessPlayback: false,
            errorBuilder: (context, error, stackTrace) => _errorWidget("Invalid image data"),
          );
        } else if (snapshot.hasError) {
          return _errorWidget("Stream error: ${snapshot.error}");
        }
        return Container(
          width: double.infinity,
          height: 200,
          color: Colors.grey[300],
          child: Center(child: Text('Waiting for video feed...')),
        );
      },
    );
  }

  Widget _errorWidget(String message) {
    return Container(
      width: double.infinity,
      height: 200,
      color: Colors.grey[300],
      child: Center(child: Text(message, style: TextStyle(color: Colors.red))),
    );
  }

  @override
  void dispose() {
    _client?.close();
    _streamController?.close();
    _animationController.dispose();
    super.dispose();
  }
}

extension ListEquality on List<int> {
  bool equals(List<int> other) {
    if (length != other.length) return false;
    for (int i = 0; i < length; i++) {
      if (this[i] != other[i]) return false;
    }
    return true;
  }
}

