// Updated Flutter MJPEG stream client using flutter_mjpeg
// Add this to pubspec.yaml dependencies:
// flutter_mjpeg: ^2.0.0 (or latest)

import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:flutter_mjpeg/flutter_mjpeg.dart';

class FeedDetailPage extends StatefulWidget {
  const FeedDetailPage({Key? key}) : super(key: key);

  @override
  _FeedDetailPageState createState() => _FeedDetailPageState();
}

class _FeedDetailPageState extends State<FeedDetailPage> {
  Map<String, dynamic>? _feed;
  String? _errorMessage;
  bool _isLoading = true;
  String? _streamUrl;

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
        _startMjpegStream();
      }
    }
  }

  Future<void> _startMjpegStream() async {
    final prefs = await SharedPreferences.getInstance();
    final token = prefs.getString('token');
    if (token == null) {
      setState(() {
        _errorMessage = 'Not authenticated';
        _isLoading = false;
      });
      return;
    }

    final feedId = _feed!['id'].toString();
    final uri = Uri.parse('http://192.168.45.195:5001/mjpeg/$feedId?token=$token');

    setState(() {
      _streamUrl = uri.toString();
      _isLoading = false;
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: Text(_feed?['name'] ?? 'Feed')),
      body: _isLoading
          ? const Center(child: CircularProgressIndicator())
          : _errorMessage != null
              ? Center(child: Text(_errorMessage!, style: const TextStyle(color: Colors.red)))
              : _streamUrl == null
                  ? const Center(child: Text('No stream URL'))
                  : Column(
                      children: [
                        Text('Location: ${_feed?['location'] ?? "Unknown"}'),
                        const SizedBox(height: 12),
                        Expanded(
                          child: Mjpeg(
                            isLive: true,
                            stream: _streamUrl!,
                            error: (context, error, stack) => Center(
                              child: Text('Stream error: $error'),
                            ),
                          ),
                        ),
                      ],
                    ),
    );
  }
}
