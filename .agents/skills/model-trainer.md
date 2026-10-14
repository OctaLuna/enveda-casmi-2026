# Skill: Model Trainer
**Path**: `.agents/skills/model-trainer.md`  
**Purpose**: Guía de ingeniería y buenas prácticas para estructurar scripts de entrenamiento, fine-tuning de embeddings, validación cruzada y guardado seguro de modelos.

---

## 1. Principios del Ciclo de Entrenamiento
Todo pipeline de entrenamiento en CASMI 2026 (fine-tuning DreaMS, MIST fingerprint predictor, DiffMS generativo, o LightGBM re-ranker) debe seguir esta estructura:

```
[ Inicialización Semillas & MLflow ]
               |
[ Carga de Splits Estructurales (data/splits/) ]
               |
[ Forward / Epoch Loop con Gradient Accumulation ]
               |
[ Evaluación por Subsets: Val-Clase1, Val-Clase2, Val-Clase3 ]
               |
[ Checkpoint Atómico con Versionado Semántico ]
```

---

## 2. Requerimientos de Implementación

### 2.1 Reproducibilidad y Semillas
- Obligatorio llamar a `set_seed(seed=42)` al inicio de la ejecución.
- Si se usa PyTorch:
  ```python
  torch.manual_seed(seed)
  torch.cuda.manual_seed_all(seed)
  torch.backends.cudnn.deterministic = True
  torch.backends.cudnn.benchmark = False
  ```

### 2.2 Validación Cruzada y Subsets de Evaluación
- No evaluar únicamente con una métrica agregada.
- Cada checkpoint debe calcular y loguear en MLflow:
  - `MRR@25_Val_Clase1` (Retrieval directo de biblioteca)
  - `MRR@25_Val_Clase2` (Matching por fingerprint / fórmula)
  - `MRR@25_Val_Clase3` (De novo / moléculas no vistas)
  - `MRR@25_Overall_Weighted` (Promedio ponderado estimado)

### 2.3 Guardado Seguro e Inmutable de Checkpoints
- **Nomenclatura Estándar**:
  `models/checkpoints/{model_name}_v{version}_{timestamp}_{metric_val:.4f}.pt`
- **Contenido del Checkpoint**:
  ```python
  checkpoint = {
      "epoch": epoch,
      "model_state_dict": model.state_dict(),
      "optimizer_state_dict": optimizer.state_dict(),
      "scheduler_state_dict": scheduler.state_dict() if scheduler else None,
      "metrics": current_metrics,
      "config": model_config,
      "git_commit": git_commit_hash,
  }
  # Guardado atómico para prevenir archivos corruptos si se interrumpe
  tmp_path = checkpoint_path.with_suffix(".tmp")
  torch.save(checkpoint, tmp_path)
  tmp_path.replace(checkpoint_path)
  ```
- **Prohibido**: `torch.save(model.state_dict(), "best_model.pt")` (sobrescritura destructiva).

### 2.4 Gestión de Memoria GPU & CPU
- Usar `torch.cuda.empty_cache()` entre épocas de evaluación.
- Implementar `torch.cuda.amp.autocast()` para entrenamiento en precisión mixta (FP16/BF16) y reducir uso de VRAM.
- En Kaggle (máximo 9 horas), estimar previamente el tiempo por epoch para asegurar que el job no sea terminado por timeout.

