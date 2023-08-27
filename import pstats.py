import pstats

# Load the profiling results
profiler_stats = pstats.Stats('SandSimResults')

# Sort the results by cumulative time
profiler_stats.sort_stats('cumulative')

# Display the profiling statistics
profiler_stats.print_stats()