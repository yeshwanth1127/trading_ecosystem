class ApiResponse<T> {
  final T? data;
  final String? error;
  final bool isSuccess;

  const ApiResponse._({
    this.data,
    this.error,
    required this.isSuccess,
  });

  factory ApiResponse.success(T data) {
    return ApiResponse._(
      data: data,
      isSuccess: true,
    );
  }

  factory ApiResponse.error(String error) {
    return ApiResponse._(
      error: error,
      isSuccess: false,
    );
  }

  bool get hasError => !isSuccess;
  bool get hasData => data != null;

  T? get value => data;
  String? get errorMessage => error;

  @override
  String toString() {
    if (isSuccess) {
      return 'ApiResponse.success($data)';
    } else {
      return 'ApiResponse.error($error)';
    }
  }
}
