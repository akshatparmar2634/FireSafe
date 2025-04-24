// Complete Flutter frontend with MJPEG stream + Firebase FCM registration

import 'package:flutter/material.dart';
import 'package:flutter_mjpeg/flutter_mjpeg.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:firebase_core/firebase_core.dart';
import 'package:firebase_messaging/firebase_messaging.dart';
import 'package:http/http.dart' as http;
import 'dart:io';

void main() async {
  WidgetsFlutterBinding.ensureInitialized();
  await Firebase.initializeApp();
  runApp(const MyApp());
}

class MyApp extends StatelessWidget {
  const MyApp({Key? key}) : super(key: key);
  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Fire Detection Stream',
      theme: ThemeData(primarySwatch: Colors.blue),
      home: const FeedDetailPage(),
    );
  }
}

class FeedDetailPage extends StatefulWidget {
  const FeedDetailPage({Key? key}) : super(key: key);

  @override
  State<FeedDetailPage> createState() => _FeedDetailPageState();
}

class _FeedDetailPageState extends State<FeedDetailPage> {
  String? _streamUrl;
  String? _errorMessage;
  bool _isLoading = true;
  Map<String, dynamic>? _feed = {
    'id': 3,
    'name': 'Test Feed',
    'location': 'Office',
    'status': 'Online',
  };

  @override
  void initState() {
    super.initState();
    _initializeMessaging();
  }

  Future<void> _initializeMessaging() async {
    final prefs = await SharedPreferences.getInstance();
    final token = prefs.getString('token');
    if (token == null) {
      setState(() {
        _errorMessage = 'User token not found';
        _isLoading = false;
      });
      return;
    }

    final fcmToken = await FirebaseMessaging.instance.getToken();
    if (fcmToken != null) {
      await http.post(
        Uri.parse('http://192.168.45.195:5001/save-token'),
        headers: {
          HttpHeaders.authorizationHeader: 'Bearer $token',
          HttpHeaders.contentTypeHeader: 'application/json',
        },
        body: '{"fcmToken": "$fcmToken"}',
      );

    }

    _startMjpegStream(token);
  }

  void _startMjpegStream(String token) {
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
              : Column(
                  crossAxisAlignment: CrossAxisAlignment.stretch,
                  children: [
                    Container(
                      padding: const EdgeInsets.all(12),
                      color: Colors.white,
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            'Location: ${_feed?['location'] ?? "Unknown"}',
                            style: const TextStyle(fontSize: 16, fontWeight: FontWeight.w500),
                          ),
                          const SizedBox(height: 6),
                          Text(
                            'Status: ${_feed?['status'] ?? ""}',
                            style: TextStyle(fontSize: 14, color: Colors.green[700]),
                          ),
                        ],
                      ),
                    ),
                    const SizedBox(height: 8),
                    Expanded(
                      child: Container(
                        color: Colors.black,
                        child: _streamUrl != null
                            ? Mjpeg(
                                isLive: true,
                                stream: _streamUrl!,
                                error: (context, error, stack) => Center(
                                  child: Text('Stream error: $error', style: const TextStyle(color: Colors.white)),
                                ),
                              )
                            : const Center(child: Text('No stream URL')),
                      ),
                    ),
                  ],
                ),
    );
  }
}
