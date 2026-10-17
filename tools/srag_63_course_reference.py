"""Load the one frozen v2 course predictor without fitting or falling back.

The study directory is a trusted, local artifact directory produced by
``srag_51_course_study --finalize``. No patient data path is inferred here.
Joblib files must not be loaded from untrusted sources.
"""

from __future__ import annotations

import copy
from dataclasses import dataclass
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import srag_51_course_study as study
from scipy import sparse
from sklearn.pipeline import Pipeline


class ReferenceIntegrityError(ValueError):
    """The requested artifact does not satisfy the frozen study contract."""


def _child(directory: Path, relative: str) -> Path:
    path = Path(relative)
    resolved = (directory / path).resolve()
    if path.is_absolute() or directory not in resolved.parents:
        raise ReferenceIntegrityError(
            "Artifact paths must remain inside the study directory"
        )
    return resolved


def _verify_document(document: dict, hash_key: str) -> str:
    recorded = document.get(hash_key)
    payload = {key: value for key, value in document.items() if key != hash_key}
    if not isinstance(recorded, str) or study.object_hash(payload) != recorded:
        raise ReferenceIntegrityError(f"Frozen metadata failed its {hash_key} check")
    return recorded


def _encoded_names(pipeline: Pipeline) -> tuple[str, ...]:
    """Read the fitted column layout, including serialized periodic transforms."""
    prepare = pipeline.named_steps.get("prepare")
    if prepare is None or not hasattr(prepare, "output_indices_"):
        raise ReferenceIntegrityError("The fitted preprocessing layout is unavailable")
    width = max(span.stop for span in prepare.output_indices_.values())
    names = [f"encoded_{index}" for index in range(width)]
    for name, transformer, columns in prepare.transformers_:
        span = prepare.output_indices_.get(name)
        if span is None or span.start == span.stop:
            continue
        columns = list(columns)
        output_names = None
        if hasattr(transformer, "get_feature_names_out"):
            try:
                output_names = list(transformer.get_feature_names_out(columns))
            except (AttributeError, ValueError):
                pass
        if output_names is None:
            if name in ("week_sin", "week_cos"):
                output_names = [f"{columns[0]}__{name.removeprefix('week_')}"]
            elif len(columns) == span.stop - span.start:
                output_names = columns
        if output_names is not None and len(output_names) == span.stop - span.start:
            names[span.start : span.stop] = [str(value) for value in output_names]
    if len(set(names)) != len(names):
        raise ReferenceIntegrityError("Encoded feature names are ambiguous")
    return tuple(names)


@dataclass(frozen=True)
class CourseReference:
    """A validated fitted predictor plus the provenance of its selection."""

    pipeline: Pipeline
    _protocol: dict
    _selection: dict

    @property
    def version(self) -> str:
        return self._protocol["version"]

    @property
    def family(self) -> str:
        return self._selection["winner"]["family"]

    @property
    def strategy(self) -> str:
        return self._selection["winner"]["strategy"]

    @property
    def candidate_id(self) -> str:
        return self._selection["winner"]["candidate_id"]

    @property
    def features(self) -> tuple[str, ...]:
        return tuple(self._protocol["features"])

    @property
    def feature_names_in_(self) -> np.ndarray:
        return np.asarray(self.features, dtype=object)

    @property
    def n_features_in_(self) -> int:
        return len(self.features)

    @property
    def classes_(self) -> np.ndarray:
        return np.asarray([0, 1], dtype=np.int8)

    @property
    def class_labels(self) -> dict[int, str]:
        return {0: "survival", 1: "death"}

    @property
    def input_schema(self) -> dict[str, str]:
        return {
            column: (
                "numeric"
                if column in study.M.NUMERICAS
                else "boolean"
                if column in study.M.BOOLEANAS
                else "categorical"
            )
            for column in self.features
        }

    @property
    def estimator(self):
        """The actual chosen estimator; no XGBoost assumption or fresh fit."""
        return self.pipeline.steps[-1][1]

    @property
    def preprocessing(self) -> Pipeline:
        """A transform-only view over the already fitted preprocessing steps."""
        return Pipeline(self.pipeline.steps[:-1])

    @property
    def encoded_feature_names(self) -> tuple[str, ...]:
        return _encoded_names(self.pipeline)

    @property
    def provenance(self) -> dict:
        return copy.deepcopy(
            {
                "version": self.version,
                "protocol_sha256": self._protocol["protocol_sha256"],
                "selection_sha256": self._selection["selection_sha256"],
                "canonical_model": self._selection["canonical_model"],
                "source": self._protocol["source"],
                "code_sha256": self._protocol["code_sha256"],
                "versions": self._protocol["versions"],
                "family": self.family,
                "strategy": self.strategy,
                "candidate_id": self.candidate_id,
                "effective_params": self._selection["winner"].get(
                    "effective_params", {}
                ),
                "selection_rule": self._selection["rule"],
                "test_status": self._protocol["test_status"],
                "probabilities_recalibrated": self._selection[
                    "probabilities_recalibrated"
                ],
            }
        )

    def _inputs(self, frame: pd.DataFrame) -> pd.DataFrame:
        if not isinstance(frame, pd.DataFrame):
            raise TypeError(
                "The reference predictor requires named raw-input DataFrame columns"
            )
        if frame.columns.duplicated().any():
            raise ValueError("Duplicate input-column names are not allowed")
        return study.model_inputs(frame, self.family)

    def predict_proba(self, frame: pd.DataFrame) -> np.ndarray:
        """Return survival/death probabilities in classes_ order, without fitting."""
        x = self._inputs(frame)
        if len(x) == 0:
            return np.empty((0, 2), dtype=np.float64)
        p = study.predict_probabilities(self.pipeline, x, self.family)
        return np.column_stack([1 - p, p])

    def predict(self, frame: pd.DataFrame, threshold: float = 0.5) -> np.ndarray:
        if not np.isfinite(threshold) or not 0 <= threshold <= 1:
            raise ValueError("The prediction threshold must lie between zero and one")
        return (self.predict_proba(frame)[:, 1] >= threshold).astype(np.int8)

    def encoded_inputs(self, frame: pd.DataFrame, *, dense: bool = False):
        """Transform raw inputs for the fitted estimator, e.g. for a SHAP explainer.

        These are encoded estimator inputs, not the raw forty feature names.
        Keep sparse matrices sparse unless the consumer explicitly needs dense.
        """
        encoded = self.preprocessing.transform(self._inputs(frame))
        if encoded.shape[1] != len(self.encoded_feature_names):
            raise ReferenceIntegrityError(
                "Encoded input width differs from the fitted layout"
            )
        return encoded.toarray() if dense and sparse.issparse(encoded) else encoded


