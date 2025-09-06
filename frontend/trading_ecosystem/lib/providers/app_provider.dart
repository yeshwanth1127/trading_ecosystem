import 'package:flutter/material.dart';

class AppSettings {
  final ThemeMode themeMode;
  final String language;

  const AppSettings({
    this.themeMode = ThemeMode.system,
    this.language = 'en',
  });

  AppSettings copyWith({
    ThemeMode? themeMode,
    String? language,
  }) {
    return AppSettings(
      themeMode: themeMode ?? this.themeMode,
      language: language ?? this.language,
    );
  }
}

class AppNotifier extends ChangeNotifier {
  AppSettings _settings = const AppSettings();

  AppSettings get settings => _settings;

  void setThemeMode(ThemeMode themeMode) {
    _settings = _settings.copyWith(themeMode: themeMode);
    notifyListeners();
  }

  void setLanguage(String language) {
    _settings = _settings.copyWith(language: language);
    notifyListeners();
  }
}
