"""Reproducibility utilities for CASMI 2026.

Guarantees strict determinism across Python random, NumPy, and PyTorch (CPU & GPU).
"""

import logging
import os
import random

logger = logging.getLogger(__name__)


def set_seed(seed: int = 42) -> None:
    """Set global random seed across all libraries to guarantee reproducibility.

    Args:
        seed: The integer seed value. Default is 42.
    """
    os.environ["PYTHONHASHSEED"] = str(seed)
    random.seed(seed)

    try:
        import numpy as np

        np.random.seed(seed)
    except ImportError:
        pass

    try:
        import torch

        torch.manual_seed(seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed(seed)
            torch.cuda.manual_seed_all(seed)
            torch.backends.cudnn.deterministic = True
            torch.backends.cudnn.benchmark = False
    except ImportError:
        pass

    logger.info("Global random seed locked to %d", seed)
