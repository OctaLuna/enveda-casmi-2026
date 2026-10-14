## 📌 Descripción del Pull Request
<!-- Resume el objetivo de la feature o corrección y vincula con la tarea SDD correspondientes. -->

### 🔬 Clases Moleculares Impactadas
- [ ] **Clase 1** (Retrieval / Moléculas presentes en librerías públicas)
- [ ] **Clase 2** (Fingerprint matching / Estructura conocida sin espectro público)
- [ ] **Clase 3** (De Novo / Moléculas fantasma ausentes de toda base de datos)

---

## 📊 Impacto en Métrica Local MRR@25 (≥ 3 Semillas)

| Métrica | Antes | Después | $\Delta$ |
|---|---|---|---|
| **MRR@25 Global** | | | |
| **Val-Clase1** | | | |
| **Val-Clase2** | | | |
| **Val-Clase3** | | | |

- **Semillas utilizadas**: `[42, 1337, 2026]`

---

## ⏱️ Presupuesto de Cómputo (< 9 Horas)
- [ ] El cambio no incrementa el tiempo total de inferencia por encima de los 450 minutos permitidos.
- Minutos estimados agregados: `+X min`

---

## 🔒 Cumplimiento de Políticas y Licencias
- [ ] **Modo Offline**: Confirmado que no existen llamadas HTTP ni descargas remotas en el código de inferencia.
- [ ] **Fuentes Externas**: Todas las bases o pesos están registrados en `docs/DATA_SOURCES.md` con licencia comercial válida.
- [ ] **Suite de Pruebas**: Todos los tests unitarios pasan localmente (`pytest tests/ -v`).

