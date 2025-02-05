/*
brew install gperftools
brew install graphviz
brew install gv
*/

#include <iostream>
#include <vector>
#include <chrono>
#include <cmath>

const int N = 10000000;

void inefficientFunction() {
    std::vector<int> vec(N);
    for (int i = 0; i < vec.size(); ++i) {
        vec[i] = i * std::sin(i);  // Inefficient operation
    }
    int y = 8;
    return;
}

void efficientFunction() {
    for (int i = 0; i < 1000000; ++i) {
        int result = i * i;  // Fast operation
    }
    inefficientFunction();
}

int main() {
    auto start = std::chrono::high_resolution_clock::now();
    inefficientFunction();  // Slow function
    efficientFunction();    // Fast function

    auto end = std::chrono::high_resolution_clock::now();
    std::chrono::duration<double> elapsed = end - start;

    std::cout << "Elapsed time: " << elapsed.count() << " seconds" << std::endl;
    
    return 0;
}
