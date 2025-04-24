
import 'dart:convert';
import 'dart:io';
import 'package:flutter/material.dart';
import 'package:flutter_mjpeg/flutter_mjpeg.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:firebase_core/firebase_core.dart';
import 'package:firebase_messaging/firebase_messaging.dart';
import 'package:http/http.dart' as http;

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
      initialRoute: '/',
      routes: {
        '/': (context) => const Placeholder(), // Replace with your home page
        '/feed-detail': (context) => const FeedDetailPage(),
      },
    );
  }
}

class FeedDetailPage extends StatefulWidget {
  const FeedDetailPage({Key? key}) : super(key: key);

  @override
  State<FeedDetailPage> createState() => _FeedDetailPageState();
}

class _FeedDetailPageState extends State<FeedDetailPage> {
  Map<String, dynamic>? _feed;
  String? _streamUrl;
  String? _errorMessage;
  bool _isLoading = true;

  @override
  void initState() {
    super.initState();
    _initialize();
  }

  Future<void> _initialize() async {
    final args = ModalRoute.of(context)?.settings.arguments as Map<String, dynamic>?;
    if (args == null || args['id'] == null) {
      setState(() {
        _errorMessage = 'Feed ID not provided';
        _isLoading = false;
      });
      return;
    }

    final feedId = args['id'].toString();
    final prefs = await SharedPreferences.getInstance();
    final token = prefs.getString('token');

    if (token == null) {
      setState(() {
        _errorMessage = 'User token not found';
        _isLoading = false;
      });
      return;
    }

    await _fetchFeed(token, feedId);
    await _registerFcmToken(token);
    _startMjpegStream(token, feedId);
  }

  Future<void> _fetchFeed(String token, String feedId) async {
    try {
      final response = await http.get(
        Uri.parse('http://192.168.45.195:5001/feeds/$feedId'),
        headers: {
          HttpHeaders.authorizationHeader: 'Bearer $token',
        },
      );

      if (response.statusCode == 200) {
        setState(() {
          _feed = json.decode(response.body);
        });
      } else {
        setState(() {
          _errorMessage = 'Failed to load feed details: ${response.body}';
        });
      }
    } catch (e) {
      setState(() {
        _errorMessage = 'Error loading feed details: $e';
      });
    }
  }

  Future<void> _registerFcmToken(String token) async {
    final fcmToken = await FirebaseMessaging.instance.getToken();
    if (fcmToken != null) {
      await http.post(
        Uri.parse('http://192.168.45.195:5001/save-token'),
        headers: {
          HttpHeaders.authorizationHeader: 'Bearer $token',
          HttpHeaders.contentTypeHeader: 'application/json',
        },
        body: jsonEncode({'fcmToken': fcmToken}),
      );
    }
  }

  void _startMjpegStream(String token, String feedId) {
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

