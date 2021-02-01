DATABASE_NAME = 's54588__data'

ANALYSIS_BATCH_SIZE = 100
# if there's more entries then batch size, how many times they should be shuffled and clustered
ANALYSIS_SHUFFLE_AMOUNT = 10

ANALYSIS_CLUSTERING_EPS = 0.05

# table for batch size - eps
CLUSTERING_EPS_TABLE = {
    30: 0.2,
    60: 0.1,
    100: 0.05
}

ANALYSIS_TEST_OUT_FILE = 'clustering_test.md'