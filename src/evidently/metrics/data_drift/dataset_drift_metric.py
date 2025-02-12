from typing import Dict
from typing import List
from typing import Optional

from evidently.base_metric import InputData
from evidently.base_metric import Metric
from evidently.base_metric import MetricResult
from evidently.calculations.data_drift import get_drift_for_columns
from evidently.calculations.stattests import PossibleStatTestType
from evidently.model.widget import BaseWidgetInfo
from evidently.options import DataDriftOptions
from evidently.renderers.base_renderer import MetricRenderer
from evidently.renderers.base_renderer import default_renderer
from evidently.renderers.html_widgets import CounterData
from evidently.renderers.html_widgets import counter
from evidently.utils.data_operations import process_columns


class DatasetDriftMetricResults(MetricResult):
    drift_share: float
    number_of_columns: int
    number_of_drifted_columns: int
    share_of_drifted_columns: float
    dataset_drift: bool


class DatasetDriftMetric(Metric[DatasetDriftMetricResults]):
    columns: Optional[List[str]]
    options: DataDriftOptions
    drift_share: float

    def __init__(
        self,
        columns: Optional[List[str]] = None,
        drift_share: float = 0.5,
        stattest: Optional[PossibleStatTestType] = None,
        cat_stattest: Optional[PossibleStatTestType] = None,
        num_stattest: Optional[PossibleStatTestType] = None,
        text_stattest: Optional[PossibleStatTestType] = None,
        per_column_stattest: Optional[Dict[str, PossibleStatTestType]] = None,
        stattest_threshold: Optional[float] = None,
        cat_stattest_threshold: Optional[float] = None,
        num_stattest_threshold: Optional[float] = None,
        text_stattest_threshold: Optional[float] = None,
        per_column_stattest_threshold: Optional[Dict[str, float]] = None,
    ):
        self.columns = columns
        self.options = DataDriftOptions(
            all_features_stattest=stattest,
            cat_features_stattest=cat_stattest,
            num_features_stattest=num_stattest,
            text_features_stattest=text_stattest,
            per_feature_stattest=per_column_stattest,
            all_features_threshold=stattest_threshold,
            cat_features_threshold=cat_stattest_threshold,
            num_features_threshold=num_stattest_threshold,
            text_features_threshold=text_stattest_threshold,
            per_feature_threshold=per_column_stattest_threshold,
        )
        self.drift_share = drift_share

    def get_parameters(self) -> tuple:
        return (
            self.drift_share,
            None if self.columns is None else tuple(self.columns),
            self.options,
        )

    def calculate(self, data: InputData) -> DatasetDriftMetricResults:
        if data.reference_data is None:
            raise ValueError("Reference dataset should be present")

        dataset_columns = process_columns(data.reference_data, data.column_mapping)
        result = get_drift_for_columns(
            current_data=data.current_data,
            reference_data=data.reference_data,
            data_drift_options=self.options,
            drift_share_threshold=self.drift_share,
            dataset_columns=dataset_columns,
            columns=self.columns,
        )
        return DatasetDriftMetricResults(
            drift_share=self.drift_share,
            number_of_columns=result.number_of_columns,
            number_of_drifted_columns=result.number_of_drifted_columns,
            share_of_drifted_columns=result.share_of_drifted_columns,
            dataset_drift=result.dataset_drift,
        )


@default_renderer(wrap_type=DatasetDriftMetric)
class DataDriftMetricsRenderer(MetricRenderer):
    def render_html(self, obj: DatasetDriftMetric) -> List[BaseWidgetInfo]:
        result = obj.get_result()

        if result.dataset_drift:
            drift_detected = "detected"

        else:
            drift_detected = "NOT detected"

        counters = [
            CounterData.int("Columns", result.number_of_columns),
            CounterData.int("Drifted Columns", result.number_of_drifted_columns),
            CounterData.float("Share of Drifted Columns", result.share_of_drifted_columns, 3),
        ]

        return [
            counter(
                counters=[
                    CounterData(
                        f"Dataset Drift is {drift_detected}. "
                        f"Dataset drift detection threshold is {result.drift_share}",
                        "Dataset Drift",
                    )
                ],
                title="",
            ),
            counter(
                counters=counters,
                title="",
            ),
        ]
