import 'dart:convert';
import 'package:flutter/services.dart';
import 'pack_match.dart';

/// 離線對話包載入器
///
/// 使用方式：
///   final loader = PackLoader();
///   await loader.load('southern_taiwan');
///   await loader.load('airport_travel');
///
///   final match = loader.match(userText);
///   if (match != null) {
///     showReply(match.response);   // 完全離線，成本 $0
///   }
class PackLoader {
  final List<Map<String, dynamic>> _packs = [];

  /// 載入 assets/offline_packs/<packId>_zh_tw.json
  Future<void> load(String packId, {String lang = 'zh_tw'}) async {
    if (isLoaded(packId)) return;

    final path = 'assets/offline_packs/${packId}_$lang.json';
    final raw = await rootBundle.loadString(path);
    // 移除行內 // 註解（JSON 原生不支援）
    final stripped = raw.replaceAll(RegExp(r'//[^\n]*'), '');
    final data = json.decode(stripped) as Map<String, dynamic>;
    _packs.add(data);
  }

  bool isLoaded(String packId) =>
      _packs.any((p) => p['pack_id'] == packId);

  /// 比對已載入的所有包，回傳第一個命中的情境；未命中回傳 null。
  PackMatch? match(String text) {
    final lower = text.toLowerCase();
    for (final pack in _packs) {
      final packId = pack['pack_id'] as String;
      for (final scenario in pack['scenarios'] as List) {
        for (final trigger in scenario['triggers'] as List) {
          if (lower.contains((trigger as String).toLowerCase())) {
            return PackMatch(
              packId: packId,
              scenarioId: scenario['id'] as String,
              category: scenario['category'] as String,
              response: scenario['response'] as String,
            );
          }
        }
      }
    }
    return null;
  }

  void clear() => _packs.clear();
}

/// 全域單例，App 啟動後保持在記憶體
final packLoader = PackLoader();
