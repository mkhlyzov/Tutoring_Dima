#include "ADS_set.h"
#include <iostream>
#include <chrono>
#include <vector>
#include <cstdlib>

// Measure execution time of a code block
#define PROFILE_BLOCK(name, code_block)                                       \
    {                                                                         \
        auto start = std::chrono::high_resolution_clock::now();               \
        code_block;                                                           \
        auto end = std::chrono::high_resolution_clock::now();                 \
        auto duration = std::chrono::duration_cast<std::chrono::milliseconds>(end - start); \
        std::cout << name << " took " << duration.count() << " ms\n";         \
    }

// Test data generation
std::vector<int> generate_random_data(int num_elements, int max_value) {
    std::vector<int> data;
    data.reserve(num_elements);
    for (int i = 0; i < num_elements; ++i) {
        data.push_back(rand() % max_value);
    }
    return data;
}

// Profiling function 1: Insert elements
void profile_insert(ADS_set<int>& my_set, const std::vector<int>& data) {
    PROFILE_BLOCK("Insertion", {
        for (const auto& elem : data) {
            my_set.insert(elem);
        }
    });
}

// Profiling function 2: Search elements
void profile_find(ADS_set<int>& my_set, const std::vector<int>& data) {
    PROFILE_BLOCK("Search", {
        for (const auto& elem : data) {
            my_set.find(elem);
        }
    });
}

// Profiling function 3: Remove elements
void profile_erase(ADS_set<int>& my_set, const std::vector<int>& data) {
    PROFILE_BLOCK("Erase", {
        for (const auto& elem : data) {
            my_set.erase(elem);
        }
    });
}

// Profiling function 4: Iterate over elements (if this is a supported operation)
void profile_iteration(ADS_set<int>& my_set) {
    PROFILE_BLOCK("Iteration", {
        for (const auto& elem : my_set) {
            // Do nothing, just iterate
        }
    });
}

int main() {
    // Prepare test set and random data
    ADS_set<int> my_set;

    // Configure test size
    int num_elements = 1000000; // Adjust size for profiling
    int max_value = 10000000;   // Range of random values

    // Generate random data
    auto data = generate_random_data(num_elements, max_value);

    // Uncomment the blocks you want to profile individually
    profile_insert(my_set, data);
    profile_find(my_set, data);
    profile_iteration(my_set);
    profile_erase(my_set, data);

    return 0;
}
