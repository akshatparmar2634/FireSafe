import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'package:shared_preferences/shared_preferences.dart';
import '../services/notification_service.dart';

class HomePage extends StatefulWidget {
  const HomePage({super.key});

  @override
  State<HomePage> createState() => _HomePageState();
}

class _HomePageState extends State<HomePage> {
  List<dynamic> feeds = [];
  bool isLoading = true;

  @override
  void initState() {
    super.initState();
    fetchFeeds();
  }

  Future<void> fetchFeeds() async {
    setState(() => isLoading = true);

    final prefs = await SharedPreferences.getInstance();
    final token = prefs.getString('token');

    if (token == null) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Please login again')),
      );
      return;
    }

    try {
      final response = await http.get(
        Uri.parse('http://192.168.242.195:5001/feeds'),
        headers: {'Authorization': 'Bearer $token'},
      );

      if (response.statusCode == 200) {
        final List<dynamic> data = json.decode(response.body);
        setState(() {
          feeds = data;
          isLoading = false;
        });
      } else {
        setState(() => isLoading = false);
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Failed to load feeds: ${response.body}')),
        );
      }
    } catch (e) {
      setState(() => isLoading = false);
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Error fetching feeds: $e')),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text('Home - Camera Feeds'),
        backgroundColor: Colors.blue[800],
        foregroundColor: Colors.white,
      ),
      body: Padding(
        padding: const EdgeInsets.all(8.0),
        child: isLoading
            ? const Center(child: CircularProgressIndicator())
            : Column(
                children: [
                  Padding(
                    padding: const EdgeInsets.symmetric(vertical: 16.0),
                    child: Text(
                      'Your Cameras',
                      style: TextStyle(fontSize: 24, fontWeight: FontWeight.bold, color: Colors.blue[800]),
                    ),
                  ),
                  Expanded(
                    child: feeds.isEmpty
                        ? const Center(child: Text('No feeds found. Add one!'))
                        : ListView.builder(
                            itemCount: feeds.length,
                            itemBuilder: (context, index) {
                              final feed = feeds[index];
                              return Card(
                                elevation: 4,
                                margin: const EdgeInsets.symmetric(vertical: 8),
                                child: ListTile(
                                  leading: Icon(
                                    Icons.videocam,
                                    color: feed['status'] == 'Active' ? Colors.green : Colors.red,
                                  ),
                                  title: Row(
                                    children: [
                                      Text(
                                        feed['name'] ?? 'Unnamed',
                                        style: const TextStyle(fontWeight: FontWeight.bold),
                                      ),
                                      if (feed['fireDetected'] == true) ...[
                                        const SizedBox(width: 8),
                                        Container(
                                          padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
                                          decoration: BoxDecoration(
                                            color: Colors.red,
                                            borderRadius: BorderRadius.circular(12),
                                          ),
                                          child: const Text(
                                            'FIRE',
                                            style: TextStyle(color: Colors.white, fontSize: 12),
                                          ),
                                        ),
                                      ],
                                    ],
                                  ),
                                  subtitle: Text(
                                    'Status: ${feed['status'] ?? 'Unknown'} | ${feed['location'] ?? 'Unknown'}',
                                  ),
                                  trailing: Icon(Icons.arrow_forward, color: Colors.blue[800]),
                                  onTap: () {
                                    Navigator.pushNamed(
                                      context,
                                      '/feed-detail',
                                      arguments: feed,
                                    );
                                  },
                                ),
                              );
                            },
                          ),
                  ),
                  if (feeds.isNotEmpty) ...[
                    const SizedBox(height: 16),
                    ElevatedButton.icon(
                      onPressed: () async {
                        final result = await Navigator.pushNamed(context, '/notifications');
                        if (result == true) {
                          fetchFeeds(); // Refresh when notification is acknowledged
                        }
                      },
                      icon: const Icon(Icons.notifications),
                      label: const Text('View Notifications'),
                      style: ElevatedButton.styleFrom(
                        padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 15),
                        backgroundColor: Colors.blue[800],
                        foregroundColor: Colors.white,
                      ),
                    ),
                  ],
                  const SizedBox(height: 16),
                  ElevatedButton.icon(
                    onPressed: () async {
                      final result = await Navigator.pushNamed(context, '/add-feed');
                      if (result == true) {
                        fetchFeeds(); // Refresh when feed added
                      }
                    },
                    icon: const Icon(Icons.add),
                    label: const Text('Add New Feed'),
                    style: ElevatedButton.styleFrom(
                      padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 15),
                      backgroundColor: Colors.blue[800],
                      foregroundColor: Colors.white,
                    ),
                  ),
                ],
              ),
      ),
    );
  }
}
