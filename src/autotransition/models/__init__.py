"""Model integration interfaces."""

from autotransition.models.acestep import AceStepRepaintAdapter, AceStepRuntimeError, ace_step_runtime_available
from autotransition.models.acestep_api import AceStepApiClient, AceStepApiError
from autotransition.models.base import RepaintModel, RepaintResult
from autotransition.models.download import ModelInstallError, install_model, resolve_model_status
from autotransition.models.registry import ACE_STEP_MODELS, ModelProfile, get_model_profile, repaint_capable_models
from autotransition.models.status import InstallState, ModelInstallStatus

__all__ = [
    "ACE_STEP_MODELS",
    "AceStepRepaintAdapter",
    "AceStepApiClient",
    "AceStepApiError",
    "AceStepRuntimeError",
    "InstallState",
    "ModelInstallError",
    "ModelInstallStatus",
    "ModelProfile",
    "RepaintModel",
    "RepaintResult",
    "get_model_profile",
    "install_model",
    "repaint_capable_models",
    "resolve_model_status",
    "ace_step_runtime_available",
]
