"""
Early Stopping callback para F5-TTS Training
"""

import logging


logger = logging.getLogger(__name__)


class EarlyStoppingCallback:
    """
    Early Stopping: para treinamento se loss não melhorar por N epochs
    """

    def __init__(
        self, patience: int = 3, min_delta: float = 0.001, mode: str = "min", verbose: bool = True
    ):
        """
        Args:
            patience: Número de epochs sem melhora antes de parar
            min_delta: Melhora mínima considerada significativa
            mode: 'min' para minimizar loss, 'max' para maximizar métrica
            verbose: Se True, imprime mensagens
        """
        self.patience = patience
        self.min_delta = min_delta
        self.mode = mode
        self.verbose = verbose

        self.best_score = None
        self.counter = 0
        self.should_stop = False
        self.best_epoch = 0

    def __call__(self, current_score: float, epoch: int) -> bool:
        """
        Checa se deve parar o treinamento

        Args:
            current_score: Loss ou métrica atual
            epoch: Epoch atual

        Returns:
            True se deve parar, False caso contrário
        """
        if self.patience <= 0:
            return False  # Early stopping desabilitado

        # Primeira época
        if self.best_score is None:
            self.best_score = current_score
            self.best_epoch = epoch
            if self.verbose:
                logger.info(f"🎯 Early Stopping: baseline loss = {current_score:.4f}")
            return False

        # Checar melhora
        if self.mode == "min":
            improved = (self.best_score - current_score) > self.min_delta
        else:
            improved = (current_score - self.best_score) > self.min_delta

        if improved:
            # Houve melhora
            improvement = abs(self.best_score - current_score)
            if self.verbose:
                logger.info(
                    f"✅ Loss melhorou: {self.best_score:.4f} → {current_score:.4f} ({improvement:.4f})"
                )
            self.best_score = current_score
            self.best_epoch = epoch
            self.counter = 0
        else:
            # Não houve melhora
            self.counter += 1
            if self.verbose:
                logger.warning(
                    f"⚠️  Loss não melhorou: {current_score:.4f} (melhor: {self.best_score:.4f} @ epoch {self.best_epoch})"
                )
                logger.warning(
                    f"   Early Stopping: {self.counter}/{self.patience} epochs sem melhora"
                )

            # Checar se deve parar
            if self.counter >= self.patience:
                self.should_stop = True
                if self.verbose:
                    logger.info("🛑 EARLY STOPPING ATIVADO!")
                    logger.info(f"   Melhor loss: {self.best_score:.4f} @ epoch {self.best_epoch}")
                    logger.info(
                        f"   {self.patience} epochs sem melhora significativa (min_delta={self.min_delta})"
                    )
                return True

        return False

    def reset(self):
        """Reset do estado do callback"""
        self.best_score = None
        self.counter = 0
        self.should_stop = False
        self.best_epoch = 0
