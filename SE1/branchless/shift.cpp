#include <iostream>
#include <random>

inline int shift_1_test(int maxX) {
    bool r = rand() % 2;
    bool cond = (r && (maxX == 35));
    int shift = cond ? 10 : 0;
    return shift;
}

inline int shift_2_test(int maxX) {
    bool r = rand() & 1;
    bool cond = (r & (maxX == 35));
    int shift = cond * 10;
    return shift;
}

int main() {
    constexpr int N = 100000000;

    auto start = std::chrono::steady_clock::now();

    for (int i = 0; i < N; ++i) {
        shift_1_test(i & 1 + 35);
    }

    auto mid = std::chrono::steady_clock::now();

    for (int i = 0; i < N; ++i) {
        shift_2_test(i & 1 + 35);
    }

    auto end = std::chrono::steady_clock::now();

    std::cout << "shift_1: "
              << std::chrono::duration_cast<std::chrono::nanoseconds>(mid - start).count()
              << " ns\n";

    std::cout << "shift_2: "
              << std::chrono::duration_cast<std::chrono::nanoseconds>(end - mid).count()
              << " ns\n";
}
