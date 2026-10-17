#include <iostream>
#include <vector>
#include <random>
#include <chrono>

constexpr std::size_t DATA_SIZE = 20'000'000;
constexpr int REPEAT_COUNT = 20;
constexpr float THRESHOLD = 0.5f;

[[gnu::noipa]]
std::size_t count_less_than_threshold(
    const std::vector<float>& data,
    float threshold
) {
    std::size_t count = 0;

    for (std::size_t i = 0; i < data.size(); ++i) {
        if (data[i] <= threshold) {
            ++count;
        }
    }

    return count;
}


int main() {
    std::vector<float> data(DATA_SIZE);

    std::mt19937 generator(67);
    std::uniform_real_distribution<float> distribution(
        0.0f,
        1.0f
    );

    for (auto& value : data) {
        value = distribution(generator);
    }

    auto start = std::chrono::high_resolution_clock::now();

    std::size_t total_count = 0;

    for (int repeat = 0; repeat < REPEAT_COUNT; ++repeat) {
        total_count += count_less_than_threshold(
            data,
            THRESHOLD
        );
    }

    auto end = std::chrono::high_resolution_clock::now();

    std::chrono::duration<double> elapsed = end - start;

    std::cout << "Total count: "
              << total_count
              << '\n';

    std::cout << "Execution time: "
              << elapsed.count()
              << " s\n";

    return 0;
}