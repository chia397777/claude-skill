# 離線對話包 — Flutter 整合說明

## 1. 安裝依賴

在 `pubspec.yaml` 加入：

```yaml
dependencies:
  geolocator: ^12.0.0   # GPS 定位

flutter:
  assets:
    - assets/offline_packs/airport_travel_zh_tw.json
    - assets/offline_packs/southern_taiwan_zh_tw.json
    # 未來新增包時在此補上
```

## 2. 複製 JSON 包

把以下檔案複製到 Flutter 專案的 `assets/offline_packs/`：

```
api_filter/offline_packs/packs/airport_travel_zh_tw.json
api_filter/offline_packs/packs/southern_taiwan_zh_tw.json
```

## 3. 平台權限設定

### Android（`android/app/src/main/AndroidManifest.xml`）
```xml
<uses-permission android:name="android.permission.ACCESS_FINE_LOCATION"/>
<uses-permission android:name="android.permission.ACCESS_COARSE_LOCATION"/>
```

### iOS（`ios/Runner/Info.plist`）
```xml
<key>NSLocationWhenInUseUsageDescription</key>
<string>法寶貝需要您的位置，以自動提供當地旅遊資訊。</string>
```

## 4. App 啟動時初始化（`main.dart`）

```dart
import 'offline_packs/location_detector.dart';

void main() async {
  WidgetsFlutterBinding.ensureInitialized();

  // 偵測 GPS → 自動載入對應離線包（完全離線，無網路需求）
  final loc = await detectAndLoadPacks();
  if (loc.hasMatch) {
    debugPrint('位置偵測：${loc.matchedLabel}，載入包：${loc.loadedPacks}');
  }

  runApp(const MyApp());
}
```

## 5. 聊天頁面整合（`chat_page.dart`）

```dart
import 'offline_packs/offline_chat_service.dart';

Future<void> _onSend(String userText) async {
  final reply = await OfflineChatService.handle(
    userText,
    onApiCall: (text) => apiService.chat(text),  // 你現有的後端呼叫
  );
  setState(() => messages.add(reply));
}
```

## 完整離線流程

```
裝置 GPS（geolocator）
    ↓ lat, lng
LocationDetector（bbox 比對，純 Dart）
    ↓ pack_id 清單
PackLoader.load()（讀取 Flutter assets，無網路）
    ↓
PackLoader.match(userText)（trigger 字串比對）
    ↓ 命中 → 直接回應（$0，離線）
    ↓ 未命中 → 呼叫後端 API
```

## 未來擴充新城市

只需在 `location_detector.dart` 的 `_rules` 清單加一條：

```dart
_LocationRule(
  label: '台中市',
  minLat: 24.050, maxLat: 24.350, minLng: 120.550, maxLng: 120.850,
  packIds: ['central_taiwan'],   // 對應新的 JSON 包
),
```

再新增對應的 JSON 包檔案，不需要改任何其他程式碼。