def load_reference(
    study_directory: Path | str, *, verify_runtime: bool = True
) -> CourseReference:
    """Load the sole finalized predictor, checking provenance before deserialization.

    The directory must already have protocol.json, selection.json and the
    canonical fitted artifact. Missing artifacts are errors: this loader never
    searches for another directory, uses the old sample or calls fit.
    """
    directory = Path(study_directory).expanduser().resolve()
    protocol = study.read_json(_child(directory, "protocol.json"))
    selection = study.read_json(_child(directory, "selection.json"))
    protocol_hash = _verify_document(protocol, "protocol_sha256")
    _verify_document(selection, "selection_sha256")
    if protocol.get("version") != study.VERSION:
        raise ReferenceIntegrityError("Unsupported course-study version")
    if selection.get("protocol_sha256") != protocol_hash:
        raise ReferenceIntegrityError("The selection belongs to another protocol")
    if (
        protocol.get("features") != list(study.M.FEATURES)
        or len(protocol["features"]) != 40
    ):
        raise ReferenceIntegrityError(
            "The reference does not have the forty-input course contract"
        )
    if verify_runtime and protocol.get("versions") != study._versions():
        raise ReferenceIntegrityError(
            "The installed runtime differs from the fitted artifact"
        )
    if verify_runtime and protocol.get("code_sha256") != study._source_hashes():
        raise ReferenceIntegrityError(
            "The prediction helpers differ from the frozen study sources"
        )
    if selection.get("test_used_for_selection") is not False:
        raise ReferenceIntegrityError(
            "The selected model lacks the validation-only selection record"
        )
    if selection.get("probabilities_recalibrated") is not False:
        raise ReferenceIntegrityError(
            "This version supports the registered raw-probability predictor"
        )
    candidates = protocol.get("candidates", [])
    if selection.get("candidate_count") != len(candidates):
        raise ReferenceIntegrityError(
            "The selected record does not cover the complete registered budget"
        )
    winner = selection.get("winner", {})
    candidate = next(
        (
            item
            for item in candidates
            if item.get("candidate_id") == winner.get("candidate_id")
        ),
        None,
    )
    if candidate is None or any(
        winner.get(key) != candidate.get(key)
        for key in ("family", "strategy", "params")
    ):
        raise ReferenceIntegrityError(
            "The selected candidate is not the registered candidate"
        )
    if (
        winner.get("status") != "complete"
        or winner.get("protocol_sha256") != protocol_hash
    ):
        raise ReferenceIntegrityError(
            "The selected candidate is incomplete or belongs to another protocol"
        )
    family = winner["family"]
    if family not in study.S.MODELOS:
        raise ReferenceIntegrityError("Unsupported estimator family")
    model_info = selection.get("canonical_model", {})
    model_path = _child(directory, model_info.get("path", ""))
    if study.file_hash(model_path) != model_info.get("sha256"):
        raise ReferenceIntegrityError(
            "The canonical fitted model failed its content hash check"
        )
    pipeline = joblib.load(model_path)
    if not isinstance(pipeline, Pipeline) or pipeline.steps[-1][0] != "model":
        raise ReferenceIntegrityError(
            "The fitted artifact is not the registered estimator pipeline"
        )
    if list(getattr(pipeline, "feature_names_in_", [])) != protocol["features"]:
        raise ReferenceIntegrityError(
            "The fitted raw-input schema differs from its protocol"
        )
    estimator = pipeline.steps[-1][1]
    if family != "lpm" and not np.array_equal(
        getattr(estimator, "classes_", None), [0, 1]
    ):
        raise ReferenceIntegrityError(
            "The fitted classifier does not use survival=0 and death=1"
        )
    reference = CourseReference(
        pipeline, copy.deepcopy(protocol), copy.deepcopy(selection)
    )
    expected_width = getattr(
        estimator, "n_features_in_", len(reference.encoded_feature_names)
    )
    if len(reference.encoded_feature_names) != expected_width:
        raise ReferenceIntegrityError(
            "The fitted estimator and preprocessing widths differ"
        )
    return reference
