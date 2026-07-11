import 'pack_loader.dart';

/// 離線優先的對話服務
///
/// 用法：
///   // App 啟動時（main.dart 或 initState）
///   await detectAndLoadPacks();             // 偵測 GPS，載入對應包
///
///   // 每次使用者送出訊息時
///   final reply = await OfflineChatService.handle(
///     userText,
///     onApiCall: (text) => callClaudeApi(text),
///   );
class OfflineChatService {
  /// 優先用離線包回應；若未命中則呼叫 [onApiCall]。
  ///
  /// [onApiCall] 是你現有的後端 API 呼叫函式，簽名：
  ///   Future<String> Function(String userText)
  static Future<String> handle(
    String userText, {
    required Future<String> Function(String) onApiCall,
  }) async {
    final match = packLoader.match(userText);
    if (match != null) {
      // 完全離線，不呼叫任何 API
      return match.response;
    }
    // 離線包未命中，交給後端
    return onApiCall(userText);
  }

  /// 檢查某段文字是否能被離線包回應（用於 UI 顯示提示）
  static bool canAnswerOffline(String text) =>
      packLoader.match(text) != null;
}
