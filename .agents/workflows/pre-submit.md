# Workflow: /pre-submit
**Propósito**: Ejecutar la suite completa de verificaciones de calidad, compatibilidad de formato y presupuesto antes de empaquetar o enviar un notebook a Kaggle.

## Pasos de Ejecución:
1. **Verificación de RDKit y Lockfiles [H20]**:
   Confirma que RDKit esté fijado en `2026.03.3` en dependencias y entorno.
2. **Validación de submission.csv [H24]**:
   Comprueba cabeceras, formato separado por `;`, límite de 25 SMILES y ausencia de duplicados/NaN.
3. **Control de Presupuesto de Tiempo (< 9h) [H27]**:
   Evalúa `configs/budget.yaml` y asegura un margen de seguridad $\ge 20\%$.
4. **Auditoría de Manifiesto de Pesos [H28]**:
   Verifica que todos los checkpoints usados en inferencia estén catalogados en `kaggle/manifest.yaml` con sha256 y licencia.
5. **Suite de Pruebas Unitarias [H42]**:
   Ejecuta `pytest tests/ -v`.

## Comando CLI Rápido:
```bash
python .agents/bin/run_checks.py pre-submit
```

