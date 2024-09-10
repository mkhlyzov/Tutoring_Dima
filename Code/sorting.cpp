#include <iostream>
#include <vector>
#include <algorithm> // For std::is_sorted
#include <cstdlib>   // For std::rand and std::srand
#include <ctime>     // For std::time

// Function to generate random sequences of integers in the range [low, high)
std::vector<int> generateRandomSequence(int length, int low, int high) {
    std::vector<int> sequence(length);
    for (int i = 0; i < length; ++i) {
        sequence[i] = low + std::rand() % (high - low);
    }
    return sequence;
}

// Function to check if a sequence is in ascending order
bool isAscendingOrder(const std::vector<int>& sequence) {
    for (size_t i = 1; i < sequence.size(); ++i) {
        if (sequence[i] < sequence[i - 1]) {
            return false;
        }
    }
    return true;
}

// Function to sort a sequence using insertion sort
void insertionSort(std::vector<int>& sequence) {
    for (size_t i = 1; i < sequence.size(); ++i) {
        int key = sequence[i];
        int j = i - 1;
        while (j >= 0 && sequence[j] > key) {
            sequence[j + 1] = sequence[j];
            --j;
        }
        sequence[j + 1] = key;
    }
}

// Test function that creates random vectors, sorts them, and checks order
void testSortingAlgorithm(int n, int length, int low, int high) {
    for (int i = 0; i < n; ++i) {
        std::vector<int> sequence = generateRandomSequence(length, low, high);
        insertionSort(sequence);
        if (!isAscendingOrder(sequence)) {
            std::cout << "Test failed on iteration " << i + 1 << "\n";
            return;
        }
    }
    std::cout << "All tests passed!\n";
}

int main() {
    std::srand(static_cast<unsigned>(std::time(nullptr))); // Seed the random number generator

    // Run the test with n=1000, length=10, low=0, high=100
    testSortingAlgorithm(1000, 100, 0, 100);

    return 0;
}
