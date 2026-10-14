# DATA_SOURCES.md — Registro de Fuentes de Datos y Modelos Externos

> Registro obligatorio exigido por el Hook `H29` (`license-ledger`).
> Toda base molecular o peso de red externa agregada al proyecto debe figurar en esta tabla.
> **Regla de Release**: Ningún código puede fusionarse a `main` si contiene fuentes con estado `Por verificar`.

| Nombre de la Fuente | URL Oficial | Tipo de Recurso | Licencia Declarada | ¿Licencia Comercial Válida? | Responsable | Observaciones |
|---|---|---|---|---|---|---|
| **PubChem** | https://pubchem.ncbi.nlm.nih.gov/ | Base de datos molecular | Dominio Público / NIH | Por verificar | Leonardo Ibarra | Evaluar subconjunto de productos naturales. |
| **COCONUT** | https://coconut.naturalproducts.net/ | Colección de productos naturales | CC-BY 4.0 | Por verificar | Leonardo Ibarra | Verificar restricciones de atribución en Kaggle. |
| **LOTUS** | https://lotus.naturalproducts.net/ | Base de ocurrencia de NPs | CC0 1.0 Universal | Por verificar | Leonardo Ibarra | Verificar versión congelada para offline. |
| **HMDB** | https://hmdb.ca/ | Metabolitos humanos | Personal / Académica | Por verificar | Leonardo Ibarra | Posible exclusión si prohíbe uso comercial. |
| **DreaMS Pretrained** | https://github.com/prior-lab/dreams | Pesos de modelo de embeddings | MIT / Apache 2.0 | Por verificar | Leonardo Ibarra | Confirmar licencia de los pesos publicados. |

