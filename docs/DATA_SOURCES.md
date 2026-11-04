# DATA_SOURCES.md — Registro de Fuentes de Datos y Modelos Externos

> Registro obligatorio exigido por el Hook `H29` (`license-ledger`).
> Toda base molecular o peso de red externa agregada al proyecto debe figurar en esta tabla.
> **Regla de Release**: Ningún código puede fusionarse a `main` si contiene fuentes con estado `Por verificar`.

| Nombre de la Fuente | URL Oficial | Tipo de Recurso | Licencia Declarada | ¿Licencia Comercial Válida? | Responsable | Observaciones |
|---|---|---|---|---|---|---|
| **PubChem** | https://pubchem.ncbi.nlm.nih.gov/ | Base de datos molecular | Dominio Público / NIH | Sí | Octavio Luna / Leonardo Ibarra | Sin restricciones de uso comercial. Filtrado por masa 150-1200 Da. |
| **COCONUT** | https://coconut.naturalproducts.net/ | Colección de productos naturales | CC-BY 4.0 | Sí | Octavio Luna / Leonardo Ibarra | Uso comercial permitido con atribución reglamentaria. |
| **LOTUS** | https://lotus.naturalproducts.net/ | Base de ocurrencia de NPs | CC0 1.0 Universal | Sí | Octavio Luna / Leonardo Ibarra | Dominio público total, sin restricciones. Versión offline. |
| **HMDB** | https://hmdb.ca/ | Metabolitos humanos | CC BY-NC 4.0 | No (Excluido) | Octavio Luna / Leonardo Ibarra | Excluido de envíos oficiales debido a cláusula NonCommercial. |
| **DreaMS Pretrained** | https://github.com/prior-lab/dreams | Pesos de modelo de embeddings | MIT | Sí | Leonardo Ibarra | Permite uso comercial e investigación sin restricciones. |

