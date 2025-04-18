import 'package:flutter/material.dart';
import 'package:firebase_core/firebase_core.dart';
import 'package:firebase_messaging/firebase_messaging.dart';
import 'services/notification_service.dart';

import 'pages/login.dart';
import 'pages/signup.dart';
import 'pages/home.dart';
import 'pages/add_feed.dart';
import 'pages/feed_detail.dart';

void main() async {
  WidgetsFlutterBinding.ensureInitialized();
  await Firebase.initializeApp();
  await NotificationService.initialize();

  // ✅ Listen to foreground messages
  FirebaseMessaging.onMessage.listen((RemoteMessage message) {
    if (message.notification != null) {
      NotificationService.showNotification(
        message.notification!.title ?? 'Fire Alert',
        message.notification!.body ?? 'Smoke or fire detected!',
      );
      print("🔥 Foreground message received: ${message.notification?.title}");

    }
  });

  runApp(MyApp());
}

class MyApp extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'FireSafe',
      theme: ThemeData(
        primarySwatch: Colors.blue,
        visualDensity: VisualDensity.adaptivePlatformDensity,
      ),
      initialRoute: '/login',
      routes: {
        '/login': (context) => LoginPage(),
        '/signup': (context) => SignupPage(),
        '/home': (context) => HomePage(),
        '/add-feed': (context) => AddFeedPage(),
        '/feed-detail': (context) => FeedDetailPage(),
      },
    );
  }
}
