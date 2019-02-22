# Supported backends for providing the data for metrics in the quality models
BACKEND_METRICS_DATA = ['scava-metrics', 'grimoirelab', 'ossmeter']


def find_metric_name_field(backend_metrics_data):
    """ Find the field with the metric name for a given backend for metrics """

    if backend_metrics_data not in BACKEND_METRICS_DATA:
        raise RuntimeError('Backend for metrics data not supported: ' + backend_metrics_data)

    if backend_metrics_data == 'grimoirelab':
        metric_name = 'metadata__gelk_backend_name'
    elif backend_metrics_data == 'ossmeter':
        metric_name = 'metric_es_name'
    elif backend_metrics_data == 'scava-metrics':
        metric_name = 'metric_name'

    return metric_name
