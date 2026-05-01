import 'package:flutter/material.dart';
import 'package:sqflite/sqflite.dart';
import 'package:path/path.dart';

void main() {
  runApp(const InventoryApp());
}

class InventoryApp extends StatelessWidget {
  const InventoryApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      debugShowCheckedModeBanner: false,
      title: 'Склад Инвентаря',
      theme: ThemeData(
        colorScheme: ColorScheme.fromSeed(seedColor: Colors.blueAccent),
        useMaterial3: true,
      ),
      home: const InventoryListScreen(),
    );
  }
}

class InventoryListScreen extends StatefulWidget {
  const InventoryListScreen({super.key});

  @override
  State<InventoryListScreen> createState() => _InventoryListScreenState();
}

class _InventoryListScreenState extends State<InventoryListScreen> {
  Database? _database;
  List<Map<String, dynamic>> _inventory = [];

  @override
  void initState() {
    super.initState();
    _initDb();
  }

  Future<void> _initDb() async {
    final dbPath = await getDatabasesPath();
    _database = await openDatabase(
      join(dbPath, 'inventory.db'),
      onCreate: (db, version) {
        return db.execute(
          'CREATE TABLE items(id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, count INTEGER)',
        );
      },
      version: 1,
    );
    _refreshItems();
  }

  Future<void> _refreshItems() async {
    final data = await _database?.query('items') ?? [];
    setState(() {
      _inventory = data;
    });
  }

  Future<void> _addItem(String name, int count) async {
    await _database?.insert('items', {'name': name, 'count': count});
    _refreshItems();
  }

  Future<void> _giveItem(int id, int currentCount) async {
    if (currentCount > 0) {
      await _database?.update('items', {'count': currentCount - 1}, where: 'id = ?', whereArgs: [id]);
      _refreshItems();
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Склад Инвентаря'),
        centerTitle: true,
        backgroundColor: Theme.of(context).colorScheme.primaryContainer,
      ),
      body: _inventory.isEmpty
          ? const Center(child: Text('На складе пусто'))
          : ListView.builder(
              padding: const EdgeInsets.all(8),
              itemCount: _inventory.length,
              itemBuilder: (context, index) {
                final item = _inventory[index];
                return Card(
                  child: ListTile(
                    title: Text(item['name'], style: const TextStyle(fontWeight: FontWeight.bold)),
                    subtitle: Text('В наличии: ${item['count']} шт.'),
                    trailing: ElevatedButton(
                      onPressed: () => _giveItem(item['id'], item['count']),
                      child: const Text('Выдать'),
                    ),
                  ),
                );
              },
            ),
      floatingActionButton: FloatingActionButton(
        onPressed: () => _showAddDialog(),
        child: const Icon(Icons.add),
      ),
    );
  }

  void _showAddDialog() {
    final nameController = TextEditingController();
    final countController = TextEditingController();
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Добавить предмет'),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            TextField(controller: nameController, decoration: const InputDecoration(labelText: 'Название')),
            TextField(controller: countController, decoration: const InputDecoration(labelText: 'Количество'), keyboardType: TextInputType.number),
          ],
        ),
        actions: [
          TextButton(onPressed: () => Navigator.pop(context), child: const Text('Отмена')),
          ElevatedButton(
            onPressed: () {
              _addItem(nameController.text, int.tryParse(countController.text) ?? 0);
              Navigator.pop(context);
            },
            child: const Text('ОК'),
          ),
        ],
      ),
    );
  }
}
