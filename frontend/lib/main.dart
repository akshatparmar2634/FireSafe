import 'package:flutter/material.dart';
import 'package:firebase_core/firebase_core.dart';
import 'package:firebase_messaging/firebase_messaging.dart';
import 'services/notification_service.dart';

import 'pages/login.dart';
import 'pages/signup.dart';
import 'pages/home.dart';
import 'pages/add_feed.dart';
import 'pages/feed_detail.dart';

/// ✅ Background handler for terminated/background state
Future<void> _firebaseMessagingBackgroundHandler(RemoteMessage message) async {
  print("📨 Handling background message...");
  await Firebase.initializeApp();
  await NotificationService.initialize();

  if (message.notification != null) {
    NotificationService.showNotification(
      message.notification!.title ?? '🔥 Fire Alert',
      message.notification!.body ?? 'Smoke or fire detected!',
    );
    print("🔥 Background message received: \${message.notification?.title}");
  }
}

void main() async {
  print("🚀 App starting...");
  WidgetsFlutterBinding.ensureInitialized();
  await Firebase.initializeApp();
  print("✅ Firebase initialized");
  await NotificationService.initialize();
  print("🔔 Notification service initialized");

  // ✅ Now it's safe to request permission
  await FirebaseMessaging.instance.requestPermission();

  // ✅ Listen for background messages
  FirebaseMessaging.onBackgroundMessage(_firebaseMessagingBackgroundHandler);

  // ✅ Listen for foreground messages
  FirebaseMessaging.onMessage.listen((RemoteMessage message) {
    if (message.notification != null) {
      NotificationService.showNotification(
        message.notification!.title ?? '🔥 Fire Alert',
        message.notification!.body ?? 'Smoke or fire detected!',
      );
      print("🔥 Foreground message received: \${message.notification?.title}");
    }
  });

  runApp(MyApp());
}

class MyApp extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    print("🏁 Building MyApp widget");
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
