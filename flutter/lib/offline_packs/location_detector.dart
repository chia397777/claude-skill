import 'package:geolocator/geolocator.dart';
import 'pack_loader.dart';

/// 一條地理範圍規則
class _LocationRule {
  final String label;
  final double minLat, maxLat, minLng, maxLng;
  final List<String> packIds;

  const _LocationRule({
    required this.label,
    required this.minLat,
    required this.maxLat,
    required this.minLng,
    required this.maxLng,
    required this.packIds,
  });

  bool contains(double lat, double lng) =>
      lat >= minLat && lat <= maxLat && lng >= minLng && lng <= maxLng;
}

/// 座標→離線包 對應規則
/// 越具體（機場）排越前；通用區域排後
const _rules = [
  // ── 機場 ──
  _LocationRule(
    label: '桃園國際機場',
    minLat: 25.055, maxLat: 25.090, minLng: 121.215, maxLng: 121.255,
    packIds: ['airport_travel'],
  ),
  _LocationRule(
    label: '高雄小港機場',
    minLat: 22.565, maxLat: 22.600, minLng: 120.340, maxLng: 120.370,
    packIds: ['airport_travel', 'southern_taiwan'],
  ),
  _LocationRule(
    label: '台南機場',
    minLat: 22.945, maxLat: 22.960, minLng: 120.195, maxLng: 120.220,
    packIds: ['airport_travel', 'southern_taiwan'],
  ),
  _LocationRule(
    label: '台東豐年機場',
    minLat: 22.745, maxLat: 22.765, minLng: 121.095, maxLng: 121.115,
    packIds: ['airport_travel', 'southern_taiwan'],
  ),
  // ── 南台灣城市 ──
  _LocationRule(
    label: '高雄市',
    minLat: 22.400, maxLat: 22.760, minLng: 120.200, maxLng: 120.750,
    packIds: ['southern_taiwan'],
  ),
  _LocationRule(
    label: '台南市',
    minLat: 22.700, maxLat: 23.450, minLng: 120.050, maxLng: 120.500,
    packIds: ['southern_taiwan'],
  ),
  _LocationRule(
    label: '屏東縣（含墾丁）',
    minLat: 21.890, maxLat: 22.710, minLng: 120.420, maxLng: 120.910,
    packIds: ['southern_taiwan'],
  ),
  _LocationRule(
    label: '台東縣',
    minLat: 22.210, maxLat: 23.180, minLng: 120.880, maxLng: 121.380,
    packIds: ['southern_taiwan'],
  ),
];

class LocationResult {
  final double lat;
  final double lng;
  final String matchedLabel;       // 命中的地點名稱（空字串代表不在已知範圍）
  final List<String> loadedPacks;  // 本次實際載入的 pack_id

  const LocationResult({
    required this.lat,
    required this.lng,
    required this.matchedLabel,
    required this.loadedPacks,
  });

  bool get hasMatch => matchedLabel.isNotEmpty;
}

/// 請求 GPS 權限，取得座標，比對 bbox，自動載入對應離線包。
///
/// 整個流程完全在裝置本地執行，無任何網路請求。
///
/// 使用方式（App 啟動後呼叫一次）：
///   final result = await detectAndLoadPacks();
///   print(result.matchedLabel);    // "高雄市"
///   print(result.loadedPacks);     // ["southern_taiwan"]
Future<LocationResult> detectAndLoadPacks() async {
  // ── 1. 確認 / 請求定位權限 ──────────────────────────────
  bool serviceEnabled = await Geolocator.isLocationServiceEnabled();
  if (!serviceEnabled) {
    return const LocationResult(lat: 0, lng: 0, matchedLabel: '', loadedPacks: []);
  }

  LocationPermission permission = await Geolocator.checkPermission();
  if (permission == LocationPermission.denied) {
    permission = await Geolocator.requestPermission();
    if (permission == LocationPermission.denied ||
        permission == LocationPermission.deniedForever) {
      return const LocationResult(lat: 0, lng: 0, matchedLabel: '', loadedPacks: []);
    }
  }

  // ── 2. 取得目前座標 ──────────────────────────────────────
  final position = await Geolocator.getCurrentPosition(
    desiredAccuracy: LocationAccuracy.low, // 低精度即可，省電
  );
  final lat = position.latitude;
  final lng = position.longitude;

  // ── 3. bbox 比對（純本地運算）───────────────────────────
  String firstLabel = '';
  final seen = <String>{};
  final toLoad = <String>[];

  for (final rule in _rules) {
    if (rule.contains(lat, lng)) {
      if (firstLabel.isEmpty) firstLabel = rule.label;
      for (final pid in rule.packIds) {
        if (seen.add(pid)) toLoad.add(pid);
      }
    }
  }

  // ── 4. 載入離線包（從 Flutter assets 讀取，無網路）────────
  final loaded = <String>[];
  for (final packId in toLoad) {
    if (!packLoader.isLoaded(packId)) {
      await packLoader.load(packId);
      loaded.add(packId);
    }
  }

  return LocationResult(
    lat: lat,
    lng: lng,
    matchedLabel: firstLabel,
    loadedPacks: loaded,
  );
}
